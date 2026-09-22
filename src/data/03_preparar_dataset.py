# Prepara CIC-IDS2017 para el modelado sin entrenar un clasificador.

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

try:
    import pyarrow as pa
    from pyarrow import parquet as parquet_api
except ModuleNotFoundError as error:
    raise ModuleNotFoundError(
        "Falta pyarrow para generar el archivo Parquet. "
        "Instálalo con: python -m pip install pyarrow"
    ) from error


RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
DIRECTORIO_DATOS_CRUDOS = RAIZ_PROYECTO / "data" / "raw"
DIRECTORIO_DATOS_PROCESADOS = RAIZ_PROYECTO / "data" / "processed"
RUTA_DATASET_PREPARADO = (
    DIRECTORIO_DATOS_PROCESADOS / "dataset_cicids2017_preparado.parquet"
)
RUTA_METADATOS = (
    DIRECTORIO_DATOS_PROCESADOS / "dataset_cicids2017_preparado_metadatos.json"
)
TAMANO_BLOQUE = 100_000

COLUMNA_OBJETIVO = "Label"
COLUMNAS_IDENTIFICADORAS = {
    "Flow ID",
    "Source IP",
    "Source Port",
    "Destination IP",
    "Destination Port",
    "Timestamp",
}


def validar_esquema(columnas: list[str]) -> None:
    columnas_requeridas = COLUMNAS_IDENTIFICADORAS | {COLUMNA_OBJETIVO}
    columnas_faltantes = sorted(columnas_requeridas.difference(columnas))
    if columnas_faltantes:
        raise ValueError(
            f"Faltan columnas requeridas en el dataset: {columnas_faltantes}"
        )


def preparar_bloque(
    bloque: pd.DataFrame,
    columnas_caracteristicas: list[str],
    contadores: Counter[str],
    huellas_vistas: set[int],
) -> pd.DataFrame:
    contadores["rows_read"] += len(bloque)
    bloque.columns = bloque.columns.str.strip()

    filas_vacias = bloque.isna().all(axis=1)
    contadores["blank_rows_removed"] += int(filas_vacias.sum())
    bloque = bloque.loc[~filas_vacias].copy()

    etiquetas = bloque[COLUMNA_OBJETIVO].astype("string").str.strip()
    etiquetas_validas = etiquetas.notna() & etiquetas.ne("")
    contadores["missing_label_rows_removed"] += int((~etiquetas_validas).sum())
    bloque = bloque.loc[etiquetas_validas].copy()
    etiquetas = etiquetas.loc[etiquetas_validas]

    bloque[columnas_caracteristicas] = bloque[columnas_caracteristicas].apply(
        pd.to_numeric, errors="coerce"
    ).astype("float64")
    bloque[columnas_caracteristicas] = bloque[columnas_caracteristicas].replace(
        [np.inf, -np.inf], np.nan
    )

    caracteristicas_validas = bloque[columnas_caracteristicas].notna().all(axis=1)
    contadores["invalid_feature_rows_removed"] += int(
        (~caracteristicas_validas).sum()
    )
    bloque = bloque.loc[caracteristicas_validas].copy()
    etiquetas = etiquetas.loc[caracteristicas_validas]

    bloque[COLUMNA_OBJETIVO] = np.where(
        etiquetas.eq("BENIGN"), "BENIGN", "MALICIOUS"
    )

    # Deduplicar la fila completa antes de excluir columnas contextuales.
    huellas = pd.util.hash_pandas_object(bloque, index=False).astype("uint64")
    filas_duplicadas = huellas.duplicated(keep="first") | huellas.isin(huellas_vistas)
    huellas_conservadas = huellas.loc[~filas_duplicadas]
    huellas_vistas.update(int(valor) for valor in huellas_conservadas)
    contadores["duplicate_rows_removed"] += int(filas_duplicadas.sum())
    bloque = bloque.loc[~filas_duplicadas]
    return bloque[columnas_caracteristicas + [COLUMNA_OBJETIVO]].reset_index(
        drop=True
    )


def preparar_dataset() -> dict[str, Any]:
    archivos = sorted(DIRECTORIO_DATOS_CRUDOS.glob("*.csv"))
    if not archivos:
        raise FileNotFoundError(
            f"No se encontraron CSV en {DIRECTORIO_DATOS_CRUDOS}"
        )

    DIRECTORIO_DATOS_PROCESADOS.mkdir(parents=True, exist_ok=True)
    if RUTA_DATASET_PREPARADO.exists():
        RUTA_DATASET_PREPARADO.unlink()
    if RUTA_METADATOS.exists():
        RUTA_METADATOS.unlink()

    columnas_caracteristicas: list[str] | None = None
    conteo_etiquetas: Counter[str] = Counter()
    contadores: Counter[str] = Counter()
    huellas_vistas: set[int] = set()
    escritor: parquet_api.ParquetWriter | None = None

    try:
        for archivo in archivos:
            lector = pd.read_csv(
                archivo,
                encoding="cp1252",
                low_memory=False,
                chunksize=TAMANO_BLOQUE,
            )

            for bloque in lector:
                bloque.columns = bloque.columns.str.strip()
                if columnas_caracteristicas is None:
                    validar_esquema(bloque.columns.tolist())
                    columnas_caracteristicas = [
                        columna
                        for columna in bloque.columns
                        if columna not in COLUMNAS_IDENTIFICADORAS
                        and columna != COLUMNA_OBJETIVO
                    ]
                elif (
                    bloque.columns.tolist()
                    != columnas_caracteristicas + [COLUMNA_OBJETIVO]
                    and set(bloque.columns)
                    != set(
                        columnas_caracteristicas
                        + list(COLUMNAS_IDENTIFICADORAS)
                        + [COLUMNA_OBJETIVO]
                    )
                ):
                    raise ValueError(
                        f"Esquema inconsistente en {archivo.name}; "
                        "revise las columnas de entrada"
                    )

                preparado = preparar_bloque(
                    bloque, columnas_caracteristicas, contadores, huellas_vistas
                )
                if preparado.empty:
                    continue

                for etiqueta, cantidad in (
                    preparado[COLUMNA_OBJETIVO].value_counts().items()
                ):
                    conteo_etiquetas[str(etiqueta)] += int(cantidad)
                tabla = pa.Table.from_pandas(preparado, preserve_index=False)
                if escritor is None:
                    escritor = parquet_api.ParquetWriter(
                        RUTA_DATASET_PREPARADO, tabla.schema
                    )
                escritor.write_table(tabla)
                contadores["rows_written"] += len(preparado)
    finally:
        if escritor is not None:
            escritor.close()

    if columnas_caracteristicas is None:
        raise ValueError("No se encontraron columnas para preparar")

    metadatos = {
        "input_files": [archivo.name for archivo in archivos],
        "input_encoding": "cp1252",
        "output": str(RUTA_DATASET_PREPARADO.relative_to(RAIZ_PROYECTO)),
        "target_column": COLUMNA_OBJETIVO,
        "target_classes": ["BENIGN", "MALICIOUS"],
        "feature_columns": columnas_caracteristicas,
        "feature_count": len(columnas_caracteristicas),
        "excluded_columns": sorted(COLUMNAS_IDENTIFICADORAS),
        "label_mapping": {
            "BENIGN": "BENIGN",
            "Todas las demás etiquetas originales": "MALICIOUS",
        },
        "label_counts": dict(conteo_etiquetas),
        "counters": dict(contadores),
        "transformations": [
            "Recorte de espacios en nombres de columnas y etiquetas.",
            "Eliminación de filas completamente vacías.",
            "Conversión de características a valores numéricos.",
            "Conversión de infinitos a valores faltantes.",
            "Eliminación de filas con etiqueta o característica inválida.",
            "Exclusión de identificadores, direcciones, puertos y marca temporal.",
            "Eliminación de duplicados exactos de la fila completa dentro del conjunto preparado.",
            "Recodificación binaria de las etiquetas.",
        ],
        "deferred_transformations": [
            "Balanceo de clases.",
            "Escalado o normalización.",
            "Selección de características basada en el modelo.",
            "División final de entrenamiento, validación y prueba.",
        ],
    }
    RUTA_METADATOS.write_text(
        json.dumps(metadatos, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return metadatos


if __name__ == "__main__":
    resultado = preparar_dataset()
    print(f"Dataset preparado: {resultado['output']}")
    print(f"Características: {resultado['feature_count']}")
    print(f"Filas escritas: {resultado['counters']['rows_written']:,}")
    print(f"Etiquetas: {resultado['label_counts']}")

# Describe los flujos que se encuentran en el dataset CIC-IDS2017.

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd


RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
DIRECTORIO_DATOS_CRUDOS = RAIZ_PROYECTO / "data" / "raw"
RUTA_INFORME = RAIZ_PROYECTO / "docs" / "resultados_comprension_datos.json"
TAMANO_BLOQUE = 100_000

COLUMNAS_IDENTIFICADORAS = {
    "Flow ID",
    "Source IP",
    "Source Port",
    "Destination IP",
    "Destination Port",
    "Timestamp",
}


def _actualizar_minimos_maximos(
    resumen: dict[str, dict[str, float]], bloque: pd.DataFrame
) -> None:
    for columna in bloque.columns:
        if columna == "Label":
            continue

        valores_numericos = pd.to_numeric(bloque[columna], errors="coerce")
        valores_finitos = valores_numericos[np.isfinite(valores_numericos)]
        if valores_finitos.empty:
            continue

        valores = resumen.setdefault(columna, {})
        valores["min"] = min(
            valores.get("min", float("inf")), float(valores_finitos.min())
        )
        valores["max"] = max(
            valores.get("max", float("-inf")), float(valores_finitos.max())
        )


def describir_archivo(ruta_archivo: Path) -> dict[str, Any]:
    filas = 0
    filas_vacias = 0
    faltantes_por_columna: Counter[str] = Counter()
    infinitos_por_columna: Counter[str] = Counter()
    etiquetas: Counter[str] = Counter()
    huellas_filas: Counter[int] = Counter()
    huellas_filas_no_vacias: Counter[int] = Counter()
    tipos_observados: dict[str, set[str]] = {}
    rangos_numericos: dict[str, dict[str, float]] = {}
    columnas: list[str] = []
    filas_duplicadas_en_bloques = 0

    lector = pd.read_csv(
        ruta_archivo,
        encoding="cp1252",
        low_memory=False,
        chunksize=TAMANO_BLOQUE,
    )

    for bloque in lector:
        bloque.columns = bloque.columns.str.strip()
        if not columnas:
            columnas = bloque.columns.tolist()

        filas += len(bloque)
        filas_vacias += int(bloque.isna().all(axis=1).sum())
        faltantes_por_columna.update(bloque.isna().sum().to_dict())

        if "Label" in bloque.columns:
            etiquetas.update(
                bloque["Label"]
                .dropna()
                .astype(str)
                .str.strip()
                .replace("", np.nan)
                .dropna()
                .value_counts()
                .to_dict()
            )

        for columna in bloque.columns:
            tipos_observados.setdefault(columna, set()).add(str(bloque[columna].dtype))

        bloque_numerico = bloque.drop(columns=["Label"], errors="ignore").apply(
            pd.to_numeric, errors="coerce"
        )
        infinitos_por_columna.update(
            np.isinf(bloque_numerico).sum().astype(int).to_dict()
        )
        _actualizar_minimos_maximos(rangos_numericos, bloque)

        huellas = pd.util.hash_pandas_object(bloque, index=False)
        conteo_huellas = huellas.value_counts()
        filas_duplicadas_en_bloques += int(
            (conteo_huellas - 1).clip(lower=0).sum()
        )
        huellas_filas.update(huellas.astype("uint64").tolist())
        huellas_filas_no_vacias.update(
            huellas[~bloque.isna().all(axis=1)].astype("uint64").tolist()
        )

    filas_duplicadas_por_huella = sum(
        conteo - 1 for conteo in huellas_filas.values() if conteo > 1
    )
    filas_no_vacias_duplicadas_por_huella = sum(
        conteo - 1 for conteo in huellas_filas_no_vacias.values() if conteo > 1
    )
    conteo_tipos = Counter(
        next(iter(tipos)) for tipos in tipos_observados.values() if len(tipos) == 1
    )

    return {
        "file": ruta_archivo.name,
        "rows": filas,
        "blank_rows": filas_vacias,
        "columns_count": len(columnas),
        "columns": columnas,
        "labels": dict(etiquetas),
        "missing_by_column": {
            columna: conteo
            for columna, conteo in faltantes_por_columna.items()
            if conteo
        },
        "infinite_by_column": {
            columna: conteo
            for columna, conteo in infinitos_por_columna.items()
            if conteo
        },
        "observed_dtypes": {
            columna: sorted(tipos)
            for columna, tipos in tipos_observados.items()
        },
        "dtype_counts": dict(conteo_tipos),
        "numeric_ranges": rangos_numericos,
        "duplicate_rows_within_chunks": filas_duplicadas_en_bloques,
        "duplicate_rows_by_row_hash": filas_duplicadas_por_huella,
        "duplicate_non_blank_rows_by_row_hash": filas_no_vacias_duplicadas_por_huella,
    }


def ejecutar_analisis() -> None:
    reconfigurar_salida = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigurar_salida):
        reconfigurar_salida(encoding="utf-8")

    archivos = sorted(DIRECTORIO_DATOS_CRUDOS.glob("*.csv"))
    if not archivos:
        raise FileNotFoundError(
            f"No se encontraron CSV en {DIRECTORIO_DATOS_CRUDOS}"
        )

    informes_archivos = [describir_archivo(ruta) for ruta in archivos]
    etiquetas_globales: Counter[str] = Counter()
    faltantes_globales: Counter[str] = Counter()
    infinitos_globales: Counter[str] = Counter()
    for informe_archivo in informes_archivos:
        etiquetas_globales.update(informe_archivo["labels"])
        faltantes_globales.update(informe_archivo["missing_by_column"])
        infinitos_globales.update(informe_archivo["infinite_by_column"])

    primeras_columnas = informes_archivos[0]["columns"]
    diferencias_esquema = {
        informe_archivo["file"]: informe_archivo["columns"]
        for informe_archivo in informes_archivos
        if informe_archivo["columns"] != primeras_columnas
    }

    informe = {
        "source_directory": str(
            DIRECTORIO_DATOS_CRUDOS.relative_to(RAIZ_PROYECTO)
        ),
        "files_count": len(informes_archivos),
        "files": informes_archivos,
        "global": {
            "rows": sum(
                informe_archivo["rows"] for informe_archivo in informes_archivos
            ),
            "blank_rows": sum(
                informe_archivo["blank_rows"]
                for informe_archivo in informes_archivos
            ),
            "labels": dict(etiquetas_globales),
            "missing_by_column": dict(faltantes_globales),
            "infinite_by_column": dict(infinitos_globales),
            "duplicate_rows_by_row_hash_within_files": sum(
                informe_archivo["duplicate_rows_by_row_hash"]
                for informe_archivo in informes_archivos
            ),
            "duplicate_non_blank_rows_by_row_hash_within_files": sum(
                informe_archivo["duplicate_non_blank_rows_by_row_hash"]
                for informe_archivo in informes_archivos
            ),
            "columns_count": len(primeras_columnas),
            "columns": primeras_columnas,
            "observed_dtypes": informes_archivos[0]["observed_dtypes"],
            "dtype_counts": informes_archivos[0]["dtype_counts"],
            "schema_differences": diferencias_esquema,
            "possible_identifier_columns": sorted(
                COLUMNAS_IDENTIFICADORAS.intersection(primeras_columnas)
            ),
        },
    }

    RUTA_INFORME.write_text(
        json.dumps(informe, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Informe generado: {RUTA_INFORME.relative_to(RAIZ_PROYECTO)}")
    print(f"Archivos: {informe['files_count']}")
    print(f"Filas brutas: {informe['global']['rows']:,}")
    print(f"Filas completamente vacías: {informe['global']['blank_rows']:,}")
    print("Etiquetas:")
    for etiqueta, conteo in sorted(etiquetas_globales.items()):
        print(f"- {etiqueta}: {conteo:,}")


if __name__ == "__main__":
    ejecutar_analisis()

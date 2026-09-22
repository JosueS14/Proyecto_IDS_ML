"""Prepara CIC-IDS2017 para el modelado sin entrenar un clasificador."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
from pyarrow import parquet as parquet_api


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_PATH = PROCESSED_DIR / "dataset_cicids2017_preparado.parquet"
METADATA_PATH = PROCESSED_DIR / "dataset_cicids2017_preparado_metadata.json"
CHUNK_SIZE = 100_000

TARGET_COLUMN = "Label"
ORIGINAL_IDENTIFIER_COLUMNS = {
    "Flow ID",
    "Source IP",
    "Source Port",
    "Destination IP",
    "Destination Port",
    "Timestamp",
}


def _validate_schema(columns: list[str]) -> None:
    required = ORIGINAL_IDENTIFIER_COLUMNS | {TARGET_COLUMN}
    missing = sorted(required.difference(columns))
    if missing:
        raise ValueError(f"Faltan columnas requeridas en el dataset: {missing}")


def _prepare_chunk(
    chunk: pd.DataFrame,
    feature_columns: list[str],
    counters: Counter[str],
    seen_hashes: set[int],
) -> pd.DataFrame:
    """Apply deterministic row and column transformations to one chunk."""
    counters["rows_read"] += len(chunk)
    chunk.columns = chunk.columns.str.strip()

    blank_rows = chunk.isna().all(axis=1)
    counters["blank_rows_removed"] += int(blank_rows.sum())
    chunk = chunk.loc[~blank_rows].copy()

    labels = chunk[TARGET_COLUMN].astype("string").str.strip()
    valid_labels = labels.notna() & labels.ne("")
    counters["missing_label_rows_removed"] += int((~valid_labels).sum())
    chunk = chunk.loc[valid_labels].copy()
    labels = labels.loc[valid_labels]

    chunk[feature_columns] = chunk[feature_columns].apply(
        pd.to_numeric, errors="coerce"
    ).astype("float64")
    chunk[feature_columns] = chunk[feature_columns].replace(
        [np.inf, -np.inf], np.nan
    )

    valid_features = chunk[feature_columns].notna().all(axis=1)
    counters["invalid_feature_rows_removed"] += int((~valid_features).sum())
    chunk = chunk.loc[valid_features].copy()
    labels = labels.loc[valid_features]

    chunk[TARGET_COLUMN] = np.where(labels.eq("BENIGN"), "BENIGN", "MALICIOUS")

    # Deduplicate the complete source row before excluding contextual columns.
    row_hashes = pd.util.hash_pandas_object(chunk, index=False).astype("uint64")
    duplicate_rows = row_hashes.duplicated(keep="first") | row_hashes.map(
        lambda value: int(value) in seen_hashes
    )
    kept_hashes = row_hashes.loc[~duplicate_rows]
    seen_hashes.update(int(value) for value in kept_hashes)
    counters["duplicate_rows_removed"] += int(duplicate_rows.sum())
    chunk = chunk.loc[~duplicate_rows]
    return chunk[feature_columns + [TARGET_COLUMN]].reset_index(drop=True)


def prepare_dataset() -> dict[str, Any]:
    """Prepare all raw CSV files and write a Parquet model-ready dataset."""
    files = sorted(RAW_DIR.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No se encontraron CSV en {RAW_DIR}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()
    if METADATA_PATH.exists():
        METADATA_PATH.unlink()

    feature_columns: list[str] | None = None
    label_counts: Counter[str] = Counter()
    counters: Counter[str] = Counter()
    seen_hashes: set[int] = set()
    writer: parquet_api.ParquetWriter | None = None

    try:
        for path in files:
            reader = pd.read_csv(
                path,
                encoding="cp1252",
                low_memory=False,
                chunksize=CHUNK_SIZE,
            )

            for chunk in reader:
                chunk.columns = chunk.columns.str.strip()
                if feature_columns is None:
                    _validate_schema(chunk.columns.tolist())
                    feature_columns = [
                        column
                        for column in chunk.columns
                        if column not in ORIGINAL_IDENTIFIER_COLUMNS
                        and column != TARGET_COLUMN
                    ]
                elif chunk.columns.tolist() != feature_columns + [TARGET_COLUMN] and set(
                    chunk.columns
                ) != set(feature_columns + list(ORIGINAL_IDENTIFIER_COLUMNS) + [TARGET_COLUMN]):
                    raise ValueError(
                        f"Esquema inconsistente en {path.name}; revise las columnas de entrada"
                    )

                prepared = _prepare_chunk(
                    chunk, feature_columns, counters, seen_hashes
                )
                if prepared.empty:
                    continue

                label_counts.update(prepared[TARGET_COLUMN].value_counts().to_dict())
                table = pa.Table.from_pandas(prepared, preserve_index=False)
                if writer is None:
                    writer = parquet_api.ParquetWriter(OUTPUT_PATH, table.schema)
                writer.write_table(table)
                counters["rows_written"] += len(prepared)
    finally:
        if writer is not None:
            writer.close()

    if feature_columns is None:
        raise ValueError("No se encontraron columnas para preparar")

    metadata = {
        "input_files": [path.name for path in files],
        "input_encoding": "cp1252",
        "output": str(OUTPUT_PATH.relative_to(PROJECT_ROOT)),
        "target_column": TARGET_COLUMN,
        "target_classes": ["BENIGN", "MALICIOUS"],
        "feature_columns": feature_columns,
        "feature_count": len(feature_columns),
        "excluded_columns": sorted(ORIGINAL_IDENTIFIER_COLUMNS),
        "label_mapping": {
            "BENIGN": "BENIGN",
            "Todas las demás etiquetas originales": "MALICIOUS",
        },
        "label_counts": dict(label_counts),
        "counters": dict(counters),
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
    METADATA_PATH.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return metadata


if __name__ == "__main__":
    result = prepare_dataset()
    print(f"Dataset preparado: {result['output']}")
    print(f"Características: {result['feature_count']}")
    print(f"Filas escritas: {result['counters']['rows_written']:,}")
    print(f"Etiquetas: {result['label_counts']}")

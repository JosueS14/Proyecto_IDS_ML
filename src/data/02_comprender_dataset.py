"""Describe CIC-IDS2017 without modifying the source CSV files."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORT_PATH = PROJECT_ROOT / "docs" / "data_understanding_results.json"
CHUNK_SIZE = 100_000

IDENTIFIER_COLUMNS = {
    "Flow ID",
    "Source IP",
    "Source Port",
    "Destination IP",
    "Destination Port",
    "Timestamp",
}


def _update_min_max(summary: dict[str, dict[str, float]], frame: pd.DataFrame) -> None:
    """Update numeric ranges after coercing values for inspection only."""
    for column in frame.columns:
        if column == "Label":
            continue

        numeric = pd.to_numeric(frame[column], errors="coerce")
        finite = numeric[np.isfinite(numeric)]
        if finite.empty:
            continue

        values = summary.setdefault(column, {})
        values["min"] = min(values.get("min", float("inf")), float(finite.min()))
        values["max"] = max(values.get("max", float("-inf")), float(finite.max()))


def describe_file(path: Path) -> dict[str, Any]:
    """Collect schema and quality information for one CSV file."""
    rows = 0
    blank_rows = 0
    missing_by_column: Counter[str] = Counter()
    infinite_by_column: Counter[str] = Counter()
    labels: Counter[str] = Counter()
    row_hashes: Counter[int] = Counter()
    non_blank_row_hashes: Counter[int] = Counter()
    observed_dtypes: dict[str, set[str]] = {}
    numeric_ranges: dict[str, dict[str, float]] = {}
    columns: list[str] = []
    duplicate_rows_within_chunks = 0

    reader = pd.read_csv(
        path,
        encoding="cp1252",
        low_memory=False,
        chunksize=CHUNK_SIZE,
    )

    for chunk in reader:
        chunk.columns = chunk.columns.str.strip()
        if not columns:
            columns = chunk.columns.tolist()

        rows += len(chunk)
        blank_rows += int(chunk.isna().all(axis=1).sum())
        missing_by_column.update(chunk.isna().sum().to_dict())

        if "Label" in chunk.columns:
            labels.update(
                chunk["Label"]
                .dropna()
                .astype(str)
                .str.strip()
                .replace("", np.nan)
                .dropna()
                .value_counts()
                .to_dict()
            )

        for column in chunk.columns:
            observed_dtypes.setdefault(column, set()).add(str(chunk[column].dtype))

        numeric_chunk = chunk.drop(columns=["Label"], errors="ignore").apply(
            pd.to_numeric, errors="coerce"
        )
        infinite_by_column.update(
            np.isinf(numeric_chunk).sum().astype(int).to_dict()
        )
        _update_min_max(numeric_ranges, chunk)

        hashes = pd.util.hash_pandas_object(chunk, index=False)
        row_hash_counts = hashes.value_counts()
        duplicate_rows_within_chunks += int((row_hash_counts - 1).clip(lower=0).sum())
        row_hashes.update(hashes.astype("uint64").tolist())
        non_blank_row_hashes.update(
            hashes[~chunk.isna().all(axis=1)].astype("uint64").tolist()
        )

    duplicate_rows_by_hash = sum(count - 1 for count in row_hashes.values() if count > 1)
    duplicate_non_blank_rows_by_hash = sum(
        count - 1 for count in non_blank_row_hashes.values() if count > 1
    )
    dtype_counts = Counter(
        next(iter(dtypes)) for dtypes in observed_dtypes.values() if len(dtypes) == 1
    )

    return {
        "file": path.name,
        "rows": rows,
        "blank_rows": blank_rows,
        "columns_count": len(columns),
        "columns": columns,
        "labels": dict(labels),
        "missing_by_column": {
            column: count for column, count in missing_by_column.items() if count
        },
        "infinite_by_column": {
            column: count for column, count in infinite_by_column.items() if count
        },
        "observed_dtypes": {
            column: sorted(dtypes) for column, dtypes in observed_dtypes.items()
        },
        "dtype_counts": dict(dtype_counts),
        "numeric_ranges": numeric_ranges,
        "duplicate_rows_within_chunks": duplicate_rows_within_chunks,
        "duplicate_rows_by_row_hash": duplicate_rows_by_hash,
        "duplicate_non_blank_rows_by_row_hash": duplicate_non_blank_rows_by_hash,
    }


def main() -> None:
    reconfigure_stdout = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure_stdout):
        reconfigure_stdout(encoding="utf-8")

    files = sorted(RAW_DIR.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No se encontraron CSV en {RAW_DIR}")

    file_reports = [describe_file(path) for path in files]
    global_labels: Counter[str] = Counter()
    global_missing: Counter[str] = Counter()
    global_infinite: Counter[str] = Counter()
    for report in file_reports:
        global_labels.update(report["labels"])
        global_missing.update(report["missing_by_column"])
        global_infinite.update(report["infinite_by_column"])

    first_columns = file_reports[0]["columns"]
    schema_differences = {
        report["file"]: report["columns"]
        for report in file_reports
        if report["columns"] != first_columns
    }

    report = {
        "source_directory": str(RAW_DIR.relative_to(PROJECT_ROOT)),
        "files_count": len(file_reports),
        "files": file_reports,
        "global": {
            "rows": sum(item["rows"] for item in file_reports),
            "blank_rows": sum(item["blank_rows"] for item in file_reports),
            "labels": dict(global_labels),
            "missing_by_column": dict(global_missing),
            "infinite_by_column": dict(global_infinite),
            "duplicate_rows_by_row_hash_within_files": sum(
                item["duplicate_rows_by_row_hash"] for item in file_reports
            ),
            "duplicate_non_blank_rows_by_row_hash_within_files": sum(
                item["duplicate_non_blank_rows_by_row_hash"] for item in file_reports
            ),
            "columns_count": len(first_columns),
            "columns": first_columns,
            "observed_dtypes": file_reports[0]["observed_dtypes"],
            "dtype_counts": file_reports[0]["dtype_counts"],
            "schema_differences": schema_differences,
            "possible_identifier_columns": sorted(
                IDENTIFIER_COLUMNS.intersection(first_columns)
            ),
        },
        "notes": [
            "Los nombres de columnas se recortan solo para describir el esquema; los CSV originales no se modifican.",
            "Los duplicados se identifican mediante la huella de cada fila dentro de cada archivo; el total no incluye coincidencias entre archivos.",
            "Los rangos se calculan sobre valores numéricos finitos y no constituyen todavía reglas de limpieza.",
        ],
    }

    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Informe generado: {REPORT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Archivos: {report['files_count']}")
    print(f"Filas brutas: {report['global']['rows']:,}")
    print(f"Filas completamente vacías: {report['global']['blank_rows']:,}")
    print("Etiquetas:")
    for label, count in sorted(global_labels.items()):
        print(f"- {label}: {count:,}")


if __name__ == "__main__":
    main()

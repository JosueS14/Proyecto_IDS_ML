"""Verifica los archivos locales de CIC-IDS2017 antes de procesarlos."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
DIRECTORIO_RAW = RAIZ_PROYECTO / "data" / "raw"
RUTA_MANIFIESTO = RAIZ_PROYECTO / "docs" / "dataset_manifest.json"
CODIFICACION = "cp1252"
URL_FUENTE = "https://www.unb.ca/cic/datasets/ids-2017.html"

ARCHIVOS_ESPERADOS: dict[str, int] = {
    "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv": 225_745,
    "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv": 286_467,
    "Friday-WorkingHours-Morning.pcap_ISCX.csv": 191_033,
    "Monday-WorkingHours.pcap_ISCX.csv": 529_918,
    "Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv": 288_602,
    "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv": 458_968,
    "Tuesday-WorkingHours.pcap_ISCX.csv": 445_909,
    "Wednesday-workingHours.pcap_ISCX.csv": 692_703,
}
COLUMNAS_ESPERADAS = 85


def sha256(ruta: Path) -> str:
    digest = hashlib.sha256()
    with ruta.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


def describir_csv(ruta: Path, calcular_hash: bool) -> dict[str, Any]:
    with ruta.open("r", encoding=CODIFICACION, newline="") as archivo:
        lector = csv.reader(archivo)
        try:
            encabezado = next(lector)
        except StopIteration as error:
            raise ValueError("El archivo no contiene encabezado.") from error

        columnas = [columna.strip() for columna in encabezado]
        filas = sum(1 for _ in lector)

    resultado: dict[str, Any] = {
        "rows": filas,
        "columns": len(columnas),
        "has_label": "Label" in columnas,
        "size_bytes": ruta.stat().st_size,
    }
    if calcular_hash:
        resultado["sha256"] = sha256(ruta)
    return resultado


def cargar_manifiesto() -> dict[str, Any] | None:
    if not RUTA_MANIFIESTO.exists():
        return None
    return json.loads(RUTA_MANIFIESTO.read_text(encoding="utf-8"))


def validar(calcular_hash: bool, escribir_manifiesto: bool) -> int:
    errores: list[str] = []
    advertencias: list[str] = []

    if not DIRECTORIO_RAW.is_dir():
        print(f"ERROR: no existe el directorio {DIRECTORIO_RAW}")
        return 1

    archivos_encontrados = {
        ruta.name for ruta in DIRECTORIO_RAW.glob("*.csv") if ruta.is_file()
    }
    faltantes = sorted(set(ARCHIVOS_ESPERADOS) - archivos_encontrados)
    adicionales = sorted(archivos_encontrados - set(ARCHIVOS_ESPERADOS))
    if faltantes:
        errores.append(f"Faltan archivos: {', '.join(faltantes)}")
    if adicionales:
        advertencias.append(
            "Hay CSV adicionales que no serán procesados: "
            + ", ".join(adicionales)
        )

    manifiesto = cargar_manifiesto()
    resultados: dict[str, dict[str, Any]] = {}
    for nombre, filas_esperadas in ARCHIVOS_ESPERADOS.items():
        ruta = DIRECTORIO_RAW / nombre
        if not ruta.is_file():
            continue

        try:
            descripcion = describir_csv(ruta, calcular_hash)
        except (OSError, UnicodeError, csv.Error, ValueError) as error:
            errores.append(f"{nombre}: no se pudo leer ({error})")
            continue

        resultados[nombre] = descripcion
        if descripcion["rows"] != filas_esperadas:
            errores.append(
                f"{nombre}: se esperaban {filas_esperadas:,} filas y "
                f"se encontraron {descripcion['rows']:,}"
            )
        if descripcion["columns"] != COLUMNAS_ESPERADAS:
            errores.append(
                f"{nombre}: se esperaban {COLUMNAS_ESPERADAS} columnas y "
                f"se encontraron {descripcion['columns']}"
            )
        if not descripcion["has_label"]:
            errores.append(f"{nombre}: no contiene la columna Label")

        referencia = (manifiesto or {}).get("files", {}).get(nombre)
        if referencia and not escribir_manifiesto:
            campos = ["rows", "columns", "size_bytes"]
            if calcular_hash:
                campos.append("sha256")
            for campo in campos:
                esperado = referencia.get(campo)
                observado = descripcion.get(campo)
                if esperado is not None and observado != esperado:
                    errores.append(
                        f"{nombre}: {campo} no coincide con el manifiesto "
                        f"(esperado={esperado}, observado={observado})"
                    )

    if escribir_manifiesto:
        manifiesto_nuevo = {
            "dataset": "CIC-IDS2017",
            "source_url": URL_FUENTE,
            "encoding": CODIFICACION,
            "expected_columns": COLUMNAS_ESPERADAS,
            "files": resultados,
        }
        RUTA_MANIFIESTO.write_text(
            json.dumps(manifiesto_nuevo, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Manifiesto generado: {RUTA_MANIFIESTO.relative_to(RAIZ_PROYECTO)}")

    for advertencia in advertencias:
        print(f"ADVERTENCIA: {advertencia}")
    for error in errores:
        print(f"ERROR: {error}")

    if errores:
        return 1

    print(f"OK: {len(resultados)} archivos CIC-IDS2017 verificados.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verifica los CSV de CIC-IDS2017 antes de preparar el dataset."
    )
    parser.add_argument(
        "--write-manifest",
        action="store_true",
        help="Genera o actualiza docs/dataset_manifest.json con los hashes locales.",
    )
    parser.add_argument(
        "--skip-hash",
        action="store_true",
        help="Omite el cálculo SHA-256 para una verificación rápida.",
    )
    argumentos = parser.parse_args()
    return validar(
        calcular_hash=not argumentos.skip_hash,
        escribir_manifiesto=argumentos.write_manifest,
    )


if __name__ == "__main__":
    raise SystemExit(main())

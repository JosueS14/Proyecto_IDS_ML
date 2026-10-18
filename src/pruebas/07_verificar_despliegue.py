"""Verificar que el prototipo esta listo para una ejecucion local por lotes."""

from __future__ import annotations

import importlib
import json
import platform
import sys
from pathlib import Path
from typing import Any


RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
RUTA_MODELO = (
    RAIZ_PROYECTO
    / "data"
    / "processed"
    / "modelos"
    / "random_forest_seleccionado.joblib"
)
RUTA_METADATOS = (
    RAIZ_PROYECTO
    / "data"
    / "processed"
    / "dataset_cicids2017_preparado_metadatos.json"
)
RUTA_PARQUET = (
    RAIZ_PROYECTO / "data" / "processed" / "dataset_cicids2017_preparado.parquet"
)
RUTA_INFORME = RAIZ_PROYECTO / "docs" / "resultados_despliegue.json"


def version_paquete(nombre: str) -> str | None:
    try:
        modulo = importlib.import_module(nombre)
    except ImportError:
        return None
    return str(getattr(modulo, "__version__", "disponible"))


def verificar() -> dict[str, Any]:
    errores: list[str] = []
    advertencias: list[str] = []
    archivos = {
        "modelo": RUTA_MODELO,
        "metadatos": RUTA_METADATOS,
        "dependencias_runtime": RAIZ_PROYECTO / "requirements-runtime.txt",
        "interfaz": RAIZ_PROYECTO / "src" / "prototipo" / "05_interfaz_tkinter.py",
        "motor_inferencia": RAIZ_PROYECTO / "src" / "prototipo" / "inferencia_ids.py",
    }

    archivos_estado = {}
    for nombre, ruta in archivos.items():
        existe = ruta.exists()
        archivos_estado[nombre] = {
            "ruta": ruta.relative_to(RAIZ_PROYECTO).as_posix(),
            "existe": existe,
        }
        if not existe:
            errores.append(f"Falta el artefacto requerido: {nombre}")

    paquetes = {
        "pandas": version_paquete("pandas"),
        "numpy": version_paquete("numpy"),
        "sklearn": version_paquete("sklearn"),
        "joblib": version_paquete("joblib"),
        "pyarrow": version_paquete("pyarrow"),
    }
    for nombre, version in paquetes.items():
        if version is None:
            errores.append(f"Falta la dependencia: {nombre}")

    versiones_artefacto = {
        "python": "3.13",
        "pandas": "2.3.3",
        "sklearn": "1.8.0",
    }
    if not sys.version.startswith(versiones_artefacto["python"]):
        advertencias.append(
            f"El artefacto fue validado con Python {versiones_artefacto['python']}.x; "
            f"el entorno actual usa Python {sys.version.split()[0]}"
        )
    for paquete in ("pandas", "sklearn"):
        version_actual = paquetes[paquete]
        if version_actual is not None and version_actual != versiones_artefacto[paquete]:
            advertencias.append(
                f"El artefacto fue validado con {paquete} {versiones_artefacto[paquete]}; "
                f"el entorno actual usa {version_actual}"
            )

    modelo_info: dict[str, Any] = {}
    if RUTA_MODELO.exists():
        try:
            import joblib

            artefacto = joblib.load(RUTA_MODELO)
            modelo = artefacto["modelo"]
            columnas = list(artefacto["feature_columns"])
            modelo_info = {
                "tipo": type(modelo).__name__,
                "caracteristicas": len(columnas),
                "clases": [str(clase) for clase in modelo.classes_],
            }
            if len(columnas) != 78:
                errores.append(
                    f"El modelo declara {len(columnas)} caracteristicas; se esperaban 78"
                )
        except Exception as error:  # pragma: no cover - depende del artefacto local
            errores.append(f"No se pudo cargar el modelo: {error}")

    metadatos_info: dict[str, Any] = {}
    if RUTA_METADATOS.exists():
        try:
            metadatos = json.loads(RUTA_METADATOS.read_text(encoding="utf-8"))
            columnas = metadatos.get("feature_columns", [])
            metadatos_info = {
                "caracteristicas": len(columnas),
                "clases": metadatos.get("target_classes", []),
                "salida": metadatos.get("output"),
            }
            if len(columnas) != 78:
                errores.append(
                    f"Los metadatos declaran {len(columnas)} caracteristicas; se esperaban 78"
                )
        except Exception as error:  # pragma: no cover - depende del archivo local
            errores.append(f"No se pudieron leer los metadatos: {error}")

    parquet_info: dict[str, Any] = {"disponible": RUTA_PARQUET.exists()}
    if RUTA_PARQUET.exists():
        try:
            import pyarrow.parquet as parquet

            esquema = parquet.read_schema(RUTA_PARQUET)
            parquet_info["columnas"] = len(esquema.names)
            parquet_info["tiene_label"] = "Label" in esquema.names
            if len(esquema.names) != 79 or "Label" not in esquema.names:
                errores.append(
                    "El esquema del Parquet no coincide con 78 caracteristicas y Label"
                )
        except Exception as error:  # pragma: no cover - depende del archivo local
            errores.append(f"No se pudo verificar el Parquet: {error}")
    else:
        advertencias.append(
            "No se encontro el Parquet preparado; se podran analizar otros CSV o Parquet compatibles"
        )

    estado = "PASÓ" if not errores else "FALLÓ"
    return {
        "estado": estado,
        "python": sys.version.split()[0],
        "plataforma": platform.platform(),
        "archivos": archivos_estado,
        "paquetes": paquetes,
        "modelo": modelo_info,
        "metadatos": metadatos_info,
        "parquet": parquet_info,
        "errores": errores,
        "advertencias": advertencias,
    }


def main() -> int:
    informe = verificar()
    RUTA_INFORME.write_text(
        json.dumps(informe, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(informe, indent=2, ensure_ascii=False))
    return 0 if informe["estado"] == "PASÓ" else 1


if __name__ == "__main__":
    raise SystemExit(main())

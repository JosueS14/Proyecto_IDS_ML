# Ejecuta pruebas reproducibles de la fase 6 del prototipo IDS.

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path
import py_compile
import sys
from time import perf_counter
from typing import Any

import numpy as np
import pandas as pd

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from src.prototipo.inferencia_ids import IDSInferencia


RUTA_PARQUET = (
    RAIZ_PROYECTO / "data" / "processed" / "dataset_cicids2017_preparado.parquet"
)
RUTA_CSV = RAIZ_PROYECTO / "data" / "raw" / "Monday-WorkingHours.pcap_ISCX.csv"
RUTA_RESULTADOS = RAIZ_PROYECTO / "docs" / "resultados_validacion.json"
CLASES_ESPERADAS = {"BENIGN", "MALICIOUS"}


def registrar_prueba(
    resultados: list[dict[str, Any]], nombre: str, funcion: Callable[[], Any]
) -> None:
    """Ejecutar una prueba y guardar su resultado sin ocultar el error."""
    inicio = perf_counter()
    try:
        detalle = funcion()
        resultados.append(
            {
                "prueba": nombre,
                "estado": "PASÓ",
                "duracion_segundos": perf_counter() - inicio,
                "detalle": detalle,
            }
        )
    except Exception as error:  # pragma: no cover - reporte de ejecución
        resultados.append(
            {
                "prueba": nombre,
                "estado": "FALLÓ",
                "duracion_segundos": perf_counter() - inicio,
                "detalle": str(error),
            }
        )


def main() -> None:
    resultados: list[dict[str, Any]] = []
    motor = IDSInferencia()

    def probar_modelo() -> Mapping[str, object]:
        clases = set(motor.modelo.classes_)
        assert clases == CLASES_ESPERADAS, clases
        assert len(motor.columnas_caracteristicas) == 78
        return {"clases": sorted(clases), "caracteristicas": len(motor.columnas_caracteristicas)}

    def probar_parquet() -> Mapping[str, object]:
        entrada = motor.cargar_archivo(RUTA_PARQUET, limite=200)
        salida = motor.clasificar(entrada)
        assert len(salida) == 200
        assert set(salida["Predicción"]) <= CLASES_ESPERADAS
        assert salida["Estado"].eq("ANALIZADO").all()
        assert (salida["Timestamp"] == "NO DISPONIBLE EN ENTRADA").all()
        return motor.resumen(salida)

    def probar_csv_original() -> Mapping[str, object]:
        entrada = motor.cargar_archivo(RUTA_CSV, limite=200)
        salida = motor.clasificar(entrada)
        assert len(salida) == 200
        assert set(salida["Predicción"]) - {""} <= CLASES_ESPERADAS
        assert salida["Estado"].isin({"ANALIZADO", "ERROR_DATOS"}).all()
        assert salida["Estado"].eq("ANALIZADO").any()
        assert not salida["Flow ID"].eq("NO DISPONIBLE EN ENTRADA").all()
        return motor.resumen(salida)

    def probar_esquema_invalido() -> str:
        entrada = motor.cargar_archivo(RUTA_PARQUET, limite=2)
        entrada = entrada.drop(columns=[motor.columnas_caracteristicas[0]])
        try:
            motor.clasificar(entrada)
        except ValueError as error:
            return str(error)
        raise AssertionError("Se aceptó un esquema sin una característica requerida")

    def probar_valores_invalidos() -> dict[str, int]:
        entrada = motor.cargar_archivo(RUTA_PARQUET, limite=5)
        entrada.loc[entrada.index[0], motor.columnas_caracteristicas[0]] = np.inf
        salida = motor.clasificar(entrada)
        estado = salida.loc[salida.index[0], "Estado"]
        assert bool(estado == "ERROR_DATOS")
        return motor.resumen(salida)

    def probar_alertas() -> dict[str, int]:
        entrada = motor.cargar_archivo(RUTA_CSV, limite=500)
        salida = motor.clasificar(entrada)
        alertas = salida[salida["Predicción"] == "MALICIOUS"]
        assert (alertas["Alerta"] == "ALERTA").all()
        benignos = salida[salida["Predicción"] == "BENIGN"]
        assert (benignos["Alerta"] == "NO").all()
        return {"alertas": int(len(alertas)), "benignos": int(len(benignos))}

    def probar_filtro() -> dict[str, int]:
        datos = pd.DataFrame(
            {
                "Predicción": ["BENIGN", "MALICIOUS"],
                "Alerta": ["NO", "ALERTA"],
                "Estado": ["ANALIZADO", "ANALIZADO"],
            }
        )
        filtrados = motor.filtrar(datos, "malicious")
        assert len(filtrados) == 1
        return {"coincidencias": len(filtrados)}

    def probar_rendimiento() -> dict[str, float | int]:
        entrada = motor.cargar_archivo(RUTA_PARQUET, limite=1_000)
        inicio = perf_counter()
        salida = motor.clasificar(entrada)
        duracion = perf_counter() - inicio
        assert len(salida) == 1_000
        return {"filas": len(salida), "segundos": duracion}

    def probar_compilacion() -> dict[str, str]:
        archivos = {
            "inferencia": RAIZ_PROYECTO / "src" / "prototipo" / "inferencia_ids.py",
            "interfaz": RAIZ_PROYECTO / "src" / "prototipo" / "05_interfaz_tkinter.py",
        }
        for ruta in archivos.values():
            py_compile.compile(str(ruta), doraise=True)
        return {nombre: str(ruta.relative_to(RAIZ_PROYECTO)) for nombre, ruta in archivos.items()}

    registrar_prueba(resultados, "Carga del modelo y esquema", probar_modelo)
    registrar_prueba(resultados, "Inferencia con Parquet preparado", probar_parquet)
    registrar_prueba(resultados, "Inferencia con CSV original", probar_csv_original)
    registrar_prueba(resultados, "Rechazo de esquema inválido", probar_esquema_invalido)
    registrar_prueba(resultados, "Manejo de valores inválidos", probar_valores_invalidos)
    registrar_prueba(resultados, "Consistencia de alertas", probar_alertas)
    registrar_prueba(resultados, "Filtro de la interfaz", probar_filtro)
    registrar_prueba(resultados, "Inferencia de un lote de 1,000 filas", probar_rendimiento)
    registrar_prueba(resultados, "Compilación de componentes", probar_compilacion)

    informe = {
        "fase": "6. Pruebas y validación",
        "total_pruebas": len(resultados),
        "pruebas_pasaron": sum(item["estado"] == "PASÓ" for item in resultados),
        "pruebas_fallaron": sum(item["estado"] == "FALLÓ" for item in resultados),
        "pruebas": resultados,
    }
    RUTA_RESULTADOS.write_text(
        json.dumps(informe, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(informe, indent=2, ensure_ascii=False))
    if informe["pruebas_fallaron"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

"""Ejecuta una prueba offline de extremo a extremo en un sandbox local."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from time import perf_counter
from typing import Any

import numpy as np
import pandas as pd
import sklearn

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from src.prototipo import inferencia_ids
from src.prototipo.inferencia_ids import IDSInferencia


RUTA_METADATOS = (
    RAIZ_PROYECTO
    / "data"
    / "processed"
    / "dataset_cicids2017_preparado_metadatos.json"
)
RUTA_FUENTE = (
    RAIZ_PROYECTO
    / "data"
    / "raw"
    / "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv"
)
RUTA_SANDBOX = RAIZ_PROYECTO / "data" / "processed" / "prueba_laboratorio"
RUTA_INFORME = RAIZ_PROYECTO / "docs" / "resultados_prueba_laboratorio.json"
REGISTROS_POR_CLASE = 10
TAMANO_BLOQUE = 25_000


def sha256(ruta: Path) -> str:
    """Calcular la huella de un archivo local."""
    digest = hashlib.sha256()
    with ruta.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


def crear_muestra_controlada(
    columnas_caracteristicas: list[str],
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Extraer una muestra pequeña y válida de ambas clases desde un CSV local."""
    if not RUTA_FUENTE.is_file():
        raise FileNotFoundError(f"No se encontró el CSV de prueba: {RUTA_FUENTE}")

    columnas_requeridas = set(columnas_caracteristicas) | {"Label"}
    muestras: dict[str, list[pd.DataFrame]] = {"BENIGN": [], "MALICIOUS": []}
    cantidades = {"BENIGN": 0, "MALICIOUS": 0}

    bloques = pd.read_csv(
        RUTA_FUENTE,
        encoding="cp1252",
        low_memory=False,
        chunksize=TAMANO_BLOQUE,
        usecols=lambda nombre: nombre.strip() in columnas_requeridas,
    )

    for bloque in bloques:
        bloque.columns = bloque.columns.str.strip()
        if not columnas_requeridas.issubset(bloque.columns):
            faltantes = sorted(columnas_requeridas.difference(bloque.columns))
            raise ValueError(f"Faltan columnas en el CSV fuente: {faltantes}")

        etiquetas = bloque["Label"].astype("string").str.strip()
        caracteristicas = bloque[columnas_caracteristicas].apply(
            pd.to_numeric, errors="coerce"
        )
        caracteristicas = caracteristicas.replace([np.inf, -np.inf], np.nan)
        validas = caracteristicas.notna().all(axis=1)

        for clase in ("BENIGN", "MALICIOUS"):
            restantes = REGISTROS_POR_CLASE - cantidades[clase]
            if restantes <= 0:
                continue

            if clase == "BENIGN":
                es_clase = etiquetas.eq("BENIGN")
            else:
                es_clase = etiquetas.notna() & etiquetas.ne("BENIGN") & etiquetas.ne("")
            indices = bloque.index[es_clase & validas][:restantes]
            if len(indices) == 0:
                continue

            seleccion = caracteristicas.loc[indices].copy()
            seleccion["Label"] = etiquetas.loc[indices].to_numpy()
            muestras[clase].append(seleccion)
            cantidades[clase] += len(seleccion)

        if all(cantidad == REGISTROS_POR_CLASE for cantidad in cantidades.values()):
            break

    if any(cantidad != REGISTROS_POR_CLASE for cantidad in cantidades.values()):
        raise ValueError(
            "No fue posible reunir la cantidad de flujos válidos requerida: "
            f"{cantidades}"
        )

    muestra = pd.concat(
        muestras["BENIGN"] + muestras["MALICIOUS"], ignore_index=True
    )
    return muestra, cantidades


def main() -> None:
    inicio_total = perf_counter()
    resultado: dict[str, Any] = {
        "fase": "6. Pruebas y validación",
        "prueba": "Ejecución offline de extremo a extremo en entorno controlado",
        "estado": "FALLÓ",
        "entorno": {
            "tipo": "sandbox local basado en archivos",
            "entrada_local": True,
            "captura_de_paquetes_en_vivo": False,
            "inyeccion_de_paquetes": False,
            "uso_de_sockets_por_la_prueba": False,
            "red_de_produccion": False,
        },
        "versiones": {
            "python": sys.version.split()[0],
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
        },
    }

    try:
        if not RUTA_METADATOS.is_file():
            raise FileNotFoundError(f"No se encontró el esquema: {RUTA_METADATOS}")

        metadatos = json.loads(RUTA_METADATOS.read_text(encoding="utf-8"))
        columnas = metadatos["feature_columns"]
        if len(columnas) != 78:
            raise ValueError(
                f"El modelo requiere 78 características; se hallaron {len(columnas)}"
            )

        RUTA_SANDBOX.mkdir(parents=True, exist_ok=True)
        ruta_entrada = RUTA_SANDBOX / "flujos_prueba_offline.csv"
        ruta_resultados = RUTA_SANDBOX / "resultado_inferencia.csv"
        ruta_alertas = RUTA_SANDBOX / "alertas_ids.csv"

        muestra, conteos_reales = crear_muestra_controlada(columnas)
        muestra.to_csv(ruta_entrada, index=False, encoding="cp1252")
        huella_entrada_antes = sha256(ruta_entrada)

        motor = IDSInferencia()
        datos_entrada = motor.cargar_archivo(
            ruta_entrada, limite=2 * REGISTROS_POR_CLASE
        )
        tiempo_inicio = perf_counter()
        predicciones = motor.clasificar(datos_entrada)
        duracion_inferencia = perf_counter() - tiempo_inicio

        if len(predicciones) != 2 * REGISTROS_POR_CLASE:
            raise AssertionError(f"Cantidad inesperada de resultados: {len(predicciones)}")
        if not predicciones["Estado"].eq("ANALIZADO").all():
            raise AssertionError("Al menos un flujo válido no fue analizado")
        if not set(predicciones["Predicción"]).issubset({"BENIGN", "MALICIOUS"}):
            raise AssertionError("El prototipo produjo una clase de salida no reconocida")

        alertas_esperadas = np.where(
            predicciones["Predicción"].eq("MALICIOUS"), "ALERTA", "NO"
        )
        if not np.array_equal(predicciones["Alerta"].to_numpy(), alertas_esperadas):
            raise AssertionError("La alerta no coincide con la predicción de cada flujo")

        alertas = predicciones.loc[predicciones["Alerta"].eq("ALERTA")].copy()
        if not alertas["Alerta"].eq("ALERTA").all():
            raise AssertionError("La salida de alertas contiene estados incorrectos")
        if alertas.empty:
            raise AssertionError("La muestra no produjo alertas para verificar la salida")

        rutas_salida_originales = (
            inferencia_ids.RUTA_SALIDA,
            inferencia_ids.RUTA_ALERTAS,
        )
        try:
            inferencia_ids.RUTA_SALIDA = ruta_resultados
            inferencia_ids.RUTA_ALERTAS = ruta_alertas
            motor.guardar_resultados(predicciones)
        finally:
            (
                inferencia_ids.RUTA_SALIDA,
                inferencia_ids.RUTA_ALERTAS,
            ) = rutas_salida_originales

        resultados_guardados = pd.read_csv(ruta_resultados, encoding="utf-8-sig")
        alertas_guardadas = pd.read_csv(ruta_alertas, encoding="utf-8-sig")
        if len(resultados_guardados) != len(predicciones):
            raise AssertionError("El archivo de resultados no conserva todas las filas")
        if len(alertas_guardadas) != len(alertas):
            raise AssertionError("El archivo de alertas no coincide con las predicciones")
        if not alertas_guardadas["Predicción"].eq("MALICIOUS").all():
            raise AssertionError("El archivo de alertas contiene predicciones no maliciosas")

        huella_entrada_despues = sha256(ruta_entrada)
        if huella_entrada_antes != huella_entrada_despues:
            raise AssertionError("El archivo de entrada fue modificado durante la prueba")

        conteos_predichos = {
            clase: int((predicciones["Predicción"] == clase).sum())
            for clase in ("BENIGN", "MALICIOUS")
        }
        resultado.update(
            {
                "estado": "PASÓ",
                "duracion_inferencia_segundos": duracion_inferencia,
                "muestra": {
                    "archivo_fuente": str(RUTA_FUENTE.relative_to(RAIZ_PROYECTO)),
                    "registros_por_clase_real": conteos_reales,
                    "total_registros": len(muestra),
                    "caracteristicas": len(columnas),
                    "predicciones": conteos_predichos,
                    "alertas_generadas": len(alertas),
                    "errores_de_datos": int(
                        predicciones["Estado"].eq("ERROR_DATOS").sum()
                    ),
                },
                "verificaciones": {
                    "entrada_sin_modificar": True,
                    "todos_los_registros_analizados": True,
                    "alertas_solo_para_prediccion_malicious": True,
                    "resultados_y_alertas_guardados_por_separado": True,
                    "evaluacion_de_desempeno_predictivo": False,
                },
                "artefactos": {
                    "entrada": str(ruta_entrada.relative_to(RAIZ_PROYECTO)),
                    "resultados": str(ruta_resultados.relative_to(RAIZ_PROYECTO)),
                    "alertas": str(ruta_alertas.relative_to(RAIZ_PROYECTO)),
                },
                "huella_sha256_entrada": huella_entrada_despues,
            }
        )
    except Exception as error:
        resultado["error"] = f"{type(error).__name__}: {error}"
    finally:
        resultado["duracion_total_segundos"] = perf_counter() - inicio_total
        RUTA_INFORME.parent.mkdir(parents=True, exist_ok=True)
        RUTA_INFORME.write_text(
            json.dumps(resultado, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    if resultado["estado"] != "PASÓ":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

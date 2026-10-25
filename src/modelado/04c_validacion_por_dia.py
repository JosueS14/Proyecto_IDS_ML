# Validación leave-one-day-out sobre CIC-IDS2017.
# Cada día con ataques (martes, miércoles, jueves y viernes) se usa una vez como prueba.
# El lunes contiene solo tráfico benigno y se mantiene siempre en entrenamiento.
# Las dos configuraciones de Random Forest se reportan completas; no se selecciona
# ninguna con estos resultados.

from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys
from time import perf_counter

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier


RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

entrenamiento = importlib.import_module("src.modelado.04_entrenar_random_forest")

RUTA_GRUPOS = (
    RAIZ_PROYECTO / "data" / "processed" / "dataset_cicids2017_preparado_grupos.parquet"
)
RUTA_RESULTADOS = RAIZ_PROYECTO / "docs" / "resultados_validacion_por_dia.json"

LUNES = ["Monday-WorkingHours.pcap_ISCX.csv"]
DIAS_EVALUADOS = {
    "martes": ["Tuesday-WorkingHours.pcap_ISCX.csv"],
    "miércoles": ["Wednesday-workingHours.pcap_ISCX.csv"],
    "jueves": [
        "Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv",
        "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv",
    ],
    "viernes": sorted(entrenamiento.ARCHIVOS_PRUEBA | {"Friday-WorkingHours-Morning.pcap_ISCX.csv"}),
}
CONFIGURACIONES = [("sin_balanceo", None), ("balanceado", "balanced")]


def ajustar(caracteristicas, objetivo, class_weight):
    modelo = RandomForestClassifier(
        n_estimators=entrenamiento.N_ESTIMADORES,
        max_depth=entrenamiento.MAX_PROFUNDIDAD,
        max_samples=entrenamiento.MAX_MUESTRAS_POR_ARBOL,
        class_weight=class_weight,
        random_state=entrenamiento.RANDOM_STATE,
        n_jobs=entrenamiento.N_JOBS,
    )
    inicio = perf_counter()
    modelo.fit(caracteristicas, objetivo)
    return modelo, perf_counter() - inicio


def deteccion_por_etiqueta(modelo, caracteristicas, predicciones, etiquetas_originales):
    filas = []
    for etiqueta in sorted(etiquetas_originales.unique()):
        mascara = (etiquetas_originales == etiqueta).to_numpy()
        detectados = int((predicciones[mascara] == entrenamiento.CLASE_MALICIOSA).sum())
        filas.append(
            {
                "etiqueta_original": etiqueta,
                "registros": int(mascara.sum()),
                "clasificados_malicious": detectados,
                "tasa": detectados / int(mascara.sum()),
            }
        )
    return filas


def main() -> None:
    caracteristicas, objetivo, _, columnas = entrenamiento.cargar_datos()
    grupos = pd.read_parquet(RUTA_GRUPOS)
    etiquetas_originales = grupos["label_original"].reset_index(drop=True)
    archivos = grupos["source_file"].reset_index(drop=True)
    objetivo = objetivo.reset_index(drop=True)
    caracteristicas = caracteristicas.reset_index(drop=True)

    resultados = []
    for dia, archivos_dia in DIAS_EVALUADOS.items():
        mascara_prueba = archivos.isin(archivos_dia).to_numpy()
        mascara_train = ~mascara_prueba
        x_train = caracteristicas.loc[mascara_train]
        y_train = objetivo.loc[mascara_train]
        x_test = caracteristicas.loc[mascara_prueba]
        y_test = objetivo.loc[mascara_prueba]
        etiquetas_test = etiquetas_originales.loc[mascara_prueba].reset_index(drop=True)

        filas_train_originales = len(y_train)
        x_train, y_train, muestra = entrenamiento.limitar_entrenamiento(x_train, y_train)
        clases_test = set(y_test.unique())
        if clases_test != {entrenamiento.CLASE_BENIGNA, entrenamiento.CLASE_MALICIOSA}:
            raise ValueError(f"El día {dia} no contiene ambas clases: {sorted(clases_test)}")

        for nombre, peso in CONFIGURACIONES:
            print(f"Prueba {dia} | {nombre}: entrenando...", flush=True)
            modelo, tiempo = ajustar(x_train, y_train, peso)
            predicciones = pd.Series(modelo.predict(x_test))
            metricas = entrenamiento.evaluar_modelo(modelo, x_test, y_test)
            por_etiqueta = deteccion_por_etiqueta(modelo, x_test, predicciones, etiquetas_test)
            resultados.append(
                {
                    "dia_prueba": dia,
                    "archivos_prueba": archivos_dia,
                    "configuracion": nombre,
                    "filas_entrenamiento": int(len(y_train)),
                    "filas_entrenamiento_originales": int(filas_train_originales),
                    "muestreo_entrenamiento": muestra,
                    "filas_prueba": int(len(y_test)),
                    "tiempo_entrenamiento_segundos": tiempo,
                    "metricas": metricas,
                    "por_etiqueta": por_etiqueta,
                }
            )
            print(
                f"  recall={metricas['recall_malicious']:.4f} "
                f"fpr={metricas['fpr']:.4f} "
                f"roc_auc={metricas['roc_auc']:.4f}",
                flush=True,
            )
            del modelo
        del x_train, y_train, x_test, y_test

    resumen = {}
    for nombre, _ in CONFIGURACIONES:
        recalls = [r["metricas"]["recall_malicious"] for r in resultados if r["configuracion"] == nombre]
        fprs = [r["metricas"]["fpr"] for r in resultados if r["configuracion"] == nombre]
        resumen[nombre] = {
            "recall_malicious_media": float(np.mean(recalls)),
            "recall_malicious_desv": float(np.std(recalls, ddof=1)),
            "fpr_media": float(np.mean(fprs)),
            "fpr_desv": float(np.std(fprs, ddof=1)),
        }

    salida = {
        "estrategia": "leave-one-day-out sobre martes, miércoles, jueves y viernes",
        "lunes_siempre_en_entrenamiento": LUNES,
        "parametros": {
            "n_estimators": entrenamiento.N_ESTIMADORES,
            "max_depth": entrenamiento.MAX_PROFUNDIDAD,
            "max_samples_per_tree": entrenamiento.MAX_MUESTRAS_POR_ARBOL,
            "random_state": entrenamiento.RANDOM_STATE,
            "limite_entrenamiento": entrenamiento.MAX_FILAS_ENTRENAMIENTO,
        },
        "nota": (
            "Ninguna configuración se selecciona con estos resultados. "
            "Recall por etiqueta = proporción de registros de cada etiqueta original "
            "clasificados como MALICIOUS."
        ),
        "resumen": resumen,
        "folds": resultados,
    }
    RUTA_RESULTADOS.write_text(json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    for resultado in resultados:
        m = resultado["metricas"]
        print(
            f"{resultado['dia_prueba']:<10} {resultado['configuracion']:<13} "
            f"recall={m['recall_malicious']:.4f} fpr={m['fpr']:.4f} "
            f"ap={m['average_precision']:.4f} roc_auc={m['roc_auc']:.4f}"
        )
    print(json.dumps(resumen, indent=2))
    print(f"Resultados: {RUTA_RESULTADOS.relative_to(RAIZ_PROYECTO)}")


if __name__ == "__main__":
    main()

# Validación leave-one-day-out repetida con varias semillas (configuración sin balanceo).
# Por cada semilla varían: el submuestreo estratificado del entrenamiento, el orden de
# las filas de entrenamiento y el random_state del Random Forest.
# No selecciona umbrales ni configuraciones. No modifica los artefactos oficiales.

from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

entrenamiento = importlib.import_module("src.modelado.04_entrenar_random_forest")
validacion = importlib.import_module("src.modelado.04c_validacion_por_dia")

RUTA_GRUPOS = validacion.RUTA_GRUPOS
RUTA_RESULTADOS = RAIZ_PROYECTO / "docs" / "resultados_multisemilla.json"
DIAS = validacion.DIAS_EVALUADOS
SEMILLAS = [42, 1, 2, 3, 4]


def preparar_entrenamiento(
    caracteristicas: pd.DataFrame, objetivo: pd.Series, semilla: int
) -> tuple[pd.DataFrame, pd.Series]:
    """Submuestreo estratificado y orden aleatorio dependientes de la semilla."""
    if len(objetivo) > entrenamiento.MAX_FILAS_ENTRENAMIENTO:
        indices = np.arange(len(objetivo))
        indices, _ = train_test_split(
            indices,
            train_size=entrenamiento.MAX_FILAS_ENTRENAMIENTO,
            stratify=objetivo,
            random_state=semilla,
        )
        caracteristicas = caracteristicas.iloc[indices]
        objetivo = objetivo.iloc[indices]
    orden = np.random.default_rng(semilla).permutation(len(objetivo))
    return caracteristicas.iloc[orden], objetivo.iloc[orden]


def ajustar_semilla(
    caracteristicas: pd.DataFrame, objetivo: pd.Series, semilla: int
) -> RandomForestClassifier:
    modelo = RandomForestClassifier(
        n_estimators=entrenamiento.N_ESTIMADORES,
        max_depth=entrenamiento.MAX_PROFUNDIDAD,
        max_samples=entrenamiento.MAX_MUESTRAS_POR_ARBOL,
        class_weight=None,
        random_state=semilla,
        n_jobs=entrenamiento.N_JOBS,
    )
    modelo.fit(caracteristicas, objetivo)
    return modelo


def resumir(valores: list[float]) -> dict[str, float]:
    return {
        "media": float(np.mean(valores)),
        "desv": float(np.std(valores, ddof=1)),
        "minimo": float(np.min(valores)),
        "maximo": float(np.max(valores)),
    }


def main() -> None:
    caracteristicas, objetivo, _, _ = entrenamiento.cargar_datos()
    grupos = pd.read_parquet(RUTA_GRUPOS)
    archivos = grupos["source_file"].reset_index(drop=True)
    objetivo = objetivo.reset_index(drop=True)
    caracteristicas = caracteristicas.reset_index(drop=True)

    mascaras_dia = {
        dia: archivos.isin(archivos_dia).to_numpy() for dia, archivos_dia in DIAS.items()
    }

    resultados = []
    for semilla in SEMILLAS:
        for dia_prueba in DIAS:
            mascara_prueba = mascaras_dia[dia_prueba]
            mascara_entrenamiento = ~mascara_prueba
            x_tr, y_tr = preparar_entrenamiento(
                caracteristicas[mascara_entrenamiento],
                objetivo[mascara_entrenamiento],
                semilla,
            )
            print(f"Semilla {semilla} | prueba {dia_prueba}: entrenando...", flush=True)
            modelo = ajustar_semilla(x_tr, y_tr, semilla)
            metricas = entrenamiento.evaluar_modelo(
                modelo,
                caracteristicas[mascara_prueba],
                objetivo[mascara_prueba],
            )
            resultados.append(
                {
                    "semilla": semilla,
                    "dia_prueba": dia_prueba,
                    "filas_entrenamiento": int(len(y_tr)),
                    "recall_malicious": metricas["recall_malicious"],
                    "fpr": metricas["fpr"],
                    "roc_auc": metricas["roc_auc"],
                    "average_precision": metricas["average_precision"],
                    "accuracy": metricas["accuracy"],
                }
            )
            print(
                f"  recall={metricas['recall_malicious']:.4f} "
                f"fpr={metricas['fpr']:.5f} "
                f"ap={metricas['average_precision']:.4f}",
                flush=True,
            )
            del modelo, x_tr, y_tr

    resumen_por_dia = {}
    for dia in DIAS:
        filas = [r for r in resultados if r["dia_prueba"] == dia]
        resumen_por_dia[dia] = {
            "recall_malicious": resumir([r["recall_malicious"] for r in filas]),
            "fpr": resumir([r["fpr"] for r in filas]),
            "average_precision": resumir([r["average_precision"] for r in filas]),
            "roc_auc": resumir([r["roc_auc"] for r in filas]),
        }

    promedio_por_semilla = []
    for semilla in SEMILLAS:
        filas = [r for r in resultados if r["semilla"] == semilla]
        promedio_por_semilla.append(
            {
                "semilla": semilla,
                "recall_malicious_promedio_dias": float(np.mean([r["recall_malicious"] for r in filas])),
                "fpr_promedio_dias": float(np.mean([r["fpr"] for r in filas])),
            }
        )

    salida = {
        "estrategia": "leave-one-day-out repetido con varias semillas",
        "configuracion": "sin_balanceo, umbral 0.5 (sin selección de umbral)",
        "semillas": SEMILLAS,
        "nota": (
            "Cada semilla cambia el submuestreo, el orden de entrenamiento y el random_state "
            "del Random Forest. No sustituye los resultados oficiales de docs/resultados_modelado.json."
        ),
        "resumen_global": {
            "recall_malicious": resumir([r["recall_malicious"] for r in resultados]),
            "fpr": resumir([r["fpr"] for r in resultados]),
            "average_precision": resumir([r["average_precision"] for r in resultados]),
            "roc_auc": resumir([r["roc_auc"] for r in resultados]),
        },
        "resumen_por_dia": resumen_por_dia,
        "promedio_por_semilla": promedio_por_semilla,
        "ejecuciones": resultados,
    }
    RUTA_RESULTADOS.write_text(json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    for dia, datos in resumen_por_dia.items():
        r = datos["recall_malicious"]
        f = datos["fpr"]
        print(
            f"{dia:<10} recall={r['media']:.4f} ± {r['desv']:.4f} "
            f"[{r['minimo']:.4f}, {r['maximo']:.4f}]  "
            f"fpr={f['media']:.5f} ± {f['desv']:.5f}"
        )
    g = salida["resumen_global"]
    print(
        f"GLOBAL     recall={g['recall_malicious']['media']:.4f} ± {g['recall_malicious']['desv']:.4f}  "
        f"fpr={g['fpr']['media']:.5f} ± {g['fpr']['desv']:.5f}"
    )
    print(f"Resultados: {RUTA_RESULTADOS.relative_to(RAIZ_PROYECTO)}")


if __name__ == "__main__":
    main()

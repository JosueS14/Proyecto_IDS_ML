# Análisis de umbral de decisión con selección anidada sobre leave-one-day-out.
# Para cada día de prueba:
#   1. El umbral se elige solo con predicciones fuera de bolsa (out-of-fold)
#      sobre los días de entrenamiento. El día de prueba no participa.
#   2. Se entrena un modelo con todos los días de entrenamiento y se evalúa
#      en el día de prueba con el umbral elegido y con el umbral 0.5 (referencia).
# El barrido de umbrales sobre el día de prueba es exploratorio y no se usa para elegir.

from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score, roc_curve


RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

entrenamiento = importlib.import_module("src.modelado.04_entrenar_random_forest")
validacion = importlib.import_module("src.modelado.04c_validacion_por_dia")

RUTA_GRUPOS = validacion.RUTA_GRUPOS
RUTA_RESULTADOS = RAIZ_PROYECTO / "docs" / "resultados_umbral_por_dia.json"
DIAS = validacion.DIAS_EVALUADOS
FPR_MAXIMO = 0.001
UMBRAL_REFERENCIA = 0.5
BARRIDO_EXPLORATORIO = [0.5, 0.3, 0.2, 0.1, 0.05, 0.02, 0.01, 0.005]


def probabilidad_maliciosa(modelo, caracteristicas) -> np.ndarray:
    indice = list(modelo.classes_).index(entrenamiento.CLASE_MALICIOSA)
    return modelo.predict_proba(caracteristicas)[:, indice]


def elegir_umbral(y_binario: np.ndarray, probabilidad: np.ndarray, fpr_maximo: float) -> float:
    """Mayor recall con FPR <= fpr_maximo; en empate, el umbral más conservador."""
    fpr, tpr, umbrales = roc_curve(y_binario, probabilidad, drop_intermediate=False)
    validos = fpr <= fpr_maximo
    indice = int(np.argmax(np.where(validos, tpr, -1.0)))
    return float(min(umbrales[indice], 1.0))


def metricas_con_umbral(y_binario: np.ndarray, probabilidad: np.ndarray, umbral: float) -> dict:
    predicho = probabilidad >= umbral
    tp = int(np.sum(predicho & y_binario))
    fn = int(np.sum(~predicho & y_binario))
    fp = int(np.sum(predicho & ~y_binario))
    tn = int(np.sum(~predicho & ~y_binario))
    return {
        "umbral": float(umbral),
        "recall_malicious": tp / (tp + fn),
        "fpr": fp / (fp + tn),
        "precision_malicious": tp / (tp + fp) if (tp + fp) > 0 else 0.0,
        "true_positives": tp,
        "false_negatives": fn,
        "false_positives": fp,
        "true_negatives": tn,
    }


def resumir(resultados: list[dict], clave: str) -> dict:
    recalls = [r[clave]["recall_malicious"] for r in resultados]
    fprs = [r[clave]["fpr"] for r in resultados]
    return {
        "recall_malicious_media": float(np.mean(recalls)),
        "recall_malicious_desv": float(np.std(recalls, ddof=1)),
        "fpr_media": float(np.mean(fprs)),
        "fpr_desv": float(np.std(fprs, ddof=1)),
    }


def main() -> None:
    caracteristicas, objetivo, _, _ = entrenamiento.cargar_datos()
    grupos = pd.read_parquet(RUTA_GRUPOS)
    archivos = grupos["source_file"].reset_index(drop=True)
    etiquetas_originales = grupos["label_original"].reset_index(drop=True)
    objetivo = objetivo.reset_index(drop=True)
    caracteristicas = caracteristicas.reset_index(drop=True)
    binario_total = (objetivo == entrenamiento.CLASE_MALICIOSA).to_numpy()

    mascaras_dia = {
        dia: archivos.isin(archivos_dia).to_numpy() for dia, archivos_dia in DIAS.items()
    }

    resultados = []
    for dia_prueba in DIAS:
        mascara_prueba = mascaras_dia[dia_prueba]
        mascara_entrenamiento = ~mascara_prueba
        dias_internos = [dia for dia in DIAS if dia != dia_prueba]

        # Fase 1: predicciones fuera de bolsa sobre los días de entrenamiento.
        probabilidad_oof = np.full(len(objetivo), np.nan)
        mascara_oof = np.zeros(len(objetivo), dtype=bool)
        for dia_interno in dias_internos:
            mascara_validacion = mascaras_dia[dia_interno]
            mascara_oof |= mascara_validacion
            mascara_tr = mascara_entrenamiento & ~mascara_validacion
            x_tr, y_tr, _ = entrenamiento.limitar_entrenamiento(
                caracteristicas[mascara_tr], objetivo[mascara_tr]
            )
            print(f"[{dia_prueba}] selección: validación interna {dia_interno}...", flush=True)
            modelo_interno, _ = validacion.ajustar(x_tr, y_tr, None)
            probabilidad_oof[mascara_validacion] = probabilidad_maliciosa(
                modelo_interno, caracteristicas[mascara_validacion]
            )
            del modelo_interno, x_tr, y_tr

        umbral = elegir_umbral(
            binario_total[mascara_oof],
            probabilidad_oof[mascara_oof],
            FPR_MAXIMO,
        )

        # Fase 2: modelo final con todos los días de entrenamiento, evaluado en el día de prueba.
        x_tr, y_tr, muestra = entrenamiento.limitar_entrenamiento(
            caracteristicas[mascara_entrenamiento], objetivo[mascara_entrenamiento]
        )
        print(f"[{dia_prueba}] entrenando modelo final...", flush=True)
        modelo, tiempo = validacion.ajustar(x_tr, y_tr, None)
        x_prueba = caracteristicas[mascara_prueba]
        y_prueba = binario_total[mascara_prueba]
        probabilidad_prueba = probabilidad_maliciosa(modelo, x_prueba)

        predicciones = pd.Series(
            np.where(probabilidad_prueba >= umbral, entrenamiento.CLASE_MALICIOSA, entrenamiento.CLASE_BENIGNA)
        )
        etiquetas_prueba = etiquetas_originales[mascara_prueba].reset_index(drop=True)
        resultado = {
            "dia_prueba": dia_prueba,
            "dias_validacion_interna": dias_internos,
            "filas_entrenamiento": int(len(y_tr)),
            "muestreo_entrenamiento": muestra,
            "tiempo_entrenamiento_segundos": tiempo,
            "umbral_elegido": umbral,
            "referencia_umbral_0_5": metricas_con_umbral(y_prueba, probabilidad_prueba, UMBRAL_REFERENCIA),
            "umbral_elegido_metricas": metricas_con_umbral(y_prueba, probabilidad_prueba, umbral),
            "roc_auc": float(roc_auc_score(y_prueba, probabilidad_prueba)),
            "average_precision": float(average_precision_score(y_prueba, probabilidad_prueba)),
            "por_etiqueta_umbral_elegido": validacion.deteccion_por_etiqueta(
                modelo, x_prueba, predicciones, etiquetas_prueba
            ),
            "barrido_exploratorio_no_usado_para_elegir": [
                metricas_con_umbral(y_prueba, probabilidad_prueba, u) for u in BARRIDO_EXPLORATORIO
            ],
        }
        resultados.append(resultado)
        print(
            f"  umbral={umbral:.4f} "
            f"recall={resultado['umbral_elegido_metricas']['recall_malicious']:.4f} "
            f"fpr={resultado['umbral_elegido_metricas']['fpr']:.4f} "
            f"(referencia 0.5: recall={resultado['referencia_umbral_0_5']['recall_malicious']:.4f} "
            f"fpr={resultado['referencia_umbral_0_5']['fpr']:.4f})",
            flush=True,
        )
        del modelo, x_tr, y_tr, x_prueba, probabilidad_prueba

    salida = {
        "estrategia": "leave-one-day-out con selección anidada del umbral",
        "fpr_maximo_para_seleccion": FPR_MAXIMO,
        "configuracion": "sin_balanceo",
        "nota": (
            "El umbral se elige solo con predicciones fuera de bolsa sobre los días de "
            "entrenamiento. El barrido en el día de prueba es exploratorio y no se usa "
            "para elegir umbrales."
        ),
        "resumen_umbral_0_5": resumir(
            [{"m": r["referencia_umbral_0_5"]} for r in resultados], "m"
        ),
        "resumen_umbral_elegido": resumir(
            [{"m": r["umbral_elegido_metricas"]} for r in resultados], "m"
        ),
        "folds": resultados,
    }
    RUTA_RESULTADOS.write_text(json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print(json.dumps(
        {"umbral_0_5": salida["resumen_umbral_0_5"], "umbral_elegido": salida["resumen_umbral_elegido"]},
        indent=2,
    ))
    print(f"Resultados: {RUTA_RESULTADOS.relative_to(RAIZ_PROYECTO)}")


if __name__ == "__main__":
    main()

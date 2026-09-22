# Entrena y evalúa Random Forest para la fase 4 del proyecto.

from __future__ import annotations

import gc
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Literal

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split


RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
DIRECTORIO_DATOS_PROCESADOS = RAIZ_PROYECTO / "data" / "processed"
RUTA_DATASET_PREPARADO = (
    DIRECTORIO_DATOS_PROCESADOS / "dataset_cicids2017_preparado.parquet"
)
RUTA_METADATOS = (
    DIRECTORIO_DATOS_PROCESADOS / "dataset_cicids2017_preparado_metadatos.json"
)
DIRECTORIO_MODELOS = DIRECTORIO_DATOS_PROCESADOS / "modelos"
RUTA_RESULTADOS = RAIZ_PROYECTO / "docs" / "resultados_modelado.json"
RANDOM_STATE = 42
N_ESTIMADORES = 50
MAX_FILAS_ENTRENAMIENTO = 500_000
MAX_PROFUNDIDAD = 20
MAX_MUESTRAS_POR_ARBOL = 0.5
N_JOBS = 4
COLUMNA_OBJETIVO = "Label"
CLASE_BENIGNA = "BENIGN"
CLASE_MALICIOSA = "MALICIOUS"


def cargar_datos() -> tuple[pd.DataFrame, pd.Series, list[str]]:
    if not RUTA_DATASET_PREPARADO.exists():
        raise FileNotFoundError(
            f"No existe el dataset preparado: {RUTA_DATASET_PREPARADO}"
        )
    if not RUTA_METADATOS.exists():
        raise FileNotFoundError(f"No existen los metadatos: {RUTA_METADATOS}")

    metadatos = json.loads(RUTA_METADATOS.read_text(encoding="utf-8"))
    columnas_caracteristicas = metadatos["feature_columns"]
    dataset = pd.read_parquet(RUTA_DATASET_PREPARADO)

    columnas_esperadas = columnas_caracteristicas + [COLUMNA_OBJETIVO]
    if dataset.columns.tolist() != columnas_esperadas:
        raise ValueError(
            "El esquema del dataset preparado no coincide con los metadatos."
        )

    if dataset[columnas_caracteristicas].isna().any().any():
        raise ValueError("El dataset contiene valores faltantes en las características.")
    if not np.isfinite(dataset[columnas_caracteristicas].to_numpy()).all():
        raise ValueError("El dataset contiene valores no finitos en las características.")

    etiquetas = set(dataset[COLUMNA_OBJETIVO].unique())
    if etiquetas != {CLASE_BENIGNA, CLASE_MALICIOSA}:
        raise ValueError(f"Etiquetas inesperadas en el dataset: {sorted(etiquetas)}")

    caracteristicas = dataset[columnas_caracteristicas]
    objetivo = dataset[COLUMNA_OBJETIVO]
    return caracteristicas, objetivo, columnas_caracteristicas


def dividir_datos(
    caracteristicas: pd.DataFrame, objetivo: pd.Series
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """Crear particiones estratificadas 80/10/10 con semilla fija."""
    indices = np.arange(len(objetivo))
    indices_entrenamiento_validacion, indices_prueba = train_test_split(
        indices,
        test_size=0.10,
        stratify=objetivo,
        random_state=RANDOM_STATE,
    )
    objetivo_entrenamiento_validacion = objetivo.iloc[
        indices_entrenamiento_validacion
    ]
    indices_entrenamiento, indices_validacion = train_test_split(
        indices_entrenamiento_validacion,
        test_size=1 / 9,
        stratify=objetivo_entrenamiento_validacion,
        random_state=RANDOM_STATE,
    )

    return (
        caracteristicas.iloc[indices_entrenamiento].copy(),
        caracteristicas.iloc[indices_validacion].copy(),
        caracteristicas.iloc[indices_prueba].copy(),
        objetivo.iloc[indices_entrenamiento].copy(),
        objetivo.iloc[indices_validacion].copy(),
        objetivo.iloc[indices_prueba].copy(),
    )


def limitar_entrenamiento(
    caracteristicas: pd.DataFrame, objetivo: pd.Series
) -> tuple[pd.DataFrame, pd.Series, int | None]:
    """Aplicar una muestra estratificada solo al conjunto de entrenamiento."""
    if len(objetivo) <= MAX_FILAS_ENTRENAMIENTO:
        return caracteristicas, objetivo, None

    indices = np.arange(len(objetivo))
    _, indices_muestra = train_test_split(
        indices,
        train_size=MAX_FILAS_ENTRENAMIENTO,
        stratify=objetivo,
        random_state=RANDOM_STATE,
    )
    return (
        caracteristicas.iloc[indices_muestra].copy(),
        objetivo.iloc[indices_muestra].copy(),
        MAX_FILAS_ENTRENAMIENTO,
    )


def evaluar_modelo(
    modelo: RandomForestClassifier,
    caracteristicas: pd.DataFrame,
    objetivo: pd.Series,
) -> dict[str, float | int]:
    """Calcular métricas con MALICIOUS como clase positiva."""
    predicciones = modelo.predict(caracteristicas)
    probabilidades = modelo.predict_proba(caracteristicas)
    indice_malicioso = list(modelo.classes_).index(CLASE_MALICIOSA)
    probabilidad_maliciosa = probabilidades[:, indice_malicioso]
    matriz = confusion_matrix(
        objetivo,
        predicciones,
        labels=[CLASE_BENIGNA, CLASE_MALICIOSA],
    )
    verdaderos_negativos, falsos_positivos, falsos_negativos, verdaderos_positivos = (
        matriz.ravel()
    )
    tasa_falsos_positivos = falsos_positivos / (
        falsos_positivos + verdaderos_negativos
    )

    return {
        "accuracy": float(accuracy_score(objetivo, predicciones)),
        "precision_malicious": float(
            precision_score(
                objetivo,
                predicciones,
                pos_label=CLASE_MALICIOSA,
                zero_division=0,
            )
        ),
        "recall_malicious": float(
            recall_score(
                objetivo,
                predicciones,
                pos_label=CLASE_MALICIOSA,
                zero_division=0,
            )
        ),
        "specificity_benign": float(
            verdaderos_negativos / (verdaderos_negativos + falsos_positivos)
        ),
        "f1_malicious": float(
            f1_score(
                objetivo,
                predicciones,
                pos_label=CLASE_MALICIOSA,
                zero_division=0,
            )
        ),
        "f1_macro": float(
            f1_score(objetivo, predicciones, average="macro", zero_division=0)
        ),
        "fpr": float(tasa_falsos_positivos),
        "average_precision": float(
            average_precision_score(
                (objetivo == CLASE_MALICIOSA).astype(int), probabilidad_maliciosa
            )
        ),
        "roc_auc": float(
            roc_auc_score(
                (objetivo == CLASE_MALICIOSA).astype(int), probabilidad_maliciosa
            )
        ),
        "true_negatives": int(verdaderos_negativos),
        "false_positives": int(falsos_positivos),
        "false_negatives": int(falsos_negativos),
        "true_positives": int(verdaderos_positivos),
    }


def entrenar_configuracion(
    nombre: str,
    peso_clases: Literal["balanced"] | None,
    datos: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series],
) -> tuple[dict[str, Any], RandomForestClassifier]:
    """Entrenar una configuración y evaluarla en validación y prueba."""
    (
        caracteristicas_entrenamiento,
        caracteristicas_validacion,
        caracteristicas_prueba,
        objetivo_entrenamiento,
        objetivo_validacion,
        objetivo_prueba,
    ) = datos
    modelo = RandomForestClassifier(
        n_estimators=N_ESTIMADORES,
        max_depth=MAX_PROFUNDIDAD,
        max_samples=MAX_MUESTRAS_POR_ARBOL,
        class_weight=peso_clases,
        random_state=RANDOM_STATE,
        n_jobs=N_JOBS,
    )
    inicio = perf_counter()
    modelo.fit(caracteristicas_entrenamiento, objetivo_entrenamiento)
    tiempo_entrenamiento = perf_counter() - inicio
    resultado = {
        "configuracion": nombre,
        "class_weight": peso_clases,
        "n_estimators": N_ESTIMADORES,
        "n_jobs": N_JOBS,
        "tiempo_entrenamiento_segundos": tiempo_entrenamiento,
        "validacion": evaluar_modelo(
            modelo, caracteristicas_validacion, objetivo_validacion
        ),
        "prueba_sin_reentrenamiento": evaluar_modelo(
            modelo, caracteristicas_prueba, objetivo_prueba
        ),
    }
    return resultado, modelo


def seleccionar_configuracion(resultados: list[dict[str, Any]]) -> dict[str, Any]:
    """Elegir por mayor recall de ataque y, en empate, menor FPR."""
    return max(
        resultados,
        key=lambda resultado: (
            resultado["validacion"]["recall_malicious"],
            -resultado["validacion"]["fpr"],
        ),
    )


def main() -> None:
    caracteristicas, objetivo, columnas_caracteristicas = cargar_datos()
    datos_particionados = dividir_datos(caracteristicas, objetivo)
    del caracteristicas, objetivo
    gc.collect()

    (
        caracteristicas_entrenamiento,
        caracteristicas_validacion,
        caracteristicas_prueba,
        objetivo_entrenamiento,
        objetivo_validacion,
        objetivo_prueba,
    ) = datos_particionados
    filas_entrenamiento_originales = len(objetivo_entrenamiento)
    (
        caracteristicas_entrenamiento,
        objetivo_entrenamiento,
        filas_entrenamiento_muestra,
    ) = limitar_entrenamiento(caracteristicas_entrenamiento, objetivo_entrenamiento)
    print(
        "Particiones: "
        f"entrenamiento={len(objetivo_entrenamiento):,}, "
        f"validacion={len(objetivo_validacion):,}, "
        f"prueba={len(objetivo_prueba):,}",
        flush=True,
    )
    if filas_entrenamiento_muestra is not None:
        print(
            "Se aplicará una muestra estratificada de entrenamiento por "
            f"restricción de recursos: {filas_entrenamiento_muestra:,} de "
            f"{filas_entrenamiento_originales:,} filas.",
            flush=True,
        )

    configuraciones: list[tuple[str, Literal["balanced"] | None]] = [
        ("sin_balanceo", None),
        ("balanceado", "balanced"),
    ]
    resultados: list[dict[str, Any]] = []
    datos_entrenamiento = (
        caracteristicas_entrenamiento,
        caracteristicas_validacion,
        caracteristicas_prueba,
        objetivo_entrenamiento,
        objetivo_validacion,
        objetivo_prueba,
    )
    for nombre, peso_clases in configuraciones:
        print(f"Entrenando configuración: {nombre}", flush=True)
        resultado, modelo = entrenar_configuracion(
            nombre, peso_clases, datos_entrenamiento
        )
        resultados.append(resultado)
        print(
            f"Validación {nombre}: "
            f"recall={resultado['validacion']['recall_malicious']:.4f}, "
            f"fpr={resultado['validacion']['fpr']:.4f}",
            flush=True,
        )
        del modelo
        gc.collect()

    seleccion = seleccionar_configuracion(resultados)
    nombre_seleccionado = seleccion["configuracion"]
    peso_seleccionado = seleccion["class_weight"]
    print(
        f"Configuración seleccionada por validación: {nombre_seleccionado}",
        flush=True,
    )

    caracteristicas_entrenamiento_validacion = pd.concat(
        [caracteristicas_entrenamiento, caracteristicas_validacion],
        ignore_index=True,
    )
    objetivo_entrenamiento_validacion = pd.concat(
        [objetivo_entrenamiento, objetivo_validacion],
        ignore_index=True,
    )
    modelo_seleccionado = RandomForestClassifier(
        n_estimators=N_ESTIMADORES,
        max_depth=MAX_PROFUNDIDAD,
        max_samples=MAX_MUESTRAS_POR_ARBOL,
        class_weight=peso_seleccionado,
        random_state=RANDOM_STATE,
        n_jobs=N_JOBS,
    )
    inicio = perf_counter()
    modelo_seleccionado.fit(
        caracteristicas_entrenamiento_validacion,
        objetivo_entrenamiento_validacion,
    )
    tiempo_reentrenamiento = perf_counter() - inicio
    metricas_prueba_finales = evaluar_modelo(
        modelo_seleccionado,
        caracteristicas_prueba,
        objetivo_prueba,
    )

    DIRECTORIO_MODELOS.mkdir(parents=True, exist_ok=True)
    ruta_modelo = DIRECTORIO_MODELOS / "random_forest_seleccionado.joblib"
    joblib.dump(
        {
            "modelo": modelo_seleccionado,
            "feature_columns": columnas_caracteristicas,
            "target_column": COLUMNA_OBJETIVO,
            "positive_class": CLASE_MALICIOSA,
            "random_state": RANDOM_STATE,
        },
        ruta_modelo,
    )

    importancia = sorted(
        zip(
            columnas_caracteristicas,
            modelo_seleccionado.feature_importances_,
        ),
        key=lambda elemento: elemento[1],
        reverse=True,
    )
    resultados_salida = {
        "dataset": str(RUTA_DATASET_PREPARADO.relative_to(RAIZ_PROYECTO)),
        "feature_count": len(columnas_caracteristicas),
        "training_parameters": {
            "n_estimators": N_ESTIMADORES,
            "max_depth": MAX_PROFUNDIDAD,
            "max_samples_per_tree": MAX_MUESTRAS_POR_ARBOL,
            "n_jobs": N_JOBS,
        },
        "split": {
            "train_original": filas_entrenamiento_originales,
            "train_used": len(objetivo_entrenamiento),
            "validation": len(objetivo_validacion),
            "test": len(objetivo_prueba),
            "strategy": "stratified_80_10_10",
            "random_state": RANDOM_STATE,
        },
        "class_counts": {
            "train": objetivo_entrenamiento.value_counts().to_dict(),
            "validation": objetivo_validacion.value_counts().to_dict(),
            "test": objetivo_prueba.value_counts().to_dict(),
        },
        "configurations": resultados,
        "selection": {
            "criterion": "max_validation_recall_malicious_then_min_validation_fpr",
            "configuration": nombre_seleccionado,
            "class_weight": peso_seleccionado,
            "retraining_seconds": tiempo_reentrenamiento,
            "final_test": metricas_prueba_finales,
            "model_path": str(ruta_modelo.relative_to(RAIZ_PROYECTO)),
        },
        "top_feature_importances": [
            {"feature": nombre, "importance": float(valor)}
            for nombre, valor in importancia[:20]
        ],
        "notes": [
            "No se aplicó escalado porque Random Forest no lo requiere.",
            "No se aplicó SMOTE ni otro balanceo sintético.",
            "El conjunto de prueba no se utilizó para seleccionar la configuración.",
            "No se fijó un umbral numérico de aceptación antes del entrenamiento.",
            "Por restricción de recursos, la muestra de entrenamiento se limitó a 500,000 filas estratificadas; validación y prueba se conservaron completas.",
        ],
    }
    RUTA_RESULTADOS.write_text(
        json.dumps(resultados_salida, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Modelo seleccionado: {ruta_modelo.relative_to(RAIZ_PROYECTO)}")
    print(f"Resultados: {RUTA_RESULTADOS.relative_to(RAIZ_PROYECTO)}")
    print(
        "Prueba final: "
        f"recall={metricas_prueba_finales['recall_malicious']:.4f}, "
        f"fpr={metricas_prueba_finales['fpr']:.4f}"
    )


if __name__ == "__main__":
    main()

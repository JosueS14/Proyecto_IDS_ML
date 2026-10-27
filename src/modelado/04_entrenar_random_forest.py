# Entrena y evalúa Random Forest para la fase 4 del proyecto.

from __future__ import annotations

import gc
import json
from pathlib import Path
import sys
from time import perf_counter
from typing import Any, Literal

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
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
RUTA_GRUPOS = (
    DIRECTORIO_DATOS_PROCESADOS / "dataset_cicids2017_preparado_grupos.parquet"
)
DIRECTORIO_MODELOS = DIRECTORIO_DATOS_PROCESADOS / "modelos"
RUTA_RESULTADOS = RAIZ_PROYECTO / "docs" / "resultados_modelado.json"
RANDOM_STATE = 42
N_ESTIMADORES = 50
MAX_FILAS_ENTRENAMIENTO = 1_762_141
NUM_PARTICIONES_HASH = 10
MAX_PROFUNDIDAD = 20
MAX_MUESTRAS_POR_ARBOL = 0.5
N_JOBS = 4
COLUMNA_OBJETIVO = "Label"
CLASE_BENIGNA = "BENIGN"
CLASE_MALICIOSA = "MALICIOUS"

# Se conservan para los análisis complementarios por día (04c/04d/04e).
ARCHIVOS_ENTRENAMIENTO = {
    "Monday-WorkingHours.pcap_ISCX.csv",
    "Tuesday-WorkingHours.pcap_ISCX.csv",
    "Wednesday-workingHours.pcap_ISCX.csv",
}
ARCHIVOS_VALIDACION = {
    "Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv",
    "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv",
}
ARCHIVOS_PRUEBA = {
    "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv",
    "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv",
    "Friday-WorkingHours-Morning.pcap_ISCX.csv",
}


def cargar_datos(
    incluir_etiquetas_originales: bool = False,
) -> tuple[pd.DataFrame, ...]:
    if not RUTA_DATASET_PREPARADO.exists():
        raise FileNotFoundError(
            f"No existe el dataset preparado: {RUTA_DATASET_PREPARADO}"
        )
    if not RUTA_METADATOS.exists():
        raise FileNotFoundError(f"No existen los metadatos: {RUTA_METADATOS}")
    if not RUTA_GRUPOS.exists():
        raise FileNotFoundError(
            f"No existe la procedencia de filas: {RUTA_GRUPOS}. "
            "Ejecute primero 03_preparar_dataset.py."
        )

    metadatos = json.loads(RUTA_METADATOS.read_text(encoding="utf-8"))
    columnas_caracteristicas = metadatos["feature_columns"]
    dataset = pd.read_parquet(RUTA_DATASET_PREPARADO)
    grupos = pd.read_parquet(RUTA_GRUPOS)

    columnas_esperadas = columnas_caracteristicas + [COLUMNA_OBJETIVO]
    if dataset.columns.tolist() != columnas_esperadas:
        raise ValueError(
            "El esquema del dataset preparado no coincide con los metadatos."
        )
    if grupos.columns.tolist() != ["source_file", "label_original"]:
        raise ValueError("El esquema de procedencia no coincide con lo esperado.")
    if len(grupos) != len(dataset):
        raise ValueError(
            "La cantidad de grupos no coincide con la cantidad de filas preparadas."
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
    salida_base = (
        caracteristicas.reset_index(drop=True),
        objetivo.reset_index(drop=True),
        grupos["source_file"].reset_index(drop=True),
    )
    if incluir_etiquetas_originales:
        return (
            *salida_base,
            grupos["label_original"].astype("string").reset_index(drop=True),
            columnas_caracteristicas,
        )
    return (*salida_base, columnas_caracteristicas)


def dividir_datos(
    caracteristicas: pd.DataFrame,
    etiquetas_originales: pd.Series,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Crear particiones estratificadas sin separar vectores de entrada idénticos.

    Cada vector de las 78 características se asigna a uno de diez pliegues mediante
    un hash estable. Se eligen dos pliegues distintos para validación y prueba
    procurando que todas las etiquetas originales estén representadas en ambos.
    Los pliegues restantes forman entrenamiento.
    """
    etiquetas_originales = etiquetas_originales.reset_index(drop=True).astype("string")
    if len(caracteristicas) != len(etiquetas_originales):
        raise ValueError("Las características y etiquetas no tienen la misma longitud.")

    hashes_flujo = pd.util.hash_pandas_object(
        caracteristicas, index=False
    ).to_numpy(dtype=np.uint64)
    pliegues = hashes_flujo % NUM_PARTICIONES_HASH
    tabla = pd.crosstab(
        pd.Series(pliegues, name="fold"),
        etiquetas_originales,
    ).reindex(index=range(NUM_PARTICIONES_HASH), fill_value=0)
    totales_etiqueta = tabla.sum(axis=0)
    fracciones_objetivo = {"train": 0.8, "validation": 0.1, "test": 0.1}

    candidatos: list[tuple[float, int, int]] = []
    for pliegue_validacion in range(NUM_PARTICIONES_HASH):
        for pliegue_prueba in range(NUM_PARTICIONES_HASH):
            if pliegue_validacion == pliegue_prueba:
                continue
            conteos = {
                "validation": tabla.loc[pliegue_validacion],
                "test": tabla.loc[pliegue_prueba],
                "train": totales_etiqueta
                - tabla.loc[pliegue_validacion]
                - tabla.loc[pliegue_prueba],
            }
            if any((serie <= 0).any() for serie in conteos.values()):
                continue

            puntuacion = 0.0
            for nombre, conteo in conteos.items():
                fraccion = fracciones_objetivo[nombre]
                proporcion_por_etiqueta = conteo / totales_etiqueta
                puntuacion += float(
                    (((proporcion_por_etiqueta - fraccion) / fraccion) ** 2).mean()
                )
            candidatos.append(
                (puntuacion, pliegue_validacion, pliegue_prueba)
            )

    if not candidatos:
        raise ValueError(
            "No se pudieron representar todas las etiquetas originales en "
            "entrenamiento, validación y prueba sin dividir vectores idénticos."
        )

    _, pliegue_validacion, pliegue_prueba = min(candidatos)
    mascaras = {
        "train": (pliegues != pliegue_validacion) & (pliegues != pliegue_prueba),
        "validation": pliegues == pliegue_validacion,
        "test": pliegues == pliegue_prueba,
    }
    indices = {
        nombre: np.flatnonzero(mascara)
        for nombre, mascara in mascaras.items()
    }

    filas_ambiguas = pd.DataFrame(
        {"hash": hashes_flujo, "etiqueta": etiquetas_originales}
    ).drop_duplicates()
    etiquetas_por_hash = filas_ambiguas.groupby("hash")["etiqueta"].nunique()
    hashes_ambiguos = set(etiquetas_por_hash[etiquetas_por_hash > 1].index.tolist())
    vectores_unicos = int(np.unique(hashes_flujo).size)
    metadatos_particion = {
        "strategy": "stratified_hash_group_split_by_feature_vector",
        "group_unit": "identical_78_feature_vector",
        "hash_folds": NUM_PARTICIONES_HASH,
        "validation_fold": int(pliegue_validacion),
        "test_fold": int(pliegue_prueba),
        "unique_feature_vectors": vectores_unicos,
        "duplicate_feature_rows": int(len(hashes_flujo) - vectores_unicos),
        "identical_feature_vectors_cross_partition": 0,
        "conflicting_label_feature_groups": len(hashes_ambiguos),
        "rows_with_conflicting_feature_labels": int(
            pd.Series(hashes_flujo).isin(hashes_ambiguos).sum()
        ),
        "label_counts_by_partition": {
            nombre: etiquetas_originales.iloc[idx].value_counts().sort_index().to_dict()
            for nombre, idx in indices.items()
        },
    }
    return indices, metadatos_particion


def seleccionar_indices_muestra(
    objetivo: pd.Series,
    etiquetas_estratificacion: pd.Series | None = None,
) -> tuple[np.ndarray, int | None]:
    """Submuestrear entrenamiento, preservando las etiquetas originales."""
    if len(objetivo) <= MAX_FILAS_ENTRENAMIENTO:
        return np.arange(len(objetivo)), None

    indices = np.arange(len(objetivo))
    estratos = (
        etiquetas_estratificacion
        if etiquetas_estratificacion is not None
        else objetivo
    )
    indices_muestra, _ = train_test_split(
        indices,
        train_size=MAX_FILAS_ENTRENAMIENTO,
        stratify=estratos,
        random_state=RANDOM_STATE,
    )
    return indices_muestra, MAX_FILAS_ENTRENAMIENTO


def limitar_entrenamiento(
    caracteristicas: pd.DataFrame, objetivo: pd.Series
) -> tuple[pd.DataFrame, pd.Series, int | None]:
    """Compatibilidad para los análisis complementarios por día."""
    indices_muestra, filas_muestra = seleccionar_indices_muestra(objetivo)
    return (
        caracteristicas.iloc[indices_muestra].copy(),
        objetivo.iloc[indices_muestra].copy(),
        filas_muestra,
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
        "balanced_accuracy": float(
            balanced_accuracy_score(objetivo, predicciones)
        ),
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
    datos: tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series],
) -> tuple[dict[str, Any], RandomForestClassifier]:
    """Entrenar una configuración y evaluarla únicamente en validación."""
    (
        caracteristicas_entrenamiento,
        caracteristicas_validacion,
        objetivo_entrenamiento,
        objetivo_validacion,
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
    }
    return resultado, modelo


def seleccionar_configuracion(resultados: list[dict[str, Any]]) -> dict[str, Any]:
    """Balancear detección de ataques y conservación del tráfico benigno."""
    return max(
        resultados,
        key=lambda resultado: (
            resultado["validacion"]["balanced_accuracy"],
            resultado["validacion"]["recall_malicious"],
            -resultado["validacion"]["fpr"],
        ),
    )


def evaluar_por_etiqueta_original(
    modelo: RandomForestClassifier,
    caracteristicas: pd.DataFrame,
    etiquetas_originales: pd.Series,
) -> list[dict[str, Any]]:
    """Desglosar detección por ataque original; BENIGN informa el FPR."""
    predicciones = pd.Series(modelo.predict(caracteristicas)).reset_index(drop=True)
    probabilidades = modelo.predict_proba(caracteristicas)[
        :, list(modelo.classes_).index(CLASE_MALICIOSA)
    ]
    etiquetas_originales = etiquetas_originales.reset_index(drop=True)
    detalle: list[dict[str, Any]] = []
    for etiqueta in sorted(etiquetas_originales.unique()):
        indices = np.flatnonzero(etiquetas_originales.eq(etiqueta).to_numpy())
        predichos_maliciosos = int(
            predicciones.iloc[indices].eq(CLASE_MALICIOSA).sum()
        )
        detalle.append(
            {
                "etiqueta_original": str(etiqueta),
                "registros": int(len(indices)),
                "predichos_malicious": predichos_maliciosos,
                "tasa_deteccion": float(predichos_maliciosos / len(indices)),
                "probabilidad_malicious_media": float(probabilidades[indices].mean()),
            }
        )
    return detalle


def main() -> None:
    (
        caracteristicas,
        objetivo,
        archivos_origen,
        etiquetas_originales,
        columnas_caracteristicas,
    ) = cargar_datos(incluir_etiquetas_originales=True)
    indices, metadatos_particion = dividir_datos(
        caracteristicas, etiquetas_originales
    )
    gc.collect()

    caracteristicas_entrenamiento = caracteristicas.iloc[indices["train"]].copy()
    caracteristicas_validacion = caracteristicas.iloc[indices["validation"]].copy()
    caracteristicas_prueba = caracteristicas.iloc[indices["test"]].copy()
    objetivo_entrenamiento = objetivo.iloc[indices["train"]].copy()
    objetivo_validacion = objetivo.iloc[indices["validation"]].copy()
    objetivo_prueba = objetivo.iloc[indices["test"]].copy()
    archivos_entrenamiento = archivos_origen.iloc[indices["train"]].copy()
    archivos_validacion = archivos_origen.iloc[indices["validation"]].copy()
    archivos_prueba = archivos_origen.iloc[indices["test"]].copy()
    etiquetas_entrenamiento = etiquetas_originales.iloc[indices["train"]].copy()
    etiquetas_validacion = etiquetas_originales.iloc[indices["validation"]].copy()
    etiquetas_prueba = etiquetas_originales.iloc[indices["test"]].copy()
    del caracteristicas, objetivo, archivos_origen, etiquetas_originales
    gc.collect()

    filas_entrenamiento_originales = len(objetivo_entrenamiento)
    indices_muestra, filas_entrenamiento_muestra = seleccionar_indices_muestra(
        objetivo_entrenamiento, etiquetas_entrenamiento
    )
    caracteristicas_entrenamiento = caracteristicas_entrenamiento.iloc[
        indices_muestra
    ].copy()
    objetivo_entrenamiento = objetivo_entrenamiento.iloc[indices_muestra].copy()
    archivos_entrenamiento = archivos_entrenamiento.iloc[indices_muestra].copy()
    etiquetas_entrenamiento = etiquetas_entrenamiento.iloc[indices_muestra].copy()
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
    datos_para_seleccion = (
        caracteristicas_entrenamiento,
        caracteristicas_validacion,
        objetivo_entrenamiento,
        objetivo_validacion,
    )
    for nombre, peso_clases in configuraciones:
        print(f"Entrenando configuración: {nombre}", flush=True)
        resultado, modelo = entrenar_configuracion(
            nombre, peso_clases, datos_para_seleccion
        )
        resultados.append(resultado)
        print(
            f"Validación {nombre}: "
            f"recall={resultado['validacion']['recall_malicious']:.4f}, "
            f"balanced_accuracy={resultado['validacion']['balanced_accuracy']:.4f}, "
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
    metricas_prueba_por_etiqueta = evaluar_por_etiqueta_original(
        modelo_seleccionado,
        caracteristicas_prueba,
        etiquetas_prueba,
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
        "environment": {
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
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
            **metadatos_particion,
            "source_files_by_partition": {
                "train": sorted(archivos_entrenamiento.unique().tolist()),
                "validation": sorted(archivos_validacion.unique().tolist()),
                "test": sorted(archivos_prueba.unique().tolist()),
            },
            "train_original_label_counts_used": etiquetas_entrenamiento.value_counts().sort_index().to_dict(),
            "random_state": RANDOM_STATE,
        },
        "class_counts": {
            "train": objetivo_entrenamiento.value_counts().to_dict(),
            "validation": objetivo_validacion.value_counts().to_dict(),
            "test": objetivo_prueba.value_counts().to_dict(),
        },
        "configurations": resultados,
        "selection": {
            "criterion": "max_validation_balanced_accuracy_then_recall_then_min_fpr",
            "configuration": nombre_seleccionado,
            "class_weight": peso_seleccionado,
            "final_training_rows": len(objetivo_entrenamiento_validacion),
            "retraining_seconds": tiempo_reentrenamiento,
            "final_test": metricas_prueba_finales,
            "final_test_by_original_label": metricas_prueba_por_etiqueta,
            "model_path": str(ruta_modelo.relative_to(RAIZ_PROYECTO)),
        },
        "top_feature_importances": [
            {"feature": nombre, "importance": float(valor)}
            for nombre, valor in importancia[:20]
        ],
        "notes": [
            "No se aplicó escalado porque Random Forest no lo requiere.",
            "No se aplicó SMOTE ni otro balanceo sintético.",
            "Las configuraciones candidatas se evaluaron únicamente con validación; la prueba se evaluó una sola vez después de seleccionar y reentrenar el modelo.",
            "No se fijó un umbral numérico de aceptación antes del entrenamiento.",
            "Por restricción de recursos, se configuró un límite operativo de 1,762,141 filas estratificadas para el entrenamiento; este tamaño no se optimizó como hiperparámetro. Validación y prueba se conservaron completas.",
            "Entrenamiento, validación y prueba contienen todos los ataques originales disponibles cuando el número de grupos lo permite; las particiones se realizan agrupando vectores idénticos de las 78 características.",
            "Una misma combinación de características puede tener etiquetas originales distintas; esas filas se conservan juntas y se reportan como ambigüedad irreducible para el modelo.",
            "La evaluación agrupada estima detección de ataques representados en el dataset; los análisis leave-one-day-out complementarios estiman transferencia a días/escenarios no vistos.",
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

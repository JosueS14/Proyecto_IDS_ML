# Calcula el recall por tipo de ataque sobre la prueba agrupada de 04.
# No reentrena el modelo: usa el artefacto persistido y la misma partición.

from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd


RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))
RUTA_MODELO = (
    RAIZ_PROYECTO / "data" / "processed" / "modelos" / "random_forest_seleccionado.joblib"
)
RUTA_RESULTADOS = RAIZ_PROYECTO / "docs" / "resultados_recall_por_ataque.json"
CLASE_BENIGNA = "BENIGN"

entrenamiento = importlib.import_module("src.modelado.04_entrenar_random_forest")


def main() -> None:
    caracteristicas, _, archivos, etiquetas_originales, columnas = (
        entrenamiento.cargar_datos(incluir_etiquetas_originales=True)
    )
    indices, metadatos_particion = entrenamiento.dividir_datos(
        caracteristicas, etiquetas_originales
    )
    artefacto = joblib.load(RUTA_MODELO)
    modelo = artefacto["modelo"]
    if list(artefacto["feature_columns"]) != columnas:
        raise ValueError("El modelo persistido no usa las columnas esperadas.")

    indices_prueba = indices["test"]
    x_prueba = caracteristicas.iloc[indices_prueba]
    etiquetas_originales = etiquetas_originales.iloc[indices_prueba].reset_index(drop=True)
    predicciones = pd.Series(modelo.predict(x_prueba))
    probabilidades = modelo.predict_proba(x_prueba)[
        :, list(modelo.classes_).index(entrenamiento.CLASE_MALICIOSA)
    ]

    detalle = []
    for etiqueta, grupo_idx in etiquetas_originales.groupby(etiquetas_originales).groups.items():
        indices = np.asarray(list(grupo_idx))
        predichas_malicioso = int((predicciones.iloc[indices] == entrenamiento.CLASE_MALICIOSA).sum())
        detalle.append(
            {
                "etiqueta_original": etiqueta,
                "registros": int(len(indices)),
                "predichos_malicious": predichas_malicioso,
                "tasa_deteccion": predichas_malicioso / len(indices),
                "probabilidad_media": float(probabilidades[indices].mean()),
            }
        )
    detalle.sort(key=lambda fila: (fila["etiqueta_original"] == CLASE_BENIGNA, fila["etiqueta_original"]))

    for fila in detalle:
        print(
            f"{fila['etiqueta_original']:<32} registros={fila['registros']:>8,}  "
            f"detectados={fila['predichos_malicious']:>8,}  "
            f"tasa={fila['tasa_deteccion']:.4f}"
        )

    resultado = {
        "modelo": str(RUTA_MODELO.relative_to(RAIZ_PROYECTO)),
        "particion": "prueba estratificada, agrupada por vector de características",
        "archivos": sorted(archivos.iloc[indices_prueba].unique().tolist()),
        "pliegue_prueba": metadatos_particion["test_fold"],
        "grupos_identicos_entre_particiones": metadatos_particion[
            "identical_feature_vectors_cross_partition"
        ],
        "nota": (
            "Tasa de detección = proporción de registros de cada etiqueta original "
            "clasificados como MALICIOUS. Para BENIGN, la tasa es la tasa de falsos positivos."
        ),
        "por_etiqueta": detalle,
    }
    RUTA_RESULTADOS.write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Resultados: {RUTA_RESULTADOS.relative_to(RAIZ_PROYECTO)}")


if __name__ == "__main__":
    main()

"""Carga el modelo persistido y clasifica flujos por lotes."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd


RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
RUTA_MODELO = (
    RAIZ_PROYECTO
    / "data"
    / "processed"
    / "modelos"
    / "random_forest_seleccionado.joblib"
)
RUTA_SALIDA = RAIZ_PROYECTO / "data" / "processed" / "resultado_inferencia.csv"
RUTA_ALERTAS = RAIZ_PROYECTO / "data" / "processed" / "alertas_ids.csv"
COLUMNA_OBJETIVO = "Label"
CLASE_BENIGNA = "BENIGN"
CLASE_MALICIOSA = "MALICIOUS"
COLUMNAS_CONTEXTUALES = [
    "Flow ID",
    "Timestamp",
    "Source IP",
    "Source Port",
    "Destination IP",
    "Destination Port",
    "Protocol",
]


class IDSInferencia:
    """Servicio local de inferencia por lotes para el prototipo IDS."""

    def __init__(self, ruta_modelo: Path = RUTA_MODELO) -> None:
        if not ruta_modelo.exists():
            raise FileNotFoundError(f"No existe el modelo: {ruta_modelo}")

        artefacto = joblib.load(ruta_modelo)
        self.modelo = artefacto["modelo"]
        self.columnas_caracteristicas = artefacto["feature_columns"]
        self.columna_objetivo = artefacto.get("target_column", COLUMNA_OBJETIVO)
        self.clase_positiva = artefacto.get("positive_class", CLASE_MALICIOSA)

    def cargar_archivo(self, ruta_archivo: Path, limite: int = 10_000) -> pd.DataFrame:
        """Cargar una vista acotada del archivo para mantener la UI responsiva."""
        extension = ruta_archivo.suffix.lower()
        if extension == ".csv":
            return pd.read_csv(
                ruta_archivo,
                encoding="cp1252",
                low_memory=False,
                nrows=limite,
            )
        if extension in {".parquet", ".pq"}:
            return pd.read_parquet(ruta_archivo).head(limite)
        raise ValueError("El archivo debe tener extensión CSV o Parquet.")

    def clasificar(self, datos: pd.DataFrame) -> pd.DataFrame:
        """Clasificar flujos y devolver una tabla orientada a la interfaz."""
        datos = datos.copy()
        datos.columns = datos.columns.str.strip()

        columnas_faltantes = sorted(
            set(self.columnas_caracteristicas).difference(datos.columns)
        )
        if columnas_faltantes:
            raise ValueError(
                "Faltan características requeridas por el modelo: "
                f"{columnas_faltantes}"
            )

        resultado = pd.DataFrame(index=datos.index)
        for columna in COLUMNAS_CONTEXTUALES:
            if columna in datos.columns:
                resultado[columna] = datos[columna].values

        resultado["No."] = np.arange(1, len(datos) + 1)
        resultado["Predicción"] = ""
        resultado["Confianza"] = np.nan
        resultado["Alerta"] = ""
        resultado["Estado"] = ""

        if self.columna_objetivo in datos.columns:
            etiquetas = datos[self.columna_objetivo].astype("string").str.strip()
            resultado["Etiqueta real"] = np.where(
                etiquetas.eq(CLASE_BENIGNA), CLASE_BENIGNA, CLASE_MALICIOSA
            )

        caracteristicas = datos[self.columnas_caracteristicas].apply(
            pd.to_numeric, errors="coerce"
        )
        caracteristicas = caracteristicas.replace([np.inf, -np.inf], np.nan)
        filas_validas = caracteristicas.notna().all(axis=1)

        resultado.loc[~filas_validas, "Estado"] = "ERROR_DATOS"
        resultado.loc[~filas_validas, "Alerta"] = "NO_ANALIZADO"

        if filas_validas.any():
            predicciones = self.modelo.predict(caracteristicas.loc[filas_validas])
            probabilidades = self.modelo.predict_proba(
                caracteristicas.loc[filas_validas]
            )
            confianza = probabilidades.max(axis=1)

            resultado.loc[filas_validas, "Predicción"] = predicciones
            resultado.loc[filas_validas, "Confianza"] = confianza
            resultado.loc[filas_validas, "Alerta"] = np.where(
                predicciones == self.clase_positiva, "ALERTA", "NO"
            )
            resultado.loc[filas_validas, "Estado"] = "ANALIZADO"

        columnas_principales = [
            "No.",
            "Predicción",
            "Confianza",
            "Alerta",
            "Estado",
            "Etiqueta real",
        ]
        columnas_principales = [
            columna for columna in columnas_principales if columna in resultado
        ]
        columnas_contextuales = [
            columna for columna in COLUMNAS_CONTEXTUALES if columna in resultado
        ]
        return resultado[columnas_principales + columnas_contextuales]

    @staticmethod
    def filtrar(datos: pd.DataFrame, texto: str) -> pd.DataFrame:
        """Aplicar filtros simples: malicious, benign, alerta o texto libre."""
        texto = texto.strip().lower()
        if not texto:
            return datos
        if texto in {"malicious", "malicioso", "alerta"}:
            return datos[
                (datos["Predicción"].str.lower() == "malicious")
                | (datos["Alerta"].str.lower() == "alerta")
            ]
        if texto in {"benign", "benigno"}:
            return datos[datos["Predicción"].str.lower() == "benign"]

        mascara = datos.astype(str).apply(
            lambda columna: columna.str.lower().str.contains(texto, regex=False)
        )
        return datos[mascara.any(axis=1)]

    @staticmethod
    def guardar_resultados(datos: pd.DataFrame) -> None:
        """Guardar resultados y alertas sin almacenar cargas útiles."""
        RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
        datos.to_csv(RUTA_SALIDA, index=False, encoding="utf-8-sig")
        datos[datos["Alerta"] == "ALERTA"].to_csv(
            RUTA_ALERTAS, index=False, encoding="utf-8-sig"
        )

    @staticmethod
    def resumen(datos: pd.DataFrame) -> dict[str, int]:
        """Obtener contadores para la barra de estado."""
        return {
            "total": int(len(datos)),
            "benign": int((datos["Predicción"] == CLASE_BENIGNA).sum()),
            "malicious": int((datos["Predicción"] == CLASE_MALICIOSA).sum()),
            "errores": int((datos["Estado"] == "ERROR_DATOS").sum()),
        }

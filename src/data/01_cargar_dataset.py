# Carga los archivos originales de CIC-IDS2017 sin transformarlos.

from pathlib import Path

import pandas as pd


RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
DIRECTORIO_DATOS_CRUDOS = RAIZ_PROYECTO / "data" / "raw"


def cargar_dataset(directorio_entrada: Path) -> pd.DataFrame:
    archivos_csv = sorted(directorio_entrada.glob("*.csv"))
    if not archivos_csv:
        raise FileNotFoundError(
            f"No se encontraron archivos CSV en: {directorio_entrada}"
        )

    marcos_datos = []
    for archivo in archivos_csv:
        print(f"Cargando: {archivo.name}")
        marcos_datos.append(
            pd.read_csv(
                archivo,
                encoding="cp1252",
                low_memory=False,
            )
        )

    return pd.concat(marcos_datos, ignore_index=True)


if __name__ == "__main__":
    conjunto_datos = cargar_dataset(DIRECTORIO_DATOS_CRUDOS)
    print(f"Archivos cargados: {len(list(DIRECTORIO_DATOS_CRUDOS.glob('*.csv')))}")
    print(f"Filas cargadas: {len(conjunto_datos):,}")
    print(f"Columnas cargadas: {len(conjunto_datos.columns)}")

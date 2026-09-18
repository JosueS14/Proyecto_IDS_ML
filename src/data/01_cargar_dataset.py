# Carga los archivos originales de CIC-IDS2017 sin transformarlos.

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUTA_RAW = PROJECT_ROOT / "data" / "raw"


def cargar_dataset(directorio_entrada: Path) -> pd.DataFrame:
    archivos_csv = sorted(directorio_entrada.glob("*.csv"))
    if not archivos_csv:
        raise FileNotFoundError(
            f"No se encontraron archivos CSV en: {directorio_entrada}"
        )

    dataframes = []
    for archivo in archivos_csv:
        print(f"Cargando: {archivo.name}")
        dataframes.append(
            pd.read_csv(
                archivo,
                encoding="cp1252",
                low_memory=False,
            )
        )

    return pd.concat(dataframes, ignore_index=True)


if __name__ == "__main__":
    dataset = cargar_dataset(RUTA_RAW)
    print(f"Archivos cargados: {len(list(RUTA_RAW.glob('*.csv')))}")
    print(f"Filas cargadas: {len(dataset):,}")
    print(f"Columnas cargadas: {len(dataset.columns)}")

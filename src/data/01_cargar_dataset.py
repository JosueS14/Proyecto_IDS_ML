import numpy as np
import pandas as pd
from pathlib import Path

RUTA_RAW = Path("data/raw")
RUTA_PROCESSED = Path("data/processed")
RUTA_PROCESSED.mkdir(parents=True, exist_ok=True)

def carga_limpiar_dataset(directorio_entrada: Path) -> pd.DataFrame:
    """
    Cargar todos los archivos CSV de CID-IDS2017, limpiar columnas identificadoras,
    trata de valores nulos/infinitos y unificar los datos.
    """
    archivos_csv = list(directorio_entrada.glob("*.csv"))
    if not archivos_csv:
        raise FileNotFoundError(f"No se encontraron archivos csv en : {directorio_entrada}")
    
    lista_dfs = []
    
    COLUMNAS_ELIMINAR = [
        "Flow ID", "Source IP", "Source Port", 
        "Destination IP", "Destination Port", "Timestamp"
    ]
    
    print(f"Encontrados {len(archivos_csv)} archivos CSV para procesar. \n" + 60*"=")
    
    for archivo in archivos_csv:
        print(f"Procesando: {archivo.name}...")
        
        df = pd.read_csv(archivo, encoding="latin1", low_memory=False)
        df.columns = df.columns.str.strip()
        
        col_presentes = [c for c in COLUMNAS_ELIMINAR if c in df.columns]
        if col_presentes:
            df = df.drop(columns=col_presentes)
        
        if "Label" in df.columns:
            df["Label"] = df["Label"].astype(str).str.strip()
            
            lista_dfs.append(df)
            
    df_completo = pd.concat(lista_dfs, ignore_index=True)
    print(60*"=")
    print(f"Total de registros cargados (bruto): {len(df_completo)}")
        
    print("\nIniciando limpieza de valores nulos a infinitos...")
        
    df_completo.replace([np.inf, -np.inf], np.nan, inplace=True)
        
    filas_iniciales = len(df_completo)
        
    df_completo.dropna(inplace=True)
    
    filas_finales = len(df_completo)
        
    print(f"Filas eliminadas por valores nulos/infinitos: {filas_iniciales - filas_finales:,}")
    print(f"Total de registros limpios: {filas_finales:,}")
        
    return df_completo



if __name__ == "__main__":
    df_limpio = carga_limpiar_dataset(RUTA_RAW)
    
    print("\n" + 60*"-")
    print("Distribucion Global de clases de trafico: ")
    print(60*"-")
    conteo_etiquetas = df_limpio["Label"].value_counts()
    for etiqueta, cantidad in conteo_etiquetas.items():
        porcentaje = (cantidad / len(df_limpio)) * 100
        print(f"- {etiqueta:<35}: {cantidad:>10,} ({porcentaje:>6.2f}%)")
        
    archivos_salida = RUTA_PROCESSED / "dataset_cicids2017_limpio.parquet"
    print(f"\nGuardando dataset procesado en: {archivos_salida}...")
        
    df_limpio.to_parquet(archivos_salida, index=False)
    print("Preprocesado completo exitosamente")

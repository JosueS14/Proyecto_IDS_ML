import pandas as pd
from pathlib import Path

ruta_datos = Path("data/raw")

archivos = [
    ruta_datos / "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv"
]

distribucion_total = {}

print("="*50)
print("Archivos encontrados")
for archivo in archivos:
    print("="*50)
    df = pd.read_csv(archivo, encoding="latin1")
    print(df.columns.tolist())
    df.columns = df.columns.str.strip()
    columnas = [
        "Flow ID",
        "Source IP",
        "Destination IP",
        "Timestamp",
        "Label"
    ]
    print(df[columnas].dtypes)
    filas_antes = len(df)
    df = df.dropna(how="all")
    filas_despues = len(df)
    print(f"Filas eliminadas: {filas_antes - filas_despues}")
    print(f"Lables nulos:  {df['Label'].isnull().sum()}")
    print(f"Archivo: {archivo.name}")
    print(f"Flows: {df.shape[0]}")
    
    conteo = df["Label"].value_counts()
    
    print("Etiquetas: ")
    print(conteo)
    
    for etiqueta, cantidad in conteo.items():
        distribucion_total[etiqueta] = (
            distribucion_total.get(etiqueta,0) + cantidad
        )
        
print("-"*50)
print("Distribucion global")
print("-"*50)
    
for etiqueta, cantidad in distribucion_total.items():
    print(f"{etiqueta}: {cantidad}")
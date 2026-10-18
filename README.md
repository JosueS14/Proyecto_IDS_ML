# Proyecto IDS ML

Prototipo experimental de detección de intrusiones por lotes. Clasifica flujos de red
de CIC-IDS2017 como `BENIGN` o `MALICIOUS` mediante un modelo Random Forest
persistido y una interfaz Tkinter.

## Despliegue local

Se requiere Python 3.13, Tkinter y los artefactos del modelo en `data/processed`.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-runtime.txt
python src/pruebas/07_verificar_despliegue.py
python src/prototipo/05_interfaz_tkinter.py
```

La interfaz recibe archivos CSV o Parquet, muestra una vista de hasta 10,000 filas y
guarda los resultados en `data/processed/resultado_inferencia.csv` y las alertas en
`data/processed/alertas_ids.csv`.

La instalación, operación, monitoreo y mantenimiento se documentan en
`thesis/07_despliegue_mantenimiento.md`.

El prototipo funciona por lotes. No captura paquetes, no bloquea conexiones y no
debe interpretarse como un IPS o como un detector de ataques zero-day.

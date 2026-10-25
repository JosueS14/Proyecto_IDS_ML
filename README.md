# Proyecto IDS ML

Prototipo experimental de detección de intrusiones por lotes. Clasifica flujos de red
de CIC-IDS2017 como `BENIGN` o `MALICIOUS` mediante un modelo Random Forest
persistido y una interfaz Tkinter.

## Despliegue local

Se requiere Python 3.13, Tkinter, Git LFS y los artefactos del modelo en `data/processed`.

```powershell
git lfs install
git lfs pull
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

## Reconstrucción del dataset

El dataset original de CIC-IDS2017 no se almacena en el repositorio por su tamaño. La guía
`docs/reconstruccion_dataset.md` explica cómo descargar los ocho CSV desde la fuente oficial,
verificarlos con SHA-256, reconstruir el Parquet preparado y volver a entrenar el modelo.

Para ejecutar únicamente el prototipo no es necesario descargar el dataset completo. Basta con
recuperar los artefactos mediante Git LFS y proporcionar un CSV o Parquet compatible a la
interfaz.

La reconstrucción del entrenamiento utiliza `requirements-train.txt` y el flujo de verificación
de `scripts/verificar_dataset.py`.

El prototipo funciona por lotes. No captura paquetes, no bloquea conexiones y no
debe interpretarse como un IPS o como un detector de ataques zero-day.

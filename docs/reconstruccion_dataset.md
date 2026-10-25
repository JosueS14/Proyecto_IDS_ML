# Reconstrucción del dataset y del modelo

Esta guía permite reconstruir localmente el dataset preparado y volver a entrenar el modelo a partir de los archivos originales de CIC-IDS2017.

La reconstrucción completa no es necesaria para ejecutar la interfaz. Para utilizar el prototipo únicamente se necesitan el modelo persistido y los metadatos publicados en `data/processed`.

## 1. Requisitos

- Windows 10 o posterior.
- Python 3.13.
- Espacio suficiente para los ocho archivos CSV y el dataset Parquet generado.
- Acceso a la página oficial de CIC-IDS2017:
  `https://www.unb.ca/cic/datasets/ids-2017.html`

El dataset original no se almacena en este repositorio porque contiene archivos grandes. Debe descargarse desde la fuente oficial y utilizarse únicamente de acuerdo con sus condiciones de uso.

## 2. Crear el entorno

Desde la raíz del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-train.txt
```

## 3. Descargar los archivos originales

Descarga los CSV de flujos de CIC-IDS2017 desde la página oficial y copia únicamente estos ocho archivos en `data/raw`:

```text
Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv
Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv
Friday-WorkingHours-Morning.pcap_ISCX.csv
Monday-WorkingHours.pcap_ISCX.csv
Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv
Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv
Tuesday-WorkingHours.pcap_ISCX.csv
Wednesday-workingHours.pcap_ISCX.csv
```

Puedes crear la carpeta si todavía no existe:

```powershell
New-Item -ItemType Directory -Force data\raw
```

Los nombres deben conservarse exactamente, incluyendo mayúsculas, minúsculas y la grafía `Infilteration` utilizada por el archivo original.

Verifica la cantidad de archivos antes de continuar:

```powershell
python -c "from pathlib import Path; print('CSV encontrados:', len(list(Path('data/raw').glob('*.csv'))))"
```

El resultado esperado es `CSV encontrados: 8`.

Después verifica la versión y la integridad estructural de los archivos:

```powershell
python scripts/verificar_dataset.py
```

El verificador comprueba los ocho nombres esperados, la codificación `cp1252`, la columna `Label`, las 85 columnas y las filas esperadas por archivo. También compara los tamaños y hashes SHA-256 contra `docs/dataset_manifest.json`.

Si estás incorporando por primera vez una copia oficial que todavía no tiene manifiesto, genera el manifiesto después de revisar la fuente:

```powershell
python scripts/verificar_dataset.py --write-manifest
```

El manifiesto generado debe revisarse y versionarse únicamente cuando los archivos correspondan a la versión de CIC-IDS2017 utilizada por el proyecto.

## 4. Comprender los datos

Este paso analiza los CSV sin modificar los archivos originales y genera el informe descriptivo:

```powershell
python src/data/02_comprender_dataset.py
```

El informe se guarda en:

```text
docs/resultados_comprension_datos.json
```

Con la versión utilizada por este proyecto se esperan aproximadamente:

- 8 archivos.
- 3,119,345 filas brutas.
- 288,602 filas completamente vacías.
- 2,830,743 registros con etiqueta válida.
- 85 columnas por archivo.

Si las cifras cambian, comprueba que descargaste la versión original de CIC-IDS2017 y documenta la diferencia antes de continuar.

## 5. Preparar el dataset

Ejecuta el pipeline de preparación:

```powershell
python src/data/03_preparar_dataset.py
```

El pipeline:

- Lee los CSV por bloques.
- Conserva `data/raw` sin modificaciones.
- Elimina filas completamente vacías.
- Convierte las características a valores numéricos.
- Elimina filas con valores faltantes o no finitos.
- Excluye identificadores, direcciones IP, puertos y `Timestamp`.
- Recodifica las etiquetas como `BENIGN` y `MALICIOUS`.
- Elimina duplicados exactos.

Los resultados se generan en:

```text
data/processed/dataset_cicids2017_preparado.parquet
data/processed/dataset_cicids2017_preparado_metadatos.json
data/processed/dataset_cicids2017_preparado_grupos.parquet
```

La salida esperada contiene aproximadamente 2,827,677 filas, 78 características y la columna `Label`.
El archivo de grupos conserva, en el mismo orden de filas, el nombre del CSV de origen. Esa columna
solo se utiliza para separar escenarios durante el modelado; nunca entra al modelo.

## 6. Entrenar nuevamente el modelo

Para repetir el entrenamiento y la evaluación:

```powershell
python src/modelado/04_entrenar_random_forest.py
```

El script separa archivos completos entre entrenamiento, validación y prueba, aplica el muestreo estratificado únicamente dentro del entrenamiento por limitaciones de recursos, compara las configuraciones sin ponderación y con `class_weight="balanced"`, y guarda el modelo seleccionado en:

```text
data/processed/modelos/random_forest_seleccionado.joblib
```

También actualiza:

```text
docs/resultados_modelado.json
```

En la configuración oficial, la partición de entrenamiento tiene 1,666,481 filas y no se submuestrea. El límite operativo de 1,762,141 filas solo se aplica si una partición lo supera. La validación y la prueba conservan sus particiones completas. La prueba no se utiliza para seleccionar la configuración.

La separación se realiza por día completo de captura para evitar que el mismo escenario temporal
aparezca en más de una partición:

- Entrenamiento: Monday, Tuesday y Wednesday.
- Validación: todos los archivos del jueves.
- Prueba: todos los archivos del viernes.

Esta separación es más exigente que una división aleatoria por fila. Las métricas resultantes miden
la transferencia entre escenarios del dataset y no deben interpretarse como detección de zero-day ni
como desempeño en una red real.

## 6.1 Análisis complementarios

Estos scripts no modifican el modelo oficial ni `docs/resultados_modelado.json`:

```powershell
python src/modelado/04b_analisis_por_ataque.py
python src/modelado/04d_analisis_umbral.py
python src/modelado/04e_validacion_multisemilla.py
```

- `04b`: recall por tipo de ataque, en `docs/resultados_recall_por_ataque.json`. Usa el modelo persistido.
- `04d`: selección anidada del umbral, en `docs/resultados_umbral_por_dia.json`. Requiere aproximadamente 16 ajustes del Random Forest.
- `04e`: leave-one-day-out con cinco semillas, en `docs/resultados_multisemilla.json`. Requiere 20 ajustes del Random Forest.
- `04c` (`src/modelado/04c_validacion_por_dia.py`) está implementado, pero no se ha ejecutado y no tiene resultados publicados.

Los resultados de `04d` y `04e` dependen del orden de las filas y de la semilla. Deben interpretarse junto con su desviación.

## 7. Verificar la reconstrucción

Después de preparar los datos y entrenar el modelo, ejecuta:

```powershell
python src/pruebas/07_verificar_despliegue.py
python src/pruebas/06_validar_prototipo.py
```

La primera orden verifica artefactos, dependencias y esquemas. La segunda comprueba la inferencia, el manejo de entradas inválidas, las alertas y la compilación de los componentes.

## 8. Inferencia sin reconstruir

Si solo necesitas ejecutar el prototipo, no descargues el dataset completo ni ejecutes el entrenamiento. Después de clonar el repositorio, recupera el modelo de Git LFS:

```powershell
git lfs install
git lfs pull
python src/pruebas/07_verificar_despliegue.py
python src/prototipo/05_interfaz_tkinter.py
```

En este modo debes proporcionar a la interfaz un CSV o Parquet compatible con las 78 características del modelo.

## 9. Rama publicada

Mientras los cambios no se integren a la rama principal, clona explícitamente la rama `Josue`:

```powershell
git clone --branch Josue https://github.com/JosueS14/Proyecto_IDS_ML.git
```

Después de integrar estos cambios a la rama principal, elimina `--branch Josue` de la orden.

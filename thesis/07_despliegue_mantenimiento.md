# Fase 7. Despliegue y mantenimiento

## 1. Propósito

Esta fase define las condiciones para instalar, ejecutar, verificar y mantener el
prototipo IDS. El despliegue corresponde a una ejecución local y controlada por lotes.
No incluye captura de paquetes, procesamiento en tiempo real, bloqueo de conexiones ni
operación sobre una red de producción.

## 2. Perfil de despliegue

El prototipo se ejecuta como una aplicación de escritorio en Windows mediante Python,
Tkinter y las bibliotecas de análisis y aprendizaje automático. La raíz del proyecto debe
conservar la siguiente estructura mínima:

```text
Proyecto_IDS_ML/
├── data/
│   └── processed/
│       ├── modelos/random_forest_seleccionado.joblib
│       ├── dataset_cicids2017_preparado_metadatos.json
│       └── dataset_cicids2017_preparado.parquet  (opcional para demostracion)
├── src/
│   ├── prototipo/05_interfaz_tkinter.py
│   ├── prototipo/inferencia_ids.py
│   └── pruebas/07_verificar_despliegue.py
├── requirements-runtime.txt
└── thesis/07_despliegue_mantenimiento.md
```

Los archivos originales de CIC-IDS2017 no son necesarios para ejecutar la inferencia
cuando ya se dispone del modelo persistido. Se conservan por separado para reproducir
las fases de comprensión, preparación y entrenamiento.

## 3. Instalación

### 3.1 Requisitos

- Windows 10 o posterior.
- Python 3.13.
- Tkinter, incluido en la instalación estándar de Python para Windows.
- Espacio suficiente para el modelo, los datos de entrada y los resultados generados.

### 3.2 Creación del entorno

Desde la raíz del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-runtime.txt
```

`requirements-runtime.txt` contiene únicamente las dependencias necesarias para la
ejecución del prototipo. `requirements.txt` conserva el entorno más amplio utilizado
durante el análisis y la documentación.

### 3.3 Verificación del despliegue

Antes de iniciar la interfaz se ejecuta:

```powershell
python src/pruebas/07_verificar_despliegue.py
```

El verificador comprueba la versión de Python, las dependencias principales, la carga del
modelo, la existencia de sus 78 características y la compatibilidad del esquema del
Parquet preparado cuando este archivo está disponible. El resultado se guarda en
`docs/resultados_despliegue.json`.

## 4. Operación

La interfaz se inicia con:

```powershell
python src/prototipo/05_interfaz_tkinter.py
```

El procedimiento operativo es:

1. Seleccionar un archivo `.csv` o `.parquet`.
2. Confirmar que el nombre del archivo aparece en la interfaz.
3. Pulsar **Analizar flujos**.
4. Revisar el total de registros, las predicciones, las alertas y los errores de datos.
5. Seleccionar un registro para consultar sus detalles.
6. Revisar los archivos de salida generados en `data/processed`.

La interfaz limita la vista a 10,000 filas para conservar una respuesta visual adecuada.
El procesamiento completo de un conjunto grande debe realizarse con el flujo de lotes
correspondiente y no debe confundirse con la vista de la interfaz.

## 5. Artefactos y salidas

| Artefacto | Función |
| --- | --- |
| `random_forest_seleccionado.joblib` | Modelo persistido seleccionado después de la validación. |
| `dataset_cicids2017_preparado_metadatos.json` | Esquema, etiqueta objetivo y orden de las 78 características. |
| `dataset_cicids2017_preparado.parquet` | Dataset preparado para demostraciones e inferencia local. |
| `resultado_inferencia.csv` | Resultado de la clasificación realizada. |
| `alertas_ids.csv` | Registros clasificados como `MALICIOUS`. |
| `resultados_despliegue.json` | Resultado de la verificación del entorno y artefactos. |

Los archivos originales de entrada no se sobrescriben. Las probabilidades producidas
por Random Forest son estimaciones del clasificador y no representan confianza
probabilística calibrada.

## 6. Monitoreo

El monitoreo se realiza después de cada lote procesado y durante las revisiones de
mantenimiento. Deben registrarse como mínimo:

- Fecha de ejecución y archivo analizado.
- Cantidad de filas recibidas, analizadas y marcadas como `ERROR_DATOS`.
- Cantidad de predicciones `BENIGN` y `MALICIOUS`.
- Cantidad de alertas generadas.
- Tiempo de carga, preparación e inferencia.
- Versión del modelo y del esquema utilizado.

Se debe comparar el comportamiento de los nuevos lotes con la línea base de la fase 4.
Una revisión de mantenimiento se activa cuando aumenta la proporción de errores, cambia
la distribución de clases, se eleva la tasa de falsos positivos o aparecen características
que no pertenecen al esquema registrado.

## 7. Mantenimiento y reentrenamiento

El modelo no se actualiza automáticamente. Para generar una nueva versión se sigue este
procedimiento:

1. Conservar los archivos originales de entrada sin modificarlos.
2. Ejecutar nuevamente la comprensión y preparación de los datos.
3. Confirmar que el orden y la cantidad de características sean compatibles.
4. Separar entrenamiento, validación y prueba sin reutilizar la prueba para seleccionar el
   modelo.
5. Entrenar y comparar las configuraciones definidas.
6. Evaluar la configuración seleccionada sobre la prueba reservada.
7. Ejecutar las pruebas de integración y el verificador de despliegue.
8. Guardar el modelo nuevo con su esquema, métricas, fecha y versión.
9. Conservar el modelo anterior como respaldo hasta aprobar la nueva versión.
10. Actualizar la guía y registrar el cambio en la bitácora.

Una nueva versión no debe publicarse únicamente porque aumente la exactitud. También
debe revisarse el recall de `MALICIOUS`, la tasa de falsos positivos, la matriz de confusión,
la calidad de los datos y la compatibilidad con la interfaz.

## 8. Seguridad y limitaciones

- Ejecutar el prototipo en un entorno controlado y aislado.
- Cargar únicamente modelos y metadatos generados por el proyecto.
- No almacenar cargas útiles, secretos ni contenido innecesario en las alertas.
- No utilizar el prototipo como IPS ni conectarlo directamente a una red de producción.
- No interpretar los resultados como evidencia de detección de ataques zero-day.
- Validar manualmente la interacción visual de Tkinter después de cambios en la interfaz.

## 9. Criterios de cierre

La fase 7 se considera cerrada cuando:

1. El entorno puede instalarse con `requirements-runtime.txt`.
2. El verificador confirma el modelo y el esquema requeridos.
3. La interfaz inicia sin reentrenar el modelo.
4. Se puede analizar un CSV o Parquet válido.
5. Se generan resultados y alertas separados.
6. Se documentan monitoreo, respaldo y reentrenamiento.
7. Las limitaciones del despliegue permanecen explícitas.

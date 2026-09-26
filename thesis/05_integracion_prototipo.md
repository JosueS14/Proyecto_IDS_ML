# Fase 5. Integración del prototipo

## 1. Propósito de la fase

Esta fase integra el modelo persistido de Random Forest con una interfaz de escritorio para analizar flujos por lotes. La interfaz adopta una organización visual inspirada en Wireshark, pero trabaja con registros de flujo del CIC-IDS2017 y no con paquetes capturados en tiempo real.

El prototipo se compone de:

- Motor de inferencia: `src/prototipo/inferencia_ids.py`.
- Interfaz de escritorio: `src/prototipo/05_interfaz_tkinter.py`.
- Modelo persistido: `data/processed/modelos/random_forest_seleccionado.joblib`.

## 2. Flujo integrado

```text
Archivo CSV o Parquet
          |
          v
Carga de una vista por lotes
          |
          v
Validación de las 78 características
          |
          v
Random Forest persistido
          |
          v
Predicción y confianza
          |
          v
Tabla de flujos, detalles y alertas
```

El modelo no utiliza `Flow ID`, direcciones IP, puertos ni `Timestamp` para decidir la clase. Cuando estos campos existen en el archivo, se muestran únicamente como contexto visual en la tabla y no se envían al clasificador.

## 3. Interfaz inspirada en Wireshark

La interfaz Tkinter incluye:

- Barra de herramientas con acciones **Abrir archivo**, **Analizar** y **Limpiar**.
- Campo de filtro para buscar `malicious`, `benign`, `alerta` o texto libre.
- Tabla principal de flujos con número, predicción, confianza, alerta, estado, etiqueta real y campos contextuales.
- Color rojo para tráfico clasificado como `MALICIOUS`.
- Color verde para tráfico `BENIGN`.
- Color amarillo para registros que no pudieron analizarse.
- Panel inferior de detalles del registro seleccionado.
- Barra de estado con totales de registros, tráfico benigno, tráfico malicioso y errores.

La semejanza con Wireshark se limita a la organización de análisis: barra de herramientas, filtro, lista principal, selección de registro y panel de detalles. No se afirma que la interfaz decodifique paquetes o implemente todas las funciones de Wireshark.

## 4. Entrada y procesamiento

El motor admite archivos `.csv` y `.parquet`.

- Los CSV se leen con codificación `cp1252`.
- Los nombres de columnas se normalizan eliminando espacios externos.
- Se valida que estén presentes las 78 características del modelo.
- Los valores no numéricos, nulos o infinitos se marcan como `ERROR_DATOS` y no se clasifican.
- El archivo original no se modifica.
- La interfaz carga como máximo 10,000 filas por ejecución para mantener la respuesta visual.

La limitación de 10,000 filas corresponde a la vista del prototipo. El procesamiento completo de un dataset debe realizarse mediante un flujo por lotes separado antes de mostrar los resultados en la interfaz.

## 5. Salidas y alertas

Después del análisis se generan localmente:

- `data/processed/resultado_inferencia.csv`: resultados de los flujos analizados.
- `data/processed/alertas_ids.csv`: únicamente los flujos clasificados como `MALICIOUS`.

Cada alerta incluye la predicción, la confianza, el estado y los campos contextuales disponibles. No se almacenan cargas útiles, secretos ni contenido de paquetes.

## 6. Ejecución

Desde la raíz del proyecto se ejecuta:

```bash
python src/prototipo/05_interfaz_tkinter.py
```

Después se selecciona un CSV o Parquet, se pulsa **Analizar** y se revisan los resultados en la tabla. El archivo de entrada recomendado para la demostración es `data/processed/dataset_cicids2017_preparado.parquet` o una muestra CSV de tamaño reducido.

## 7. Criterios de aceptación

La fase se considera integrada cuando:

1. La interfaz puede iniciarse sin volver a entrenar el modelo.
2. El modelo persistido se carga correctamente.
3. Se rechazan archivos con características faltantes.
4. Se clasifican registros válidos como `BENIGN` o `MALICIOUS`.
5. Se muestra la confianza de la predicción cuando el modelo la proporciona.
6. Las alertas se distinguen visualmente y se guardan en un archivo separado.
7. La selección de un registro muestra sus detalles.
8. Los archivos originales no se sobrescriben.

## 8. Limitaciones

- El prototipo funciona por lotes y no captura paquetes en tiempo real.
- La interfaz muestra una vista máxima de 10,000 filas por ejecución.
- La clasificación se realiza sobre características de flujo compatibles con CICFlowMeter.
- No se ejecutan bloqueos, terminaciones de conexión ni respuestas propias de un IPS.
- La interfaz no sustituye a Wireshark ni a un NIDS operacional.

Con estos componentes se cierra la **fase 5. Integración del prototipo**. La siguiente fase será la **fase 6. Pruebas y validación**, donde se comprobarán formalmente los módulos, la generación de alertas y el comportamiento ante entradas válidas e inválidas.

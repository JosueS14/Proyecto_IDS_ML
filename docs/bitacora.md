# Sesion 1
## Objetivo

Explorar el dataset CID-IDS-2017

## Resultados
- Se cargo correctamente el archivo Monday-WorkingHours.
- El dataset contiene 529,918 Flows.
- Tiene 85 columnas.
- La variable objetivo es Label.
Se detecto que varias columnas contienen espacios al inicio del nombre.

## Aprendizaje
Comprendo la diferiencia entre Flow, un Feature y un Label.

# Sesion 2
 

## Objetivo
Realizar uns inspeccion inicial al archivo Monday-WorkingHours del cnjunto de datos CIC-IDS2017.

## Resultados
- El archivo contiene 519,918 Flows.
- Se identificaron 85 columnas.
- Existen 45 columnas de tipo float64.
- Existen 35 columnas de tipo int64.
- Existen 5 columnas de tipo str.
- La variable aobjetivo es Label.
- Se detecto que la columna Flow Bytes/s contiene 64 valores faltantes.
Se observo que varias columnas presentan espacios en blanco al inicio del nombre.

## Aprendizaje
Comprendi como utilizar head(), shape(), cloumns(), info() para realizar una exploracion inicial.

# Sesion 3
Durante la exploración inicial del conjunto de datos CIC-IDS2017 se identificaron 288,602 registros completamente vacíos al analizar el archivo correspondiente a los ataques Web. Estos registros no contenían información de flujo ni etiqueta asociada. Debido a que no representan observaciones válidas de tráfico de red, se determinó que deberán ser eliminados durante la fase de preparación de los datos.

# Sesion 4
Durante la implementación del cálculo de la distribución global de etiquetas se presentó un error debido al uso del método item() en lugar de items(). El método item() intenta obtener un único valor, mientras que items() permite recorrer los pares clave-valor. Se corrigió la instrucción utilizando items(), permitiendo continuar con la acumulación de las etiquetas.

Análisis de distribución global: Se realizó un análisis de la distribución de etiquetas de los ocho archivos seleccionados del conjunto CIC-IDS2017. Después de eliminar las filas completamente vacías presentes en el archivo correspondiente a Web Attacks, se obtuvieron 3,036,743 flows. De estos, 2,273,097 corresponden a tráfico BENIGN y 763,646 a tráfico identificado como ataque. Al considerar una clasificación binaria, la distribución corresponde aproximadamente a 74.86 % de tráfico benigno y 25.14 % de tráfico malicioso. A nivel multiclase se observó una distribución considerablemente desigual entre los diferentes tipos de ataques, destacando DoS Hulk, PortScan y DDoS por su cantidad de muestras, mientras que categorías como Infiltration, Web Attack Sql Injection y Heartbleed presentan cantidades muy reducidas.

Decisión pendiente: El tratamiento del desbalance de clases será evaluado durante la fase de Data Preparation, evitando realizar modificaciones al dataset durante la etapa actual de Data Understanding.

# Sesion 5
## Objetivo

Formalizar la fase 1 de planificación y requisitos a partir del documento académico y del estado actual del repositorio.

## Resultados

- Se documentó el problema, el objetivo general, el alcance y las exclusiones de la primera versión.
- Se establecieron los requisitos funcionales, técnicos y de seguridad con identificadores verificables.
- Se definió `MALICIOUS` como la clase positiva para el cálculo de las métricas.
- Se confirmó el modo por lotes como alcance inicial y se excluyeron temporalmente el modo tiempo real, la respuesta activa y la clasificación multiclase.
- Se registraron riesgos y pendientes relacionados con la selección de características, el desbalance, la partición de datos y la reproducibilidad.

## Decisión

La siguiente actividad será la fase 2, Comprensión de los datos. No se modificó todavía el pipeline de preparación ni se entrenó un modelo.

# Sesion 6
## Objetivo

Ejecutar una comprensión reproducible de los ocho archivos CSV de CIC-IDS2017 sin modificar los datos originales.

## Resultados

- Se analizaron 3,119,345 filas brutas y 85 columnas con un esquema común.
- Se detectaron 288,602 filas completamente vacías en el archivo de Web Attacks.
- Se identificaron 2,830,743 registros con etiqueta válida: 2,273,097 `BENIGN` y 557,646 registros de ataque.
- La distribución binaria preliminar es 80.30 % `BENIGN` y 19.70 % `MALICIOUS`.
- Se detectaron valores faltantes en `Flow Bytes/s`, valores infinitos en `Flow Bytes/s` y `Flow Packets/s`, y valores potencialmente inconsistentes en variables como `Flow Duration` y tasas de flujo.
- Se detectaron 203 duplicados mediante huella de fila entre registros no completamente vacíos, sin contar coincidencias entre archivos diferentes.
- Se identificaron como posibles fuentes de fuga `Flow ID`, direcciones IP, puertos y `Timestamp`.

## Corrección de trazabilidad

El conteo reproducible de esta sesión sustituye el conteo global registrado en la sesión 4. La diferencia se documentó en `thesis/02_comprension_datos.md` y en `docs/resultados_comprension_datos.json`.

## Decisión

La limpieza, el tratamiento del desbalance, la selección final de características y la partición del dataset se trasladan a la fase 3. Los archivos originales no fueron modificados y no se entrenó ningún modelo.

# Sesion 7
## Objetivo

Ajustar `01_cargar_dataset.py` para que cumpla únicamente la función de carga.

## Resultados

- Se eliminó del cargador la eliminación de columnas identificadoras.
- Se eliminó del cargador el reemplazo de infinitos, la eliminación de valores nulos y la recodificación de etiquetas.
- Se eliminó la generación automática de un Parquet procesado.
- El cargador ahora conserva las filas, columnas, valores y etiquetas originales, y utiliza la misma codificación `cp1252` que el analizador de la fase 2.

## Decisión

La limpieza y transformación definitiva quedan reservadas para la fase 3. El archivo `02_comprender_dataset.py` continúa siendo el encargado del análisis descriptivo y no modifica los CSV de origen.

# Sesion 8
## Objetivo

Preparar el dataset para el modelado y definir el diseño inicial del prototipo IDS.

## Resultados

- Se ejecutó `src/data/03_preparar_dataset.py` sobre los ocho archivos CSV.
- Se eliminaron 288,602 filas completamente vacías, 2,867 filas con características inválidas y 199 duplicados exactos de la fila completa.
- Se generó un dataset preparado con 2,827,677 filas, 78 características y la columna objetivo `Label`.
- Las clases de salida son únicamente `BENIGN` y `MALICIOUS`.
- Se generaron los metadatos del esquema y de los contadores en `data/processed`.
- Se validó que la salida no contiene valores nulos ni valores no finitos.
- Se definió el diseño por módulos: ingesta, preparación de características, inferencia y alertas.

## Decisión

No se aplicó balanceo, escalado, selección basada en importancia ni división final de entrenamiento y prueba. Esas actividades se trasladan a la fase 4.

# Sesion 9
## Objetivo

Entrenar y evaluar Random Forest con las decisiones definidas para la fase 4.

## Resultados

- Se generaron particiones estratificadas 80/10/10 con `random_state=42`.
- Se compararon Random Forest sin balanceo y con `class_weight="balanced"`.
- La configuración balanceada obtuvo el mayor recall de `MALICIOUS` en validación: 0.998437.
- El modelo seleccionado alcanzó en prueba final un recall de 0.998113 y una tasa de falsos positivos de 0.001365.
- La matriz de confusión final registró 226,802 verdaderos negativos, 310 falsos positivos, 105 falsos negativos y 55,551 verdaderos positivos.
- Se persistió el modelo en `data/processed/modelos/random_forest_seleccionado.joblib`.

## Restricción

El entrenamiento completo superó el tiempo disponible del entorno. Se utilizó una muestra estratificada de 500,000 registros únicamente para entrenar; la validación y la prueba conservaron todos sus registros.

## Decisión

La fase 4 queda cerrada. La siguiente actividad será integrar el modelo seleccionado en el prototipo durante la fase 5.


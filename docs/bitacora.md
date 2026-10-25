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
- El archivo contiene 529,918 Flows.
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
- La configuración balanceada obtuvo el mayor recall de `MALICIOUS` en validación: 0.998149.
- El modelo seleccionado alcanzó en prueba final un recall de 0.997916 y una tasa de falsos positivos de 0.001220.
- La matriz de confusión final registró 226,835 verdaderos negativos, 277 falsos positivos, 116 falsos negativos y 55,540 verdaderos positivos.
- Se persistió el modelo en `data/processed/modelos/random_forest_seleccionado.joblib`.

Estos resultados corresponden a la partición aleatoria por fila utilizada originalmente y quedan
conservados como antecedente histórico. Fueron sustituidos como resultados principales por la
evaluación por día de captura documentada en la sesión 15.

## Restricción

El entrenamiento completo superó el tiempo disponible del entorno. Se utilizó una muestra estratificada de 1,762,141 registros únicamente para entrenar; la validación y la prueba conservaron todos sus registros.

## Decisión

La fase 4 queda cerrada. La siguiente actividad será integrar el modelo seleccionado en el prototipo durante la fase 5.

# Sesion 10
## Objetivo

Integrar el modelo persistido en un prototipo de escritorio con una interfaz inspirada en Wireshark.

## Resultados

- Se creó el motor `src/prototipo/inferencia_ids.py`.
- Se creó la interfaz Tkinter `src/prototipo/05_interfaz_tkinter.py`.
- Se validó la inferencia con un Parquet preparado y con un CSV original.
- La interfaz incluye tabla de flujos, filtro, panel de detalles, colores para alertas y barra de resumen.
- Se definió una vista máxima de 10,000 registros para mantener la interfaz responsiva.
- Se generó la documentación de integración en `thesis/05_integracion_prototipo.md`.

## Decisión

La interfaz funciona por lotes, no captura paquetes en tiempo real y no ejecuta acciones de bloqueo. La fase 6 se encargará de probar formalmente la integración y el manejo de entradas inválidas.

# Sesion 11
## Objetivo

Mejorar la interfaz del prototipo a partir de la revisión visual.

## Resultados

- Se sustituyeron los textos de acción por iconos de abrir, analizar, limpiar y filtrar.
- Se agregaron tooltips que describen cada acción al pasar el cursor.
- El panel de detalles ahora muestra todas las columnas del flujo original mediante desplazamiento vertical.
- Se conservaron el resumen de predicción, probabilidad estimada, alerta y estado.

## Verificación

La interfaz y el motor de inferencia compilan correctamente. La clasificación de Parquet y CSV continúa funcionando, y los archivos con características faltantes se rechazan con un error explícito.

# Sesion 13
## Objetivo

Ejecutar las pruebas funcionales, de integración, robustez y rendimiento básico del prototipo.

## Resultados

- Se ejecutaron 9 pruebas y todas pasaron.
- Se validó la carga del modelo y sus 78 características.
- Se probó inferencia con Parquet preparado y CSV original.
- Se verificó el rechazo de esquemas incompletos y el manejo de valores infinitos.
- Se validó la consistencia entre predicción y alerta.
- Se comprobó el filtro de la interfaz y la compilación de sus componentes.
- La inferencia de 1,000 filas tardó aproximadamente 0.08 segundos después de cargar el modelo.

## Decisión

La fase 6 queda cerrada. La fase 7 se enfocará en documentación de instalación, operación, monitoreo y mantenimiento.

# Sesion 12
## Objetivo

Revisar falsos positivos y mejorar la visualización de campos contextuales en la interfaz.

## Resultados

- Las predicciones `MALICIOUS` con etiqueta real `BENIGN` se identificaron como falsos positivos del modelo, no como un error de la interfaz.
- En la vista de 10,000 registros preparados se observaron 33 predicciones maliciosas y todas correspondieron a registros benignos.
- Se confirmó que `Timestamp`, `Flow ID`, `Source IP` y `Destination IP` no están disponibles en el Parquet preparado porque fueron excluidos para evitar fuga de información.
- La interfaz ahora muestra `NO DISPONIBLE EN ENTRADA` en lugar de dejar esos campos vacíos.

## Decisión

Para visualizar los valores originales de identificación y contexto se deben abrir los CSV de `data/raw`. Estos campos continuarán excluidos de las características utilizadas por el modelo.

# Sesion 14
## Objetivo

Cerrar la fase 7 de despliegue y mantenimiento del prototipo IDS.

## Resultados

- Se documentó la instalación, operación, monitoreo, respaldo y reentrenamiento en `thesis/07_despliegue_mantenimiento.md`.
- Se creó `requirements-runtime.txt` con las dependencias mínimas para ejecutar la interfaz y leer CSV o Parquet.
- Se creó `src/pruebas/07_verificar_despliegue.py` para comprobar artefactos, esquema, dependencias y compatibilidad del Parquet preparado.
- Se agregó el procedimiento de ejecución rápida al `README.md`.
- El verificador genera `docs/resultados_despliegue.json` sin modificar los datos de entrada.

## Decisión

El despliegue queda limitado a ejecución local por lotes. El modelo no se actualiza automáticamente; cualquier reentrenamiento debe conservar el modelo anterior, repetir la validación y registrar la nueva versión antes de reemplazar el artefacto activo.

# Sesion 15
## Objetivo

Eliminar la fuga de escenario causada por la partición aleatoria por fila.

## Resultados

- El pipeline conserva la procedencia de cada fila en `data/processed/dataset_cicids2017_preparado_grupos.parquet`.
- La procedencia no se utiliza como característica del modelo.
- Se separaron días completos entre entrenamiento, validación y prueba.
- El entrenamiento utiliza lunes, martes y miércoles; la validación utiliza jueves y la prueba utiliza viernes.
- Se reentrenaron las dos configuraciones de Random Forest con la nueva partición.
- La configuración sin balanceo fue seleccionada por validación con recall `0.019856`.
- La prueba final obtuvo recall `0.076022`, lo que evidencia una generalización limitada hacia escenarios de ataque no presentes en el entrenamiento.

## Decisión

Las métricas anteriores basadas en una partición aleatoria por fila dejan de ser las métricas principales. La evaluación por día de captura se conserva como resultado válido para analizar transferencia entre escenarios de CIC-IDS2017 y no se interpreta como detección de zero-day ni como desempeño en redes reales.

Nota posterior (sesiones 17 y 18): el valor 0.076022 depende del orden de las filas de entrenamiento. Con el mismo modelo y los mismos datos, el viernes puede obtener recall entre 0.085 y 0.282 según la semilla y el orden. Por ello, 0.076022 se conserva como una ejecución oficial y no como el valor representativo.

# Sesion 16
## Objetivo

Calcular el recall por tipo de ataque sobre la partición de prueba por día, sin reentrenar el modelo.

## Resultados

- `src/modelado/04b_analisis_por_ataque.py` usa el artefacto persistido y la partición de 04.
- Resultados en `docs/resultados_recall_por_ataque.json` (prueba: viernes):
  - Bot: 0 de 1,956 detectados.
  - DDoS: 21,876 de 128,025 detectados (17.1 %).
  - PortScan: 78 de 158,804 detectados (0.05 %).
  - BENIGN: 148 falsos positivos de 413,928 (FPR 0.036 %).

## Decisión

La baja sensibilidad se concentra en tipos de ataque distintos de los presentes en el entrenamiento. El análisis no modifica el modelo oficial.

# Sesion 17
## Objetivo

Evaluar si elegir el umbral de decisión mejora el recall sin aumentar los falsos positivos.

## Resultados

- `src/modelado/04d_analisis_umbral.py` aplica selección anidada: el umbral se elige con predicciones fuera de bolsa sobre los días de entrenamiento, con FPR máximo de 0.1 %, y se evalúa en el día de prueba.
- Umbrales elegidos: martes 0.620, miércoles 0.369, jueves 0.559 y viernes 0.520.
- Recall medio con umbral 0.5: 0.073 ± 0.137. Con umbral elegido: 0.074 ± 0.136.
- FPR medio con umbral 0.5: 0.00106. Con umbral elegido: 0.00088.
- El barrido exploratorio muestra recall alto en miércoles y jueves con umbrales bajos, pero esos umbrales no se pueden identificar de forma fiable con la selección interna.
- Se detectó sensibilidad al orden de las filas: el fold de viernes da recall 0.278 con el orden del Parquet y 0.076 con el orden de `04_entrenar_random_forest.py` (Mon-Wed + Thu). Un control con todas las filas de entrenamiento, sin submuestreo, dio 0.278; por tanto, la diferencia proviene del orden y no del submuestreo.
- Resultados en `docs/resultados_umbral_por_dia.json`.

## Decisión

No se cambia el umbral oficial de 0.5. El umbral elegido en validación no mejora de forma consistente el recall.

# Sesion 18
## Objetivo

Cuantificar la variabilidad del resultado por semilla y por orden de entrenamiento.

## Resultados

- `src/modelado/04e_validacion_multisemilla.py` ejecuta leave-one-day-out con 5 semillas (42, 1, 2, 3, 4). Cada semilla cambia el submuestreo estratificado, el orden de entrenamiento y el `random_state` del Random Forest.
- Recall por día (media ± desviación; rango):
  - Martes: 0.0001 ± 0.0000.
  - Miércoles: 0.0063 ± 0.0011; rango 0.0050 - 0.0077.
  - Jueves: 0.0191 ± 0.0168; rango 0.0045 - 0.0469.
  - Viernes: 0.2318 ± 0.0844; rango 0.0849 - 0.2819.
- Global: recall 0.064 ± 0.107; FPR 0.0012 ± 0.0011.
- Resultados en `docs/resultados_multisemilla.json`.

## Estado pendiente

- `src/modelado/04c_validacion_por_dia.py` está implementado, pero no se ha ejecutado: `docs/resultados_validacion_por_dia.json` no existe. Sus resultados no se reportan.

## Decisión

Presentar la tabla multi-semilla como resultado principal de generalización. El resultado oficial de 0.076 se reporta como una ejecución dentro de esa distribución. Los artefactos oficiales no se modifican.

# Sesion 19
## Objetivo

Ejecutar la validación leave-one-day-out con ambas configuraciones (`04c_validacion_por_dia.py`), pendiente desde la sesión 18.

## Resultados

- Resultados en `docs/resultados_validacion_por_dia.json`.
- Sin balanceo: recall medio 0.0728 ± 0.1370; FPR medio 0.00105 ± 0.00123.
- Balanceado: recall medio 0.0723 ± 0.0929; FPR medio 0.00177 ± 0.00156.
- Balanceado obtiene recall 0.2013 en jueves, pero 0.0789 en viernes (ROC-AUC 0.584).
- Miércoles y viernes (sin balanceo) difieren ligeramente de 04d: 0.0060 frente a 0.0064, y 0.2781 frente a 0.2786. Causa no identificada; no altera las conclusiones.

## Decisión

Se mantiene la configuración sin balanceo: igual recall que la balanceada y menor FPR. La sección 10.5 de `thesis/04_desarrollo_modelo.md` documenta la tabla completa.


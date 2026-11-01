# Fase 4. Desarrollo del modelo

## 1. Propósito de la fase

Esta fase corresponde al modelado de CRISP-DM. Su objetivo es entrenar y comparar dos configuraciones de Random Forest sobre el dataset preparado. Las configuraciones candidatas se comparan únicamente mediante validación; la prueba se reserva hasta después de seleccionar y reentrenar el modelo final.

La evaluación principal responde a la detección de ataques que sí están representados
en CIC-IDS2017. Además, se conserva una evaluación secundaria por día completo para
medir transferencia hacia escenarios de captura no vistos.

Las decisiones adoptadas antes del entrenamiento fueron:

- Clasificador principal: Random Forest.
- Características: las 78 variables numéricas del dataset preparado.
- Variable positiva: `MALICIOUS`.
- División principal: se agrupan los vectores idénticos de las 78 características; no se separan archivos, días ni sesiones de captura. Las etiquetas originales quedan representadas en cada partición cuando hay grupos suficientes.
- Proporciones aproximadas: 80 % entrenamiento, 10 % validación y 10 % prueba.
- Semilla: `random_state=42`.
- Configuraciones: sin balanceo y con `class_weight="balanced"`.
- Criterio de selección: mayor balanced accuracy en validación; desempate por recall de `MALICIOUS` y luego menor FPR.
- Umbral numérico de aceptación: no se fijó antes del entrenamiento.

## 2. Procedimiento reproducible

El procedimiento se implementó en `src/modelado/04_entrenar_random_forest.py`.

1. Se carga el Parquet preparado y sus metadatos.
2. Se valida que las 78 características coincidan exactamente con el esquema registrado.
3. Se verifica que no existan valores faltantes, valores no finitos ni etiquetas desconocidas.
4. Se agrupan las filas por el vector exacto de las 78 características, que es la entrada efectiva del modelo.
5. Se calcula un hash del vector de características y se distribuyen los grupos en diez pliegues deterministas. En la ejecución registrada, el pliegue 7 se usa para validación, el 8 para prueba y los ocho restantes para entrenamiento; se seleccionan pliegues que mantienen las etiquetas originales representadas cuando hay grupos suficientes.
6. Se submuestrea solo entrenamiento, estratificando por etiqueta de ataque original para conservar las clases minoritarias.
7. Se entrenan Random Forest sin balanceo y con `class_weight="balanced"`.
8. Se selecciona usando únicamente validación.
9. Se reentrena la configuración seleccionada con entrenamiento y validación.
10. Se evalúa una sola vez sobre prueba y se reportan métricas binarias y por etiqueta original.
11. Se persiste el modelo y se guardan las métricas, la partición y la importancia de características.

## 3. Restricción de recursos

La partición es por vector de características, no por archivo o sesión de captura. Los
ocho CSV de origen aparecen en entrenamiento, validación y prueba, como muestra
`source_files_by_partition` en `docs/resultados_modelado.json`. La agrupación impide que
vectores de entrada exactamente idénticos crucen de una partición a otra, pero no
garantiza independencia entre sesiones ni escenarios.

La partición agrupada contiene 2,272,892 filas de entrenamiento antes del límite operativo,
279,147 de validación y 275,638 de prueba. El entrenamiento se submuestreó a 1,762,141
filas, estratificadas por etiqueta original. La validación y la prueba conservan todos sus
registros.

La configuración seleccionada se reentrenó con las 1,762,141 filas de entrenamiento
muestreadas más las 279,147 filas de validación, para un total de 2,041,288. La prueba no
se incorpora al reentrenamiento. El parámetro `max_samples=0.5` hace que cada árbol utilice
una muestra de la mitad de las filas disponibles para ese ajuste. No se generaron datos
sintéticos ni se modificaron los archivos originales o el dataset preparado.

Los parámetros utilizados fueron:

| Parámetro | Valor |
| --- | ---: |
| Número de árboles | 50 |
| Profundidad máxima | 20 |
| Muestras por árbol | 0.5 del entrenamiento disponible |
| Hilos de ejecución | 4 |
| Semilla aleatoria | 42 |

## 4. Resultados de validación

Los resultados de esta ejecución se generaron con Python 3.14.6, NumPy 2.4.6,
pandas 3.0.3, scikit-learn 1.9.0 y joblib 1.5.3. Las cifras completas y la
procedencia del entorno están registradas en `docs/resultados_modelado.json`; las
tablas de este documento presentan sus valores redondeados a seis decimales.

| Configuración | Accuracy | Balanced accuracy | Precision `MALICIOUS` | Recall `MALICIOUS` | F1 macro | FPR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Sin balanceo | 0.998470 | 0.997365 | 0.997094 | 0.995484 | 0.997662 | 0.000754 |
| `class_weight="balanced"` | 0.998392 | 0.998003 | 0.994871 | 0.997342 | 0.997546 | 0.001336 |

Se seleccionó la configuración balanceada: obtuvo balanced accuracy 0.998003 frente a
0.997365 para la configuración sin balanceo. La configuración sin balanceo tuvo algo más
de precisión y menor FPR en validación; por eso se reportan ambas y se da prioridad a la
balanced accuracy, que considera tanto la detección de ataques como el reconocimiento de
tráfico benigno.

## 5. Evaluación final sobre prueba

Después de seleccionar la configuración mediante validación, la configuración balanceada
se reentrenó con entrenamiento más validación y se evaluó una sola vez sobre la prueba
reservada. En esta partición están representados los 14 tipos de ataque originales.

| Métrica | Resultado |
| --- | ---: |
| Accuracy | 0.997961 |
| Balanced accuracy | 0.997476 |
| Precision `MALICIOUS` | 0.992068 |
| Recall `MALICIOUS` | 0.996716 |
| Especificidad `BENIGN` | 0.998237 |
| F1-score `MALICIOUS` | 0.994387 |
| F1-score macro | 0.996570 |
| FPR (tasa de falsos positivos) | 0.001763 |
| Average precision | 0.999417 |
| ROC-AUC | 0.999884 |

La matriz de confusión final fue:

| | Predicho `BENIGN` | Predicho `MALICIOUS` |
| --- | ---: | ---: |
| Real `BENIGN` | 225,299 | 398 |
| Real `MALICIOUS` | 164 | 49,777 |

El recall `MALICIOUS` de 0.996716 (≈0.9967) estima la detección de ataques conocidos de
CIC-IDS2017 en vectores de características retenidos. No mide generalización a sesiones,
archivos o días no vistos: los ocho archivos de origen aparecen en las tres particiones.
La evaluación leave-one-day-out de la sección 10.5 responde a esa pregunta de transferencia
entre días y no es directamente comparable con la prueba agrupada. La prueba registró 164
falsos negativos y 398 falsos positivos.

## 6. Importancia de características

Las características con mayor importancia en el modelo final fueron:

| Característica | Importancia aproximada |
| --- | ---: |
| `Init_Win_bytes_forward` | 0.078041 |
| `Max Packet Length` | 0.071506 |
| `Average Packet Size` | 0.060322 |
| `Min Packet Length` | 0.048852 |
| `Packet Length Std` | 0.043536 |
| `Packet Length Variance` | 0.042336 |
| `Init_Win_bytes_backward` | 0.039691 |
| `Subflow Fwd Bytes` | 0.032733 |
| `Avg Bwd Segment Size` | 0.032025 |
| `Fwd Packet Length Mean` | 0.031237 |

La importancia de características se utilizará como elemento interpretativo y no como criterio para eliminar variables en esta fase. Una selección reducida de características requeriría un experimento separado.

## 7. Artefactos generados

- `src/modelado/04_entrenar_random_forest.py`: procedimiento reproducible de modelado.
- `docs/resultados_modelado.json`: métricas, particiones, parámetros, selección e importancia de características.
- `data/processed/dataset_cicids2017_preparado_grupos.parquet`: procedencia y etiquetas originales para partición y desglose.
- `data/processed/modelos/random_forest_seleccionado.joblib`: modelo balanceado persistido.
- `src/modelado/04b_analisis_por_ataque.py`: recall por tipo de ataque sobre la misma prueba agrupada. Resultado: `docs/resultados_recall_por_ataque.json`.
- `src/modelado/04c_validacion_por_dia.py`: leave-one-day-out con ambas configuraciones. Ejecutado; resultados en `docs/resultados_validacion_por_dia.json` (sección 10.5).
- `src/modelado/04d_analisis_umbral.py`: análisis complementario de selección anidada del umbral. Resultado: `docs/resultados_umbral_por_dia.json`.
- `src/modelado/04e_validacion_multisemilla.py`: análisis complementario con cinco semillas. Resultado: `docs/resultados_multisemilla.json`.

El modelo persistido contiene el clasificador, el orden de las características, la columna objetivo, la clase positiva y la semilla utilizada. Su integración con el módulo de inferencia se describe en la fase 5.

## 8. Interpretación y limitaciones

La prueba agrupada obtiene recall alto para ataques conocidos del dataset. Sin embargo,
la evaluación leave-one-day-out complementaria muestra que transferir a un día no visto
es mucho más difícil. Los dos resultados contestan preguntas distintas y deben
presentarse juntos. Ninguno demuestra generalización a redes reales ni detección de
ataques zero-day.

En la prueba agrupada, SQL Injection tuvo recall 1/2; las métricas de Heartbleed (1
registro) e Infiltration (4) son demasiado pequeñas para considerarse estables. Bot
obtuvo recall 0.662. Además, 269 vectores idénticos aparecen con etiquetas originales
distintas, en 82,456 filas; como el modelo recibe las mismas características para esos
casos, existe ambigüedad de etiqueta que no puede resolverse solo mediante el clasificador.

La tasa de falsos positivos debe analizarse junto con el volumen real de tráfico antes de valorar una operación continua. Además, las métricas no demuestran detección de ataques zero-day ni sustituyen una validación con tráfico independiente del dataset.

## 9. Cierre de la fase

La prueba agrupada se reservó para la evaluación final y no intervino en la selección de
la configuración. Las tres particiones contienen los ataques originales cuando el
número de grupos permite representarlos. La evaluación leave-one-day-out se mantiene
como diagnóstico separado de transferencia entre escenarios.

La fase 4 queda cerrada porque:

1. Se entrenaron las dos configuraciones definidas.
2. La selección se realizó con validación, sin utilizar la prueba.
3. Se evaluó la configuración seleccionada con datos independientes.
4. Se generaron métricas, matriz de confusión e importancia de características.
5. Se persistió el modelo seleccionado para su integración posterior.

La integración, las pruebas funcionales y el despliegue local del prototipo se documentan en las fases 5, 6 y 7, respectivamente.

## 10. Análisis complementarios

Los análisis de esta sección caracterizan la transferencia entre días completos, una
tarea distinta de la partición principal agrupada por vector. Las secciones 10.2 y 10.3
son análisis complementarios previos con la configuración sin balanceo; la sección
10.5 contiene la ejecución leave-one-day-out más reciente. No cambian la selección del
modelo oficial agrupado.

### 10.1 Recall por tipo de ataque (prueba agrupada del modelo actual)

| Etiqueta original | Registros de prueba | Detectados | Recall |
| --- | ---: | ---: | ---: |
| Bot | 210 | 139 | 66.2 % |
| DDoS | 12,775 | 12,771 | 99.97 % |
| DoS GoldenEye | 994 | 993 | 99.9 % |
| DoS Hulk | 19,536 | 19,469 | 99.7 % |
| DoS Slowhttptest | 546 | 545 | 99.8 % |
| DoS slowloris | 413 | 412 | 99.8 % |
| FTP-Patator | 779 | 778 | 99.9 % |
| Heartbleed | 1 | 1 | 100 % |
| Infiltration | 4 | 3 | 75.0 % |
| PortScan | 13,969 | 13,967 | 99.99 % |
| SSH-Patator | 507 | 503 | 99.2 % |
| Web Attack – Brute Force | 142 | 132 | 93.0 % |
| Web Attack – Sql Injection | 2 | 1 | 50.0 % |
| Web Attack – XSS | 63 | 63 | 100 % |
| BENIGN (falsos positivos) | 225,697 | 398 | FPR 0.176 % |

Los resultados de las categorías con muy pocos registros de prueba (en especial
Heartbleed, Infiltration y SQL Injection) no son estimaciones estables.

### 10.2 Umbral de decisión (leave-one-day-out con selección anidada)

El umbral se eligió solo con predicciones fuera de bolsa sobre los días de entrenamiento, con FPR máximo de 0.1 %, y se evaluó en el día de prueba.

| Día de prueba | Umbral elegido | Recall (0.5) | Recall (elegido) | FPR (0.5) | FPR (elegido) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Martes | 0.620 | 0.0001 | 0.0001 | 0.00107 | 0.00037 |
| Miércoles | 0.369 | 0.0064 | 0.0137 | 0.00004 | 0.00013 |
| Jueves | 0.559 | 0.0068 | 0.0050 | 0.00279 | 0.00269 |
| Viernes | 0.520 | 0.2786 | 0.2781 | 0.00034 | 0.00032 |
| **Media ± desv.** | | 0.073 ± 0.137 | 0.074 ± 0.136 | 0.00106 | 0.00088 |

Este análisis es una comprobación complementaria sobre el modelo sin balanceo y con
prueba por día; no cambia el umbral 0.5 del modelo agrupado actual. La selección del
umbral no mejoró de forma consistente el recall entre días.

### 10.3 Variabilidad por semilla y orden de entrenamiento (configuración sin balanceo)

Se ejecutó leave-one-day-out con cinco semillas (42, 1, 2, 3 y 4). Cada semilla cambia el submuestreo estratificado del entrenamiento, el orden de las filas y el `random_state` del Random Forest. Se usó umbral 0.5.

| Día de prueba | Recall (media ± desv.) | Rango de recall | FPR (media) |
| --- | ---: | ---: | ---: |
| Martes | 0.0001 ± 0.0000 | 0.0001 – 0.0001 | 0.00159 |
| Miércoles | 0.0063 ± 0.0011 | 0.0050 – 0.0077 | 0.00005 |
| Jueves | 0.0191 ± 0.0168 | 0.0045 – 0.0469 | 0.00278 |
| Viernes | 0.2318 ± 0.0844 | 0.0849 – 0.2819 | 0.00037 |
| **Global** | **0.064 ± 0.107** | | **0.00119** |

Este resultado corresponde al protocolo por día y al modelo sin balanceo, no al modelo
agrupado actual. Ilustra la variabilidad al transferir a días no vistos; no debe
compararse directamente con la prueba estratificada que contiene ataques de todos los días.

Se verificó la causa de la variabilidad en este análisis leave-one-day-out anterior a la partición agrupada principal. Al dejar viernes fuera, el recall fue 0.278 con el orden de filas del Parquet y 0.076 con el orden de concatenación lunes-miércoles seguido de jueves. Un control con todas las filas de entrenamiento, sin submuestreo, dio 0.278; por tanto, el submuestreo no explica la diferencia. Estos resultados describen la sensibilidad del protocolo por día al orden de entrenamiento, no la partición agrupada principal.

### 10.4 Conclusión de los análisis complementarios

- La prueba agrupada estima la detección de ataques conocidos del dataset, sin separar vectores de características idénticos.
- La prueba por día mide una tarea distinta y muestra una transferencia débil a escenarios no vistos.
- El umbral no corrige por sí solo el cambio de distribución entre días.
- Ninguna de estas evaluaciones reemplaza una prueba externa con capturas independientes.

### 10.5 Validación con ambas configuraciones (leave-one-day-out, 04c)

| Día | Configuración | Recall | FPR | ROC-AUC | Average precision |
| --- | --- | ---: | ---: | ---: | ---: |
| Martes | sin balanceo | 0.0001 | 0.0011 | 0.7875 | 0.0857 |
| Martes | balanceado | 0.0001 | 0.0030 | 0.9007 | 0.1620 |
| Miércoles | sin balanceo | 0.0060 | 0.0000 | 0.8879 | 0.8598 |
| Miércoles | balanceado | 0.0088 | 0.0001 | 0.8836 | 0.8506 |
| Jueves | sin balanceo | 0.0068 | 0.0028 | 0.9091 | 0.0345 |
| Jueves | balanceado | 0.2013 | 0.0032 | 0.9618 | 0.2996 |
| Viernes | sin balanceo | 0.2781 | 0.0003 | 0.8399 | 0.8000 |
| Viernes | balanceado | 0.0789 | 0.0007 | 0.5840 | 0.6271 |
| Media ± desv. | sin balanceo | 0.0728 ± 0.1370 | 0.00105 ± 0.00123 | | |
| Media ± desv. | balanceado | 0.0723 ± 0.0929 | 0.00177 ± 0.00156 | | |

Esta evaluación por día no selecciona el modelo oficial. La configuración balanceada
mantiene recall bajo al probar días completos no vistos, sobre todo martes a jueves;
por tanto, el alto resultado de la partición agrupada se limita a los ataques y escenarios
representados en entrenamiento.

El resultado agrupado principal se documenta en las secciones 4–5 y no reemplaza esta
prueba de transferencia entre días.

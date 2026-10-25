# Fase 4. Desarrollo del modelo

## 1. Propósito de la fase

Esta fase corresponde al modelado de CRISP-DM. Su objetivo es entrenar y comparar dos configuraciones de Random Forest sobre el dataset preparado. Las configuraciones candidatas se comparan únicamente mediante validación; la prueba se reserva hasta después de seleccionar y reentrenar el modelo final.

Las decisiones adoptadas antes del entrenamiento fueron:

- Clasificador principal: Random Forest.
- Características: las 78 variables numéricas del dataset preparado.
- Variable positiva: `MALICIOUS`.
- División: separación fija por día de captura; lunes-martes-miércoles para entrenamiento, jueves para validación y viernes para prueba.
- Semilla: `random_state=42`.
- Configuraciones: sin balanceo y con `class_weight="balanced"`.
- Criterio de selección: mayor recall de `MALICIOUS` y, en caso de empate, menor FPR.
- Umbral numérico de aceptación: no se fijó antes del entrenamiento.

## 2. Procedimiento reproducible

El procedimiento se implementó en `src/modelado/04_entrenar_random_forest.py`.

1. Se carga el Parquet preparado y sus metadatos.
2. Se valida que las 78 características coincidan exactamente con el esquema registrado.
3. Se verifica que no existan valores faltantes, valores no finitos ni etiquetas desconocidas.
4. Se separan los días completos mediante la procedencia conservada en `dataset_cicids2017_preparado_grupos.parquet`.
5. Se entrena Random Forest sin balanceo.
6. Se entrena Random Forest con `class_weight="balanced"`.
7. Se comparan las configuraciones usando únicamente validación.
8. Se selecciona la configuración con mayor recall de tráfico malicioso y menor FPR en empate.
9. Se reentrena la configuración seleccionada con entrenamiento más validación.
10. Se evalúa el modelo seleccionado una sola vez sobre el conjunto de prueba.
11. Se persiste el modelo seleccionado y se guardan las métricas y la importancia de características.

## 3. Restricción de recursos

La partición por día contiene 1,666,481 registros de entrenamiento, 458,483 de validación y 702,713 de prueba. El entrenamiento no superó el límite operativo de 1,762,141 registros, por lo que no fue necesario submuestrear esta partición. La validación y la prueba conservan todos sus registros.

La configuración seleccionada se reentrenó con los 1,666,481 registros de entrenamiento más los 458,483 registros de validación, para un total de 2,124,964 registros. La prueba no se incorpora al reentrenamiento. El parámetro `max_samples=0.5` hace que cada árbol utilice una muestra de la mitad de las filas disponibles para ese ajuste. No se generaron datos sintéticos, no se aplicó SMOTE y no se modificaron los archivos originales ni el dataset preparado.

Los parámetros utilizados fueron:

| Parámetro | Valor |
| --- | ---: |
| Número de árboles | 50 |
| Profundidad máxima | 20 |
| Muestras por árbol | 0.5 del entrenamiento disponible |
| Hilos de ejecución | 4 |
| Semilla aleatoria | 42 |

## 4. Resultados de validación

| Configuración | Accuracy | Precision `MALICIOUS` | Recall `MALICIOUS` | F1 macro | FPR |
| --- | ---: | ---: | ---: | ---: | ---: |
| Sin balanceo | 0.994665 | 0.138365 | 0.019856 | 0.516026 | 0.000601 |
| `class_weight="balanced"` | 0.994176 | 0.058366 | 0.013538 | 0.509529 | 0.001061 |

La configuración sin balanceo fue seleccionada porque obtuvo el mayor recall en el conjunto de validación del jueves. El resultado también muestra que la generalización entre días completos es considerablemente más difícil que la división aleatoria por fila utilizada anteriormente.

## 5. Evaluación final sobre prueba

Después de seleccionar la configuración mediante validación, la configuración sin balanceo se reentrenó con entrenamiento más validación y se evaluó una sola vez sobre la partición de prueba reservada.

| Métrica | Resultado |
| --- | ---: |
| Accuracy | 0.620074 |
| Precision `MALICIOUS` | 0.993304 |
| Recall `MALICIOUS` | 0.076022 |
| Especificidad `BENIGN` | 0.999642 |
| F1-score `MALICIOUS` | 0.141235 |
| F1-score macro | 0.448658 |
| Tasa de falsos positivos | 0.000358 |
| Average precision | 0.693450 |
| ROC-AUC | 0.728977 |

La matriz de confusión final fue:

| | Predicho `BENIGN` | Predicho `MALICIOUS` |
| --- | ---: | ---: |
| Real `BENIGN` | 413,780 | 148 |
| Real `MALICIOUS` | 266,831 | 21,954 |

Esto significa que el modelo detectó 21,954 de 288,785 registros maliciosos del conjunto de prueba y clasificó erróneamente 148 registros benignos como maliciosos. La caída respecto a la evaluación aleatoria anterior evidencia que el modelo dependía en gran medida de patrones compartidos entre filas del mismo escenario.

## 6. Importancia de características

Las características con mayor importancia en el modelo final fueron:

| Característica | Importancia aproximada |
| --- | ---: |
| `Max Packet Length` | 0.088507 |
| `Packet Length Std` | 0.084965 |
| `Packet Length Variance` | 0.082682 |
| `Init_Win_bytes_forward` | 0.075073 |
| `Avg Bwd Segment Size` | 0.069318 |
| `Bwd Packet Length Max` | 0.053498 |
| `Idle Mean` | 0.036237 |
| `Bwd Packet Length Std` | 0.035572 |
| `Fwd IAT Max` | 0.026126 |
| `Fwd Header Length.1` | 0.023358 |

La importancia de características se utilizará como elemento interpretativo y no como criterio para eliminar variables en esta fase. Una selección reducida de características requeriría un experimento separado.

## 7. Artefactos generados

- `src/modelado/04_entrenar_random_forest.py`: procedimiento reproducible de modelado.
- `docs/resultados_modelado.json`: métricas, particiones, parámetros, selección e importancia de características.
- `data/processed/dataset_cicids2017_preparado_grupos.parquet`: procedencia utilizada para separar escenarios.
- `data/processed/modelos/random_forest_seleccionado.joblib`: modelo sin balanceo persistido.
- `src/modelado/04b_analisis_por_ataque.py`: análisis complementario de recall por tipo de ataque. Resultado: `docs/resultados_recall_por_ataque.json`.
- `src/modelado/04c_validacion_por_dia.py`: leave-one-day-out con ambas configuraciones. Ejecutado; resultados en `docs/resultados_validacion_por_dia.json` (sección 10.5).
- `src/modelado/04d_analisis_umbral.py`: análisis complementario de selección anidada del umbral. Resultado: `docs/resultados_umbral_por_dia.json`.
- `src/modelado/04e_validacion_multisemilla.py`: análisis complementario con cinco semillas. Resultado: `docs/resultados_multisemilla.json`.

El modelo persistido contiene el clasificador, el orden de las características, la columna objetivo, la clase positiva y la semilla utilizada. La integración con el módulo de inferencia se realizará en la fase 5.

## 8. Interpretación y limitaciones

Los resultados muestran que la separación por día reduce considerablemente el desempeño respecto a una división aleatoria por fila. Esto no debe ocultarse mediante la métrica de accuracy: el recall de `MALICIOUS` en la prueba fue 0.076022. El dataset fue generado en un entorno controlado y la evaluación no comparte días de captura entre particiones.

El resultado de prueba también depende del orden de las filas de entrenamiento y de la semilla. Con el mismo conjunto de datos, el recall del viernes varía entre 0.085 y 0.282 (sección 10.3). El valor 0.076022 de la sección 5 es una ejecución dentro de esa distribución y no debe presentarse como el desempeño representativo.

La tasa de falsos positivos debe analizarse junto con el volumen real de tráfico antes de valorar una operación continua. Además, las métricas no demuestran detección de ataques zero-day ni sustituyen una validación con tráfico independiente del dataset.

## 9. Cierre de la fase

La prueba se reservó para la evaluación final y no intervino en la selección de la configuración. La separación se realizó por días completos: entrenamiento con lunes, martes y miércoles; validación con jueves; y prueba con viernes. Por ello, estas métricas ofrecen una estimación más exigente de transferencia entre escenarios de CIC-IDS2017, pero no demuestran generalización a redes reales ni detección de ataques zero-day. La baja sensibilidad observada en la prueba debe considerarse un resultado de la evaluación, no ocultarse mediante la exactitud.

La fase 4 queda cerrada porque:

1. Se entrenaron las dos configuraciones definidas.
2. La selección se realizó con validación, sin utilizar la prueba.
3. Se evaluó la configuración seleccionada con datos independientes.
4. Se generaron métricas, matriz de confusión e importancia de características.
5. Se persistió el modelo seleccionado para su integración posterior.

La siguiente etapa será la **fase 5. Integración del prototipo**, donde se implementarán la carga del modelo, la validación de entradas, la inferencia por lotes y el registro de alertas.

## 10. Análisis complementarios

Los análisis de esta sección se ejecutaron después de cerrar la fase 4 para caracterizar la generalización del modelo. Usan la misma configuración sin balanceo y el mismo esquema de 78 características. Ninguno cambia el modelo oficial ni la selección de la fase 4.

### 10.1 Recall por tipo de ataque (prueba: viernes, modelo oficial)

| Etiqueta original | Registros | Clasificados como `MALICIOUS` | Tasa |
| --- | ---: | ---: | ---: |
| Bot | 1,956 | 0 | 0.0 % |
| DDoS | 128,025 | 21,876 | 17.1 % |
| PortScan | 158,804 | 78 | 0.05 % |
| BENIGN (falsos positivos) | 413,928 | 148 | 0.036 % |

### 10.2 Umbral de decisión (leave-one-day-out con selección anidada)

El umbral se eligió solo con predicciones fuera de bolsa sobre los días de entrenamiento, con FPR máximo de 0.1 %, y se evaluó en el día de prueba.

| Día de prueba | Umbral elegido | Recall (0.5) | Recall (elegido) | FPR (0.5) | FPR (elegido) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Martes | 0.620 | 0.0001 | 0.0001 | 0.00107 | 0.00037 |
| Miércoles | 0.369 | 0.0064 | 0.0137 | 0.00004 | 0.00013 |
| Jueves | 0.559 | 0.0068 | 0.0050 | 0.00279 | 0.00269 |
| Viernes | 0.520 | 0.2786 | 0.2781 | 0.00034 | 0.00032 |
| **Media ± desv.** | | 0.073 ± 0.137 | 0.074 ± 0.136 | 0.00106 | 0.00088 |

La selección del umbral no mejora de forma consistente el recall. Los umbrales elegidos varían entre 0.37 y 0.62, por lo que no se puede fijar un umbral que funcione entre días. Se mantiene el umbral de 0.5 como referencia oficial.

### 10.3 Variabilidad por semilla y orden de entrenamiento

Se ejecutó leave-one-day-out con cinco semillas (42, 1, 2, 3 y 4). Cada semilla cambia el submuestreo estratificado del entrenamiento, el orden de las filas y el `random_state` del Random Forest. Se usó umbral 0.5.

| Día de prueba | Recall (media ± desv.) | Rango de recall | FPR (media) |
| --- | ---: | ---: | ---: |
| Martes | 0.0001 ± 0.0000 | 0.0001 – 0.0001 | 0.00159 |
| Miércoles | 0.0063 ± 0.0011 | 0.0050 – 0.0077 | 0.00005 |
| Jueves | 0.0191 ± 0.0168 | 0.0045 – 0.0469 | 0.00278 |
| Viernes | 0.2318 ± 0.0844 | 0.0849 – 0.2819 | 0.00037 |
| **Global** | **0.064 ± 0.107** | | **0.00119** |

El recall es muy variable entre días y semillas, mientras que el FPR es estable. Esta es la estimación de generalización que debe presentarse como resultado principal.

Se verificó la causa de la variabilidad. Con los mismos datos, el viernes obtuvo recall 0.278 con el orden de filas del Parquet y 0.076 con el orden de concatenación usado en la fase 4 (lunes-martes-miércoles seguido de jueves). Un control con todas las filas de entrenamiento, sin submuestreo, dio 0.278; por tanto, el submuestreo no explica la diferencia.

### 10.4 Conclusión de los análisis complementarios

- La baja sensibilidad ante tipos de ataque no vistos en el entrenamiento es el hallazgo principal.
- Ajustar el umbral no compensa esa limitación.
- El valor oficial de 0.076 debe interpretarse dentro de la distribución de 10.3.
- Una evaluación definitiva requiere reportar media y desviación sobre varias semillas, y evitar elegir el modelo o el umbral con el conjunto de prueba.

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

La configuración balanceada no mejora el recall medio frente a la configuración sin balanceo y aumenta el FPR de 0.00105 a 0.00177. Su mejor resultado, en jueves (recall 0.2013), no se repite en viernes (recall 0.0789, ROC-AUC 0.584). La configuración sin balanceo se mantiene como la elegida: igual recall y menor FPR.

Los valores de miércoles y viernes difieren ligeramente de los de la sección 10.2 (0.0060 frente a 0.0064, y 0.2781 frente a 0.2786). La causa no se identificó y no altera las conclusiones.

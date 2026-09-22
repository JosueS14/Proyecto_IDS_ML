# Fase 4. Desarrollo del modelo

## 1. Propósito de la fase

Esta fase corresponde al modelado de CRISP-DM. Su objetivo es entrenar y comparar dos configuraciones de Random Forest sobre el dataset preparado, sin utilizar el conjunto de prueba para seleccionar la configuración final.

Las decisiones adoptadas antes del entrenamiento fueron:

- Clasificador principal: Random Forest.
- Características: las 78 variables numéricas del dataset preparado.
- Variable positiva: `MALICIOUS`.
- División: estratificada 80 % entrenamiento, 10 % validación y 10 % prueba.
- Semilla: `random_state=42`.
- Configuraciones: sin balanceo y con `class_weight="balanced"`.
- Criterio de selección: mayor recall de `MALICIOUS` y, en caso de empate, menor FPR.
- Umbral numérico de aceptación: no se fijó antes del entrenamiento.

## 2. Procedimiento reproducible

El procedimiento se implementó en `src/modelado/04_entrenar_random_forest.py`.

1. Se carga el Parquet preparado y sus metadatos.
2. Se valida que las 78 características coincidan exactamente con el esquema registrado.
3. Se verifica que no existan valores faltantes, valores no finitos ni etiquetas desconocidas.
4. Se realiza una división estratificada 80/10/10.
5. Se entrena Random Forest sin balanceo.
6. Se entrena Random Forest con `class_weight="balanced"`.
7. Se comparan las configuraciones usando únicamente validación.
8. Se selecciona la configuración con mayor recall de tráfico malicioso y menor FPR en empate.
9. Se reentrena la configuración seleccionada con entrenamiento más validación.
10. Se evalúa el modelo seleccionado una sola vez sobre el conjunto de prueba.
11. Se persiste el modelo seleccionado y se guardan las métricas y la importancia de características.

## 3. Restricción de recursos

El dataset de entrenamiento contiene 2,262,141 registros. Un entrenamiento completo con 100 árboles excedió el tiempo disponible del entorno de laboratorio. Para obtener una ejecución reproducible y viable se aplicó una muestra estratificada de 500,000 registros únicamente al conjunto de entrenamiento.

La validación y la prueba conservaron todos sus registros. No se generaron datos sintéticos, no se aplicó SMOTE y no se modificaron los archivos originales ni el dataset preparado.

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
| Sin balanceo | 0.998433 | 0.996279 | 0.995760 | 0.997522 | 0.000911 |
| `class_weight="balanced"` | 0.998614 | 0.994541 | 0.998437 | 0.997811 | 0.001343 |

La configuración balanceada fue seleccionada porque detectó una mayor proporción de tráfico malicioso. El incremento del FPR fue pequeño en términos absolutos y se consideró aceptable frente a la mejora del recall, de acuerdo con el criterio definido previamente.

## 5. Evaluación final sobre prueba

Después de seleccionar la configuración mediante validación, el modelo balanceado se reentrenó con entrenamiento más validación y se evaluó sobre la prueba independiente.

| Métrica | Resultado |
| --- | ---: |
| Accuracy | 0.998532 |
| Precision `MALICIOUS` | 0.994451 |
| Recall `MALICIOUS` | 0.998113 |
| Especificidad `BENIGN` | 0.998635 |
| F1-score `MALICIOUS` | 0.996279 |
| F1-score macro | 0.997682 |
| Tasa de falsos positivos | 0.001365 |
| Average precision | 0.999633 |
| ROC-AUC | 0.999898 |

La matriz de confusión final fue:

| | Predicho `BENIGN` | Predicho `MALICIOUS` |
| --- | ---: | ---: |
| Real `BENIGN` | 226,802 | 310 |
| Real `MALICIOUS` | 105 | 55,551 |

Esto significa que el modelo detectó 55,551 de 55,656 registros maliciosos del conjunto de prueba y clasificó erróneamente 310 registros benignos como maliciosos.

## 6. Importancia de características

Las características con mayor importancia en el modelo final fueron:

| Característica | Importancia aproximada |
| --- | ---: |
| `Init_Win_bytes_forward` | 0.078422 |
| `Max Packet Length` | 0.075912 |
| `Average Packet Size` | 0.057432 |
| `Packet Length Std` | 0.054197 |
| `Init_Win_bytes_backward` | 0.050190 |
| `Min Packet Length` | 0.048004 |
| `Fwd Packet Length Mean` | 0.037952 |
| `Bwd Packet Length Max` | 0.031745 |
| `Bwd Packet Length Std` | 0.028531 |
| `Fwd Header Length` | 0.028142 |

La importancia de características se utilizará como elemento interpretativo y no como criterio para eliminar variables en esta fase. Una selección reducida de características requeriría un experimento separado.

## 7. Artefactos generados

- `src/modelado/04_entrenar_random_forest.py`: procedimiento reproducible de modelado.
- `docs/resultados_modelado.json`: métricas, particiones, parámetros, selección e importancia de características.
- `data/processed/modelos/random_forest_seleccionado.joblib`: modelo balanceado persistido.

El modelo persistido contiene el clasificador, el orden de las características, la columna objetivo, la clase positiva y la semilla utilizada. La integración con el módulo de inferencia se realizará en la fase 5.

## 8. Interpretación y limitaciones

Los resultados muestran un desempeño elevado sobre CIC-IDS2017, pero no deben interpretarse como garantía de funcionamiento en redes reales. El dataset fue generado en un entorno controlado y la evaluación utiliza una muestra de entrenamiento limitada por recursos.

La tasa de falsos positivos debe analizarse junto con el volumen real de tráfico antes de valorar una operación continua. Además, las métricas no demuestran detección de ataques zero-day ni sustituyen una validación con tráfico independiente del dataset.

## 9. Cierre de la fase

La fase 4 queda cerrada porque:

1. Se entrenaron las dos configuraciones definidas.
2. La selección se realizó con validación, sin utilizar la prueba.
3. Se evaluó la configuración seleccionada con datos independientes.
4. Se generaron métricas, matriz de confusión e importancia de características.
5. Se persistió el modelo seleccionado para su integración posterior.

La siguiente etapa será la **fase 5. Integración del prototipo**, donde se implementarán la carga del modelo, la validación de entradas, la inferencia por lotes y el registro de alertas.

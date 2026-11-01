# Resumen

La presente investigación desarrolla y evalúa un prototipo experimental de sistema de detección de intrusiones en red basado en aprendizaje automático supervisado. El prototipo utiliza características estadísticas de flujos del conjunto CIC-IDS2017 y clasifica cada registro como `BENIGN` o `MALICIOUS` mediante Random Forest. El sistema funciona por lotes, recibe archivos CSV o Parquet, valida las 78 características utilizadas por el modelo y genera alertas informativas sin bloquear conexiones ni operar como un sistema de prevención de intrusiones.

Durante la comprensión y preparación de los datos se analizaron ocho archivos del conjunto CIC-IDS2017. Se identificaron 3,119,345 filas brutas y 2,830,743 registros con etiqueta válida, de los cuales 2,273,097 correspondían a tráfico benigno y 557,646 a tráfico asociado con ataques. Después de eliminar filas vacías, registros con características no utilizables y duplicados exactos, se obtuvieron 2,827,677 registros y 78 características numéricas. Las columnas identificadoras, direcciones IP, puertos y marca temporal se excluyeron para reducir la dependencia del escenario de captura.

Se compararon dos configuraciones de Random Forest: una sin ponderación de clases y otra con `class_weight="balanced"`. La configuración balanceada fue seleccionada mediante la balanced accuracy de validación, con recall de `MALICIOUS` y tasa de falsos positivos como criterios secundarios. En la prueba agrupada por vectores de características, obtuvo una accuracy de 0.997961, balanced accuracy de 0.997476, precision de 0.992068, recall de 0.996716, especificidad de 0.998237, F1-score de `MALICIOUS` de 0.994387 y FPR de 0.001763. También alcanzó un Average Precision de 0.999417 y un ROC-AUC de 0.999884.

Estos resultados representan la detección de ataques conocidos dentro de CIC-IDS2017 bajo una partición que evita que vectores de características exactamente idénticos crucen entre conjuntos, pero que no separa completamente días, archivos o sesiones de captura. La validación leave-one-day-out mostró una transferencia considerablemente más débil a días no vistos: el recall medio fue de 0.0728 para la configuración sin balanceo y de 0.0723 para la configuración balanceada. Por tanto, los resultados no demuestran generalización a redes reales, detección de ataques zero-day ni superioridad frente a otros IDS. Las pruebas funcionales confirmaron la carga del modelo, la validación de entradas, la clasificación y la generación de alertas; la batería principal obtuvo 9 de 9 pruebas satisfactorias.

**Palabras clave:** sistemas de detección de intrusiones, aprendizaje automático, Random Forest, CIC-IDS2017, clasificación binaria, tráfico de red.

# Conclusiones

1. Se cumplió el objetivo de implementar un prototipo experimental de IDS por lotes capaz de clasificar registros de flujo como `BENIGN` o `MALICIOUS`. La solución integra un modelo persistido de Random Forest, validación del esquema de entrada, manejo de registros inválidos y generación de alertas informativas.

2. La preparación de los datos permitió construir un conjunto reproducible de 2,827,677 registros y 78 características numéricas. La eliminación de filas vacías, valores no utilizables y duplicados exactos evitó que problemas conocidos de calidad ingresaran al entrenamiento. La exclusión de identificadores, direcciones, puertos y marcas temporales redujo la dependencia directa de elementos específicos del escenario CIC-IDS2017.

3. La configuración `class_weight="balanced"` fue seleccionada porque obtuvo una balanced accuracy de validación de 0.998003, superior a 0.997365 de la configuración sin balanceo. En la prueba agrupada, el modelo alcanzó un recall de 0.996716 para `MALICIOUS`, con 49,777 verdaderos positivos, 164 falsos negativos, 225,299 verdaderos negativos y 398 falsos positivos.

4. El resultado agrupado debe interpretarse con cautela. Aunque los vectores idénticos se mantuvieron dentro de una sola partición, los ocho archivos de origen aparecen en entrenamiento, validación y prueba. En consecuencia, esta evaluación mide principalmente la detección de patrones de ataque representados en el conjunto y no la transferencia hacia capturas o sesiones completamente nuevas.

5. La validación por días completos confirmó esta limitación. El recall medio fue de 0.0728 sin balanceo y de 0.0723 con balanceo, con tasas medias de falsos positivos de 0.00105 y 0.00177, respectivamente. La diferencia frente al recall de la prueba agrupada indica un cambio importante de distribución entre escenarios y demuestra que las métricas agrupadas no deben presentarse como evidencia de desempeño operativo en redes reales.

6. El análisis por tipo de ataque mostró un desempeño desigual. DDoS y PortScan tuvieron recalls cercanos a 1, mientras que Bot alcanzó 0.662 y Web Attack – Sql Injection 0.50. Heartbleed, Infiltration y SQL Injection tienen muy pocos registros en la prueba, por lo que sus porcentajes no son estimaciones estables.

7. La integración funcional fue satisfactoria: las nueve pruebas principales finalizaron correctamente y la prueba offline de extremo a extremo generó las predicciones y alertas esperadas en un entorno controlado. Esta comprobación valida el flujo de software, pero no constituye una evaluación independiente del desempeño porque utiliza muestras derivadas del mismo conjunto CIC-IDS2017.

8. El prototipo no captura paquetes en tiempo real, no extrae características directamente desde interfaces de red, no bloquea conexiones y no detecta de manera garantizada ataques zero-day. Asimismo, las probabilidades producidas por Random Forest no están calibradas y no deben interpretarse como niveles de confianza probabilística.

9. Como trabajo futuro se recomienda evaluar particiones por día, sesión o captura independiente; validar el modelo con tráfico externo; estudiar técnicas para las clases minoritarias; calibrar las probabilidades; desarrollar un flujo de procesamiento completo para archivos grandes; y comparar el modelo con clasificadores y sistemas IDS de referencia bajo un protocolo común.

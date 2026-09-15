# Fase 1. Planificación y requisitos

## 1. Propósito de la fase

Esta fase corresponde a la comprensión del negocio de CRISP-DM y a la definición del alcance y los requisitos de seguridad de SecSDLC. NIST SP 800-94 se utiliza como referencia técnica para establecer las capacidades esperadas de un sistema de detección de intrusiones en red (NIDS).

El resultado de esta fase es una especificación inicial, verificable y suficiente para orientar la comprensión de los datos, la preparación, el modelado y la construcción del prototipo. Las decisiones sobre columnas concretas, tratamiento del desbalance, hiperparámetros y umbrales se tomarán en fases posteriores a partir de evidencia experimental.

## 2. Problema que se pretende resolver

Los mecanismos basados exclusivamente en firmas dependen de patrones previamente conocidos y pueden tener dificultades para identificar variantes modificadas o comportamientos no registrados. El proyecto propone estudiar la viabilidad de un IDS basado en aprendizaje automático supervisado que analice características estadísticas de flujos de red y clasifique cada flujo como benigno o malicioso.

El problema se formula de la siguiente manera:

> Dado un flujo de red representado por sus características, determinar si pertenece a tráfico benigno o a tráfico asociado con una actividad maliciosa, procurando detectar la mayor cantidad posible de ataques sin producir un número excesivo de falsas alertas.

La solución será experimental y académica. No sustituirá un IDS comercial, no ejecutará acciones de bloqueo y no se considerará evidencia suficiente para operar sobre una red de producción.

## 3. Objetivo del proyecto

### 3.1 Objetivo general

Implementar y evaluar un prototipo de sistema de detección de intrusiones en red basado en aprendizaje automático supervisado, utilizando características de flujos del conjunto CIC-IDS2017 para clasificar el tráfico como `BENIGN` o `MALICIOUS`.

### 3.2 Objetivos específicos

1. Establecer una base teórica y metodológica sobre IDS, aprendizaje automático y análisis de tráfico de red.
2. Identificar y justificar las características que podrán utilizarse para diferenciar el tráfico benigno del malicioso.
3. Preparar un conjunto reproducible de datos para clasificación binaria.
4. Entrenar y evaluar Random Forest como algoritmo principal y comparar, si los recursos lo permiten, al menos un modelo de referencia.
5. Integrar el modelo seleccionado en un prototipo que funcione inicialmente en modo por lotes.
6. Medir el desempeño mediante exactitud, precisión, sensibilidad, especificidad, F1-score, matriz de confusión, tasa de falsos positivos y, cuando sea pertinente, área bajo la curva precision-recall.
7. Documentar la instalación, ejecución, limitaciones y condiciones de actualización del prototipo.

## 4. Alcance inicial

### 4.1 Incluido

- Dataset principal: CIC-IDS2017 en formato CSV de flujos generado por CICFlowMeter.
- Tipo de sistema: NIDS experimental basado en características de flujo.
- Tipo de aprendizaje: supervisado.
- Tarea principal: clasificación binaria.
- Clases de salida: `BENIGN` y `MALICIOUS`.
- Algoritmo principal: Random Forest.
- Modo inicial de operación: procesamiento por lotes mediante archivos preparados.
- Entrada prevista: registros tabulares con las características esperadas por el modelo.
- Salida prevista: clase predicha, confianza o probabilidad cuando esté disponible y registro de eventos maliciosos.
- Evaluación: conjunto de prueba independiente y métricas definidas en este documento.
- Entorno de ejecución: laboratorio controlado y aislado.

### 4.2 Fuera del alcance de la primera versión

- Bloqueo, terminación o modificación activa de conexiones.
- Funcionamiento como IPS.
- Operación sobre redes de producción.
- Captura y clasificación directa en tiempo real.
- Extracción completa de características de flujo desde paquetes en línea.
- Clasificación multiclase de cada familia de ataque.
- Detección garantizada de ataques zero-day.
- Comparación concluyente contra productos IDS comerciales.

La captura en tiempo real, la clasificación multiclase y la respuesta activa quedan registradas como posibles extensiones, no como requisitos de aceptación de esta versión.

## 5. Decisiones de diseño iniciales

| ID | Decisión | Justificación |
| --- | --- | --- |
| D-001 | Usar clasificación binaria | Reduce la complejidad inicial y permite validar primero el flujo completo del IDS. |
| D-002 | Usar CIC-IDS2017 | Contiene flujos benignos y varias categorías de ataques generados en un entorno controlado. |
| D-003 | Usar Random Forest como modelo principal | Es adecuado para datos tabulares, maneja relaciones no lineales y permite estimar importancia de características. |
| D-004 | Trabajar inicialmente por lotes | Evita confundir la validación del modelo con los problemas adicionales de captura, agrupación de paquetes y latencia en tiempo real. |
| D-005 | Definir `MALICIOUS` como clase positiva | Hace explícita la interpretación de verdaderos positivos, falsos negativos y tasa de falsos positivos. |
| D-006 | Evaluar con datos no usados en entrenamiento | Reduce el riesgo de presentar una estimación optimista del desempeño. |
| D-007 | No aplicar balanceo en esta fase | La técnica de balanceo debe seleccionarse después de medir la distribución y el efecto de cada alternativa en la preparación de datos. |

## 6. Requisitos funcionales

Los requisitos se expresan con identificadores para facilitar la trazabilidad durante las fases posteriores.

| ID | Requisito | Criterio de verificación |
| --- | --- | --- |
| RF-01 | El sistema deberá recibir un archivo tabular de flujos en un formato documentado. | Se procesa un archivo válido y se rechaza uno que no cumpla el esquema. |
| RF-02 | El sistema deberá comprobar que las características de entrada coincidan con las esperadas por el modelo. | Se informa el nombre o cantidad de columnas faltantes, adicionales o incompatibles. |
| RF-03 | El sistema deberá aplicar las mismas transformaciones definidas durante el entrenamiento. | Una misma entrada produce el mismo vector transformado bajo la misma versión del artefacto. |
| RF-04 | El sistema deberá clasificar cada registro como `BENIGN` o `MALICIOUS`. | La salida solo contiene las dos clases definidas para la primera versión. |
| RF-05 | El sistema deberá cargar un modelo previamente entrenado sin volver a entrenarlo durante la inferencia. | La ejecución de inferencia utiliza un artefacto persistido. |
| RF-06 | El sistema deberá generar una alerta informativa para cada registro clasificado como `MALICIOUS`. | Las alertas pueden identificarse y contarse en la salida generada. |
| RF-07 | El sistema deberá registrar los resultados de clasificación. | Cada resultado incluye, como mínimo, fecha de análisis, clase predicha y confianza o probabilidad si está disponible. |
| RF-08 | El proceso de entrenamiento deberá separar los datos de entrenamiento, validación y prueba cuando el volumen y la estrategia elegida lo permitan. | El conjunto de prueba no participa en el ajuste de hiperparámetros. |
| RF-09 | El sistema deberá calcular las métricas de evaluación definidas. | Se generan valores para accuracy, precision, recall, especificidad, F1-score y FPR, además de la matriz de confusión. |
| RF-10 | El proceso deberá conservar la relación entre la etiqueta original y la etiqueta binaria. | Se documenta qué etiquetas originales se recodifican como `BENIGN` y cuáles como `MALICIOUS`. |

## 7. Requisitos técnicos y de calidad

| ID | Requisito | Criterio de verificación |
| --- | --- | --- |
| RT-01 | La implementación deberá utilizar Python. | El código y los experimentos se ejecutan en el entorno Python documentado. |
| RT-02 | El análisis de datos deberá utilizar Pandas y NumPy, y el modelado deberá utilizar scikit-learn. | Las dependencias aparecen en la configuración del proyecto y el flujo se ejecuta correctamente. |
| RT-03 | El modelo y las transformaciones deberán poder persistirse para su uso posterior. | Se genera y se vuelve a cargar un artefacto, preferentemente mediante joblib. |
| RT-04 | El proyecto deberá poder reproducir los experimentos principales. | Se documentan versiones, semilla aleatoria, archivos de entrada, partición y parámetros. |
| RT-05 | El procesamiento deberá manejar valores faltantes, infinitos, no numéricos y duplicados según reglas documentadas. | El informe de preparación registra el tratamiento y el número de registros afectados. |
| RT-06 | Las transformaciones ajustadas con datos deberán aprenderse únicamente a partir del conjunto de entrenamiento. | La validación y la prueba solo reciben transformaciones ya ajustadas. |
| RT-07 | El sistema deberá informar errores de entrada sin generar resultados silenciosamente incorrectos. | Se prueban archivos con columnas faltantes, tipos inválidos y etiquetas no reconocidas. |
| RT-08 | El desempeño deberá considerar el costo de los falsos positivos y falsos negativos. | El análisis no selecciona el modelo únicamente por accuracy. |
| RT-09 | El prototipo deberá funcionar con los recursos disponibles del entorno de laboratorio. | Se registra el tiempo de ejecución y, si es necesario, se documenta el muestreo o la reducción aplicada. |
| RT-10 | El formato, la cantidad final y el orden de las características deberán quedar documentados. | El artefacto incluye o referencia el esquema utilizado en entrenamiento. |

No se fija todavía un número definitivo de características. El repositorio contiene versiones de CIC-IDS2017 con 85 columnas iniciales y el script actual elimina algunas columnas identificadoras; el número final deberá confirmarse durante la comprensión y preparación de datos.

## 8. Requisitos de seguridad

| ID | Requisito | Criterio de verificación |
| --- | --- | --- |
| RS-01 | El entrenamiento y la evaluación deberán ejecutarse en un entorno controlado y aislado. | No se utilizan interfaces de producción ni se envían paquetes a terceros. |
| RS-02 | El prototipo deberá comportarse como IDS y no como IPS. | No bloquea, modifica ni termina conexiones. |
| RS-03 | Los archivos de datos originales deberán conservarse sin modificación. | El procesamiento escribe salidas separadas y el origen se trata como entrada de solo lectura. |
| RS-04 | Las entradas deberán validarse antes de la inferencia. | Se rechazan esquemas incompatibles y valores que impidan una clasificación confiable. |
| RS-05 | Los registros no deberán incluir cargas útiles ni secretos innecesarios. | Las alertas contienen metadatos de análisis y no almacenan payloads. |
| RS-06 | Las direcciones IP y otros identificadores potencialmente memorables no deberán utilizarse como características sin una justificación documentada. | La selección de variables registra su inclusión o exclusión y revisa el riesgo de fuga de información. |
| RS-07 | Las dependencias y artefactos deberán identificarse por versión. | La guía de ejecución permite reconstruir el entorno del proyecto. |
| RS-08 | El modelo persistido deberá tratarse como un artefacto de confianza. | Solo se cargan artefactos generados por el proceso del proyecto y almacenados en la ubicación documentada. |

## 9. Métricas y criterio de éxito

La clase positiva será `MALICIOUS`.

- **Accuracy:** proporción total de clasificaciones correctas.
- **Precision:** proporción de predicciones `MALICIOUS` que realmente son maliciosas.
- **Recall o sensibilidad:** proporción de ataques reales detectados.
- **Especificidad:** proporción de tráfico benigno identificado correctamente.
- **F1-score:** media armónica entre precision y recall.
- **Matriz de confusión:** valores de verdaderos positivos, verdaderos negativos, falsos positivos y falsos negativos.
- **Tasa de falsos positivos (FPR):** `FP / (FP + TN)`, es decir, tráfico benigno clasificado como malicioso.
- **Área bajo la curva precision-recall:** se utilizará cuando el desbalance haga útil analizar distintos umbrales.

El proyecto se considerará técnicamente satisfactorio si, como mínimo:

1. El flujo completo carga datos válidos, aplica las transformaciones y produce predicciones reproducibles.
2. Las dos clases definidas pueden evaluarse sobre datos no utilizados para entrenar o ajustar el modelo.
3. Se generan las métricas y la matriz de confusión sin depender únicamente de accuracy.
4. Las alertas de tráfico malicioso quedan registradas y son interpretables.
5. Se documentan los errores, limitaciones, distribución de clases y condiciones bajo las que se obtuvieron los resultados.

No se fija en esta fase un umbral numérico de accuracy, recall o FPR. Ese umbral debe establecerse después de conocer la distribución real de los datos, el costo relativo de cada error y los resultados de la evaluación. Presentar porcentajes tomados de otros estudios como si fueran objetivos garantizados sería metodológicamente incorrecto.

## 10. Estado actual del repositorio

### 10.1 Avances confirmados

- Existe una estructura inicial con `data/raw`, `data/processed`, `src/data`, `docs` y `thesis`.
- Se dispone de los ocho archivos CSV principales de CIC-IDS2017 en el entorno local.
- El script `src/data/01_cargar_dataset.py` carga varios CSV, normaliza nombres de columnas, elimina identificadores seleccionados, trata infinitos y valores nulos y genera un archivo Parquet.
- La bitácora registra una exploración inicial de columnas, tipos, etiquetas y distribución de clases.
- Se tomó la decisión de utilizar clasificación binaria y Random Forest como algoritmo principal.
- Se definió que el tratamiento del desbalance se analizará en la preparación de datos y no se asumirá de antemano.

### 10.2 Diferencias o pendientes detectados

- `thesis/01_Business_Understanding.md` solo contenía decisiones generales; no incluía requisitos verificables, alcance fuera de límites, seguridad ni criterios de aceptación. Esta versión corrige esa carencia.
- El script actual realiza limpieza y genera datos procesados, pero esas actividades pertenecen principalmente a las fases 2 y 3. Todavía no deben considerarse evidencia de que la preparación final esté aprobada.
- La bitácora reporta diferencias entre conteos de una sesión y otra. Antes de usar cifras definitivas deberá establecerse un procedimiento único y reproducible de conteo.
- La selección actual de columnas eliminadas debe revisarse porque quitar `Source Port` y `Destination Port` puede eliminar información útil para detectar ciertos ataques. La decisión final queda pendiente de la fase de comprensión y preparación de datos.
- El script no recodifica todavía la etiqueta original a `BENIGN` y `MALICIOUS`.
- Todavía no existe un módulo de entrenamiento, evaluación, inferencia ni generación de alertas.
- No existe aún un esquema formal de entrada/salida, un modelo persistido ni una guía de ejecución.
- `README.md` está vacío y deberá completarse durante la integración o el despliegue del prototipo.
- `requirements.txt` contiene el inventario del entorno, pero su formato y codificación deben verificarse antes de usarlo como archivo de instalación reproducible.

## 11. Riesgos, restricciones y supuestos

| ID | Tipo | Descripción | Tratamiento previsto |
| --- | --- | --- | --- |
| R-001 | Riesgo | El desbalance puede inflar la accuracy y ocultar ataques minoritarios. | Reportar métricas por clase, F1 macro cuando corresponda y matriz de confusión. |
| R-002 | Riesgo | Puede existir fuga de información por identificadores, marcas temporales o registros relacionados. | Analizar las columnas y documentar la estrategia de división antes de entrenar. |
| R-003 | Riesgo | El dataset experimental puede no representar una red real. | Limitar las conclusiones al entorno controlado y declarar la limitación. |
| R-004 | Riesgo | La extracción desde paquetes en tiempo real puede no reproducir las características de CICFlowMeter. | Mantener el modo por lotes como alcance inicial. |
| R-005 | Restricción | El volumen de datos puede superar la memoria o el tiempo disponibles. | Medir recursos y documentar cualquier muestreo o procesamiento por partes. |
| R-006 | Riesgo | Un modelo entrenado puede quedar obsoleto ante cambios en el tráfico. | Definir monitoreo y reentrenamiento en la fase 7. |
| R-007 | Supuesto | Los archivos de entrada contienen una columna `Label` y características numéricas compatibles. | Verificar el supuesto durante la fase 2. |

## 12. Entregables de la fase 1

1. Este documento de planificación y requisitos.
2. Alcance inicial y exclusiones explícitas.
3. Requisitos funcionales, técnicos y de seguridad identificados.
4. Métricas y criterio de aceptación definidos.
5. Registro de decisiones, riesgos, supuestos y pendientes.
6. Relación inicial entre el estado del repositorio y las actividades de las fases posteriores.

## 13. Criterio para cerrar la fase 1

La fase 1 queda cerrada para continuar con la fase 2 cuando se confirme que:

- el alcance binario y el modo por lotes son aceptados;
- `MALICIOUS` está definido como clase positiva;
- los requisitos RF, RT y RS son suficientes para diseñar las pruebas posteriores;
- se acepta que no habrá respuesta activa ni operación en producción en esta versión;
- las cifras descriptivas del dataset se tratarán como resultados de comprensión de datos y no como requisitos de negocio;
- las decisiones pendientes de columnas, balanceo, partición e hiperparámetros se trasladan explícitamente a las fases 2 y 3.

Con este cierre, la siguiente actividad será la **fase 2. Comprensión de los datos**, sin entrenar todavía el modelo ni construir el módulo de inferencia.

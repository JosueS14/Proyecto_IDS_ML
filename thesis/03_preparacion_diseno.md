# Fase 3. Preparación y diseño

## 1. Propósito de la fase

Esta fase integra la preparación de datos de CRISP-DM con el diseño inicial de la solución de SecSDLC. Su propósito es transformar los archivos originales en un conjunto reproducible y compatible con el modelado, además de definir el flujo lógico del prototipo IDS.

La preparación se ejecuta mediante `src/data/03_preparar_dataset.py`. El script procesa los CSV por bloques, no entrena modelos y conserva los archivos de `data/raw` sin modificaciones.

## 2. Decisiones de preparación

| ID | Decisión | Justificación |
| --- | --- | --- |
| P-001 | Normalizar los nombres de columnas y etiquetas recortando espacios | Evita que diferencias de formato impidan identificar variables y etiquetas. |
| P-002 | Eliminar filas completamente vacías | No representan flujos ni contienen una etiqueta utilizable. |
| P-003 | Convertir infinitos en valores faltantes y eliminar filas con características inválidas | Evita que valores no finitos entren al modelo sin una interpretación definida. |
| P-004 | Excluir `Flow ID`, IP origen/destino, puertos origen/destino y `Timestamp` | Reduce dependencia del escenario de captura y riesgo de fuga de información. |
| P-005 | Mantener las 78 características numéricas restantes inicialmente | Random Forest puede trabajar con variables tabulares y la reducción basada en evidencia se pospone. |
| P-006 | Recodificar `BENIGN` como `BENIGN` y cualquier otra etiqueta como `MALICIOUS` | Implementa el alcance binario definido en la fase 1. |
| P-007 | Eliminar duplicados exactos de la fila completa después de la conversión y recodificación, antes de excluir identificadores | Evita que la misma observación influya varias veces sin colapsar flujos distintos que solo comparten las características seleccionadas. |
| P-008 | No aplicar balanceo en esta fase | SMOTE, submuestreo u otra técnica debe evaluarse únicamente sobre el conjunto de entrenamiento. |
| P-009 | No aplicar escalado por ahora | Random Forest no requiere normalización; la decisión evita una transformación innecesaria. |

La exclusión de puertos es una decisión de generalización para la primera versión. Aunque pueden aportar señales de ataque, también pueden hacer que el modelo memorice los servicios específicos del escenario CIC-IDS2017. Su inclusión podrá evaluarse posteriormente como experimento controlado, sin cambiar silenciosamente el esquema principal.

## 3. Flujo de preparación

```text
CSV originales CIC-IDS2017
          |
          v
Lectura por bloques con codificación cp1252
          |
          v
Normalización de nombres y etiquetas
          |
          v
Eliminación de filas vacías
          |
          v
Conversión numérica e invalidación de infinitos
          |
          v
Eliminación de filas con valores no utilizables
          |
          v
Exclusión de identificadores y contexto no generalizable
          |
          v
Recodificación BENIGN/MALICIOUS y eliminación de duplicados
          |
          v
Dataset Parquet preparado + metadatos del esquema
```

El resultado principal es `data/processed/dataset_cicids2017_preparado.parquet`. El esquema y los contadores de filas se almacenan en `data/processed/dataset_cicids2017_preparado_metadatos.json`.

## 4. Esquema de salida

El dataset preparado contiene:

- 78 columnas de características numéricas.
- Una columna objetivo `Label`.
- Clases objetivo: `BENIGN` y `MALICIOUS`.
- Sin `Flow ID`, direcciones IP, puertos ni `Timestamp`.
- Orden de columnas registrado en el archivo de metadatos.

El modelo deberá utilizar exclusivamente la lista `feature_columns` del archivo de metadatos. No se deberá seleccionar automáticamente todo el DataFrame menos `Label`, porque el esquema podría cambiar si posteriormente se agregan columnas de auditoría.

## 5. Resultado de la ejecución

El pipeline se ejecutó sobre los ocho archivos del dataset y produjo los siguientes resultados:

| Concepto | Resultado |
| --- | ---: |
| Filas leídas | 3,119,345 |
| Filas completamente vacías eliminadas | 288,602 |
| Filas con características inválidas eliminadas | 2,867 |
| Duplicados exactos eliminados | 199 |
| Filas escritas | 2,827,677 |
| Características de salida | 78 |
| Columnas totales de salida | 79 |

La salida contiene 2,271,122 registros `BENIGN` y 556,555 registros `MALICIOUS`. La validación del Parquet confirmó que no quedan valores nulos ni valores no finitos en las características y que las etiquetas de salida son únicamente `BENIGN` y `MALICIOUS`.

## 6. Política de calidad

Las reglas implementadas son:

1. Leer los CSV sin modificar los archivos de origen.
2. Recortar espacios en nombres de columnas y etiquetas.
3. Remover filas completamente vacías.
4. Remover filas sin etiqueta válida.
5. Convertir las características a valores numéricos; las conversiones imposibles se consideran inválidas.
6. Convertir valores infinitos a faltantes.
7. Remover filas con alguna característica faltante o inválida.
8. Recodificar las etiquetas originales a las dos clases del proyecto.
9. Remover duplicados exactos de la fila completa mediante una huella de fila, incluyendo coincidencias entre bloques y archivos, antes de excluir los identificadores.

No se eliminan automáticamente valores negativos finitos como `Flow Duration = -1`. Estos valores requieren una regla de dominio que debe justificarse con mayor detalle; por tanto, quedan disponibles para análisis posterior y se registran como una limitación de la preparación actual.

## 7. Diseño lógico del prototipo

La primera versión se diseñará como un NIDS experimental por lotes con módulos separados:

```text
Archivo de flujos
       |
       v
Módulo de ingesta
       |
       v
Módulo de preparación y características
       |
       v
Modelo persistido de clasificación
       |
       v
Clasificación BENIGN/MALICIOUS
       |
       v
Registro de eventos y alertas
```

### 7.1 Módulo de ingesta

Recibe archivos con el esquema de flujo documentado. En la primera versión trabaja por lotes y no captura paquetes ni modifica conexiones.

### 7.2 Módulo de preparación y características

Aplica el mismo orden y selección de características definidos durante el entrenamiento. Deberá rechazar archivos con columnas faltantes, tipos incompatibles o un esquema diferente al registrado.

### 7.3 Módulo de inferencia

Se implementará en la fase 5. Cargará el modelo y los objetos auxiliares persistidos, recibirá el vector de 78 características y devolverá la clase predicha y la probabilidad cuando esté disponible.

### 7.4 Módulo de alertas y reportes

Se implementará en la fase 5. Registrará como mínimo la fecha de análisis, la clase predicha, la confianza o probabilidad y un identificador del registro. No almacenará cargas útiles ni ejecutará bloqueo activo.

## 8. Partición y prevención de fuga

La partición de entrenamiento, validación y prueba se realizará después de generar el dataset preparado. El conjunto de prueba deberá mantenerse separado de cualquier ajuste de hiperparámetros.

Como estrategia inicial se utilizará una partición estratificada y reproducible. Antes de fijarla definitivamente se analizará si existen flujos relacionados por tiempo, archivo o escenario que requieran una partición por grupos o por orden temporal. Las transformaciones que aprendan parámetros deberán ajustarse únicamente con entrenamiento.

El balanceo, se aplicará únicamente al conjunto de entrenamiento y no al conjunto de prueba.

## 9. Artefactos de esta fase

- `src/data/03_preparar_dataset.py`: pipeline reproducible de preparación.
- `data/processed/dataset_cicids2017_preparado.parquet`: salida local derivada, no versionada.
- `data/processed/dataset_cicids2017_preparado_metadatos.json`: esquema, decisiones y contadores de preparación.
- `thesis/03_preparacion_diseno.md`: descripción de las transformaciones y del diseño lógico.

## 10. Criterios de aceptación

La fase se considera técnicamente aceptable cuando:

1. El pipeline puede ejecutarse sobre los ocho CSV sin modificar los originales.
2. El resultado contiene únicamente las 78 características definidas y `Label`.
3. No quedan valores faltantes ni infinitos en las características de salida.
4. Las etiquetas de salida son exclusivamente `BENIGN` y `MALICIOUS`.
5. Los metadatos registran archivos de entrada, columnas excluidas, orden de características y filas eliminadas.
6. La eliminación de duplicados se aplica entre bloques y archivos, no solo dentro de un bloque aislado.
7. El esquema puede ser validado antes de usarlo en entrenamiento o inferencia.

La fase 3 no incluye todavía entrenamiento, ajuste de hiperparámetros, selección de modelo, evaluación estadística ni alertas operativas. Esas actividades se realizarán en las fases 4, 5 y 6.

## 11. Pendientes para la fase 4

- Medir el efecto de la preparación sobre cada clase.
- Definir la partición reproducible de entrenamiento, validación y prueba.
- Evaluar si el tratamiento del desbalance es necesario.
- Entrenar Random Forest y modelos de referencia.
- Comparar configuraciones sin utilizar el conjunto de prueba para el ajuste.

Con estos artefactos se cierra la **fase 3. Preparación y diseño**.

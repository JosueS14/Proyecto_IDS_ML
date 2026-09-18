# Fase 2. Comprensión de los datos

## 1. Propósito de la fase

Esta fase corresponde a la comprensión de los datos de CRISP-DM. Su objetivo es conocer la fuente, estructura, contenido, calidad y limitaciones del conjunto de datos antes de definir las transformaciones que se aplicarán en la fase 3.

El análisis se realizó sobre los ocho archivos CSV disponibles en `data/raw`. Para evitar alterar la fuente, se utilizó un análisis por bloques mediante `src/data/02_comprender_dataset.py`. El script únicamente describe los datos y genera el informe técnico `docs/data_understanding_results.json`; no limpia, balancea ni sobrescribe los CSV originales.

## 2. Fuente y organización de los datos

El conjunto utilizado es CIC-IDS2017, generado a partir de tráfico benigno y tráfico asociado con diferentes ataques en un entorno controlado. Cada fila representa un flujo de red y contiene características estadísticas calculadas a partir de los paquetes que forman dicho flujo.

Los archivos analizados son:

| Archivo | Filas brutas | Filas completamente vacías |
| --- | ---: | ---: |
| `Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv` | 225,745 | 0 |
| `Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv` | 286,467 | 0 |
| `Friday-WorkingHours-Morning.pcap_ISCX.csv` | 191,033 | 0 |
| `Monday-WorkingHours.pcap_ISCX.csv` | 529,918 | 0 |
| `Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv` | 288,602 | 0 |
| `Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv` | 458,968 | 288,602 |
| `Tuesday-WorkingHours.pcap_ISCX.csv` | 445,909 | 0 |
| `Wednesday-workingHours.pcap_ISCX.csv` | 692,703 | 0 |
| **Total** | **3,119,345** | **288,602** |

Los archivos presentan el mismo esquema después de retirar espacios al inicio y al final de los nombres de columna únicamente para efectos descriptivos. No se detectaron diferencias de esquema entre los ocho archivos.

## 3. Estructura del conjunto

Cada archivo contiene 85 columnas: 84 columnas de información del flujo y la columna objetivo `Label`. El esquema incluye:

- Identificadores y contexto del flujo: `Flow ID`, `Source IP`, `Source Port`, `Destination IP`, `Destination Port` y `Timestamp`.
- Protocolo y duración: `Protocol`, `Flow Duration`.
- Conteos y tamaños de paquetes hacia adelante y hacia atrás.
- Estadísticas de inter-arrival time (IAT).
- Banderas TCP.
- Tasas de paquetes y bytes.
- Estadísticas de paquetes, subflujos, ventanas TCP, actividad e inactividad.
- Etiqueta original: `Label`.

El detalle completo de las 85 columnas se encuentra en `docs/data_understanding_results.json`. En el primer archivo analizado se observaron 56 columnas `int64`, 24 columnas `float64` y 5 columnas de tipo `object`. Las columnas de tipo texto corresponden principalmente a identificadores, la marca temporal y la etiqueta.

## 4. Distribución de las etiquetas

El conjunto contiene 15 etiquetas originales: una etiqueta benigna y 14 categorías de ataque.

| Etiqueta | Registros |
| --- | ---: |
| `BENIGN` | 2,273,097 |
| `DDoS` | 128,027 |
| `PortScan` | 158,930 |
| `Bot` | 1,966 |
| `Infiltration` | 36 |
| `Web Attack – Brute Force` | 1,507 |
| `Web Attack – XSS` | 652 |
| `Web Attack – Sql Injection` | 21 |
| `FTP-Patator` | 7,938 |
| `SSH-Patator` | 5,897 |
| `DoS Hulk` | 231,073 |
| `DoS slowloris` | 5,796 |
| `DoS Slowhttptest` | 5,499 |
| `DoS GoldenEye` | 10,293 |
| `Heartbleed` | 11 |
| **Total con etiqueta válida** | **2,830,743** |

Para relacionar estos resultados con el alcance de la fase 1, las etiquetas originales de ataque representan la clase agregada `MALICIOUS`. La distribución binaria preliminar, calculada únicamente sobre los registros con etiqueta válida, es:

| Clase binaria | Registros | Porcentaje |
| --- | ---: | ---: |
| `BENIGN` | 2,273,097 | 80.30 % |
| `MALICIOUS` | 557,646 | 19.70 % |
| **Total** | **2,830,743** | **100.00 %** |

Esta distribución muestra un desbalance moderado en la clasificación binaria y un desbalance considerable entre las categorías de ataque. El tratamiento del desbalance no se decide en esta fase.

## 5. Calidad de los datos

### 5.1 Registros completamente vacíos

Se detectaron 288,602 filas completamente vacías en `Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv`. Estas filas no contienen características ni etiqueta y explican la diferencia entre las filas brutas y las filas con etiqueta válida.

Por ahora no se eliminan físicamente. La eliminación y su justificación se ejecutarán y medirán en la fase 3.

### 5.2 Valores faltantes

Todas las columnas presentan al menos 288,602 valores faltantes porque las filas completamente vacías afectan a todas las variables. Además, `Flow Bytes/s` presenta 1,358 valores faltantes adicionales en registros que no son completamente vacíos. En total, esta columna registra 289,960 valores faltantes.

La presencia de valores faltantes en `Flow Bytes/s` debe tratarse junto con los valores infinitos de la misma variable. Todavía no se decide si se eliminarán filas, se imputarán valores o se aplicará otra estrategia.

### 5.3 Valores infinitos

Se encontraron valores infinitos en dos variables:

| Variable | Valores infinitos |
| --- | ---: |
| `Flow Bytes/s` | 1,509 |
| `Flow Packets/s` | 2,867 |

Estos valores pueden aparecer cuando una tasa se calcula con una duración nula o inválida. Deben convertirse en valores faltantes o recibir otro tratamiento documentado durante la preparación.

### 5.4 Duplicados

La comparación mediante huella de fila detectó 288,803 duplicados dentro de los archivos, de los cuales 203 corresponden a filas no completamente vacías. La mayoría de las coincidencias está relacionada con las filas vacías repetidas del archivo de Web Attacks.

El conteo no incluye coincidencias entre archivos diferentes. En la fase 3 se deberá decidir si se eliminan duplicados exactos después de retirar las filas vacías y cómo se evita que la eliminación afecte de manera desproporcionada a una clase minoritaria.

### 5.5 Rangos y valores potencialmente inconsistentes

El informe técnico conserva los rangos observados de las variables numéricas. Algunos valores requieren revisión de dominio antes de entrenar:

| Variable | Mínimo observado | Máximo observado | Observación |
| --- | ---: | ---: | --- |
| `Flow Duration` | -1 | 119,999,937 | Una duración negativa requiere tratamiento. |
| `Flow Bytes/s` | -12,000,000 | 2,070,000,000 | Incluye valores negativos e infinitos. |
| `Flow Packets/s` | -2,000,000 | 3,000,000 | Incluye valores negativos e infinitos. |
| `Flow IAT Mean` | -1 | 107,000,000 | Debe revisarse el significado de los valores negativos. |
| `Source Port` | 0 | 65,534 | Rango compatible con puertos, sujeto a la estrategia de selección. |
| `Destination Port` | 0 | 65,532 | Rango compatible con puertos, sujeto a la estrategia de selección. |
| `Protocol` | 0 | 17 | Variable codificada numéricamente. |

La identificación de valores fuera de rango no implica todavía su eliminación. Las reglas se definirán en la fase de preparación con base en el significado de cada característica y en el efecto sobre el modelo.

## 6. Revisión de posibles fugas de información

Se identificaron seis columnas que pueden producir dependencia del escenario de captura o memorizar identidades específicas:

- `Flow ID`.
- `Source IP`.
- `Destination IP`.
- `Timestamp`.
- `Source Port`.
- `Destination Port`.

Las direcciones IP, el identificador de flujo y la marca temporal no se consideran características generalizables para la primera versión sin un análisis adicional. Los puertos pueden contener información útil para detectar ciertos ataques, pero también pueden inducir dependencia de servicios concretos del dataset. La decisión sobre conservar o excluir los puertos queda pendiente de la fase 3.

La columna `Label` es la variable objetivo y nunca deberá utilizarse como entrada del modelo. Tampoco se deberá ajustar ninguna transformación con información de la etiqueta de los conjuntos de validación o prueba.

## 7. Corrección de resultados previos

La bitácora de la sesión 4 registraba 3,036,743 flujos y una distribución de 74.86 % benigno frente a 25.14 % malicioso. El análisis reproducible de esta fase, ejecutado sobre los ocho archivos actuales y con exclusión explícita de las 288,602 filas completamente vacías, produce 2,830,743 registros con etiqueta válida y una distribución de 80.30 % frente a 19.70 %.

Por tanto, los resultados de esta fase sustituyen a esas cifras anteriores para efectos del proyecto. La diferencia queda registrada como una corrección de trazabilidad y no como una modificación del dataset original.

## 8. Artefactos generados

- `src/data/02_comprender_dataset.py`: analizador reproducible por bloques.
- `docs/data_understanding_results.json`: informe detallado del esquema, etiquetas, calidad, duplicados y rangos.
- `thesis/02_Data_Understanding.md`: interpretación metodológica de los resultados.

## 9. Conclusiones de la fase

1. El conjunto local contiene ocho archivos con un esquema común de 85 columnas.
2. Existen 3,119,345 filas brutas, de las cuales 288,602 están completamente vacías.
3. Después de excluir conceptualmente esas filas, quedan 2,830,743 registros con etiqueta válida.
4. La clasificación binaria tendrá 2,273,097 registros `BENIGN` y 557,646 registros `MALICIOUS` antes de cualquier balanceo.
5. Existen valores faltantes, infinitos, duplicados y valores potencialmente inconsistentes que deben tratarse en la fase 3.
6. Hay columnas identificadoras y contextuales que podrían producir fuga de información; no se fijó todavía la selección final de variables.
7. La fase 2 no entrena modelos ni modifica los archivos originales.

## 10. Pendientes para la fase 3

- Definir y ejecutar las reglas de limpieza de filas vacías, faltantes, infinitos y duplicados.
- Normalizar definitivamente nombres y etiquetas.
- Decidir la inclusión o exclusión de puertos y otras variables contextuales.
- Separar características y variable objetivo.
- Definir la estrategia de partición evitando fuga de información.
- Analizar el desbalance y seleccionar una estrategia que se aplique únicamente al conjunto de entrenamiento.
- Construir el vector de características documentando su cantidad y orden.

Con estos resultados se cierra la **fase 2. Comprensión de los datos**. La siguiente fase será **fase 3. Preparación y diseño**, donde comenzarán las transformaciones justificadas del conjunto.

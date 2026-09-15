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


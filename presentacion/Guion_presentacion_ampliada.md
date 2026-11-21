# Guion oral — presentación ampliada del proyecto IDS ML

**Presentación:** `IDS_ML_presentacion_ampliada.pptx`  
**Extensión:** 31 diapositivas  
**Duración sugerida:** 15–20 minutos, más el espacio de preguntas.


## 1. Sistema de detección de intrusiones basado en aprendizaje automático

Buenos días. Mi nombre es Josué Orlando Sánchez Azpeitia y hoy presentaré el proyecto **“Sistema de detección de intrusiones basado en aprendizaje automático para la detección de tráfico malicioso en redes”**. El trabajo desarrolla un prototipo que analiza flujos de red y los clasifica como benignos o maliciosos mediante un modelo Random Forest entrenado con CIC-IDS2017. Desde el inicio quiero subrayar que se trata de un prototipo experimental que procesa archivos por lotes; no captura tráfico en vivo ni bloquea conexiones.

## 2. ¿Qué veremos?

Primero explicaré el problema y los conceptos de detección de intrusiones. Después resumiré algunos trabajos relacionados y presentaré los datos y la metodología. A continuación revisaré cómo se entrenó y evaluó el modelo, incluida una evaluación por días que revela una limitación importante. Finalmente mostraré el prototipo, las pruebas realizadas y las conclusiones.

## 3. El reto: identificar actividad maliciosa entre millones de flujos

Una red puede generar muchísimos registros, y revisar cada uno manualmente no es práctico. El reto que abordo es distinguir los flujos benignos de los asociados con ataques, procurando no dejar pasar demasiados ataques y, al mismo tiempo, no producir una cantidad excesiva de falsas alarmas.

La pregunta experimental es si un modelo supervisado puede reconocer patrones de tráfico malicioso representados en CIC-IDS2017 y qué ocurre cuando cambia el escenario de captura. El alcance está limitado a las etiquetas conocidas de ese conjunto de datos: aquí no se prueba la detección de ataques *zero-day*.

## 4. Dos paradigmas de detección: firmas y anomalías

En la detección por firmas se compara el tráfico con patrones conocidos. Esto puede ser eficaz cuando existe una firma para la amenaza, pero depende de que esas firmas se mantengan actualizadas. La detección por anomalías, en cambio, busca comportamientos que se apartan de una referencia de normalidad; puede descubrir patrones atípicos, aunque también puede generar más falsas alarmas.

Este proyecto utiliza aprendizaje supervisado: el algoritmo aprende de ejemplos etiquetados como benignos o asociados con ataques. Por eso no equivale automáticamente a un detector de anomalías ni permite afirmar que reconocerá ataques nunca vistos.

## 5. Un IDS informa; un IPS interviene

Conviene distinguir un IDS de un IPS. Un IDS identifica actividad sospechosa y la comunica para que alguien la revise. Un IPS puede intervenir, por ejemplo, bloqueando o terminando una conexión.

El prototipo de este proyecto es únicamente un IDS experimental: analiza un archivo, produce predicciones y genera alertas informativas. No interactúa con conexiones de red y no debe entenderse como una herramienta de protección activa.

## 6. Objetivo y alcance experimental

El objetivo general fue implementar y evaluar un prototipo supervisado con dos clases de salida: `BENIGN` y `MALICIOUS`. Para lograrlo, preparé los datos, comparé dos configuraciones de Random Forest, medí sus resultados y conecté el modelo seleccionado con una interfaz de escritorio.

La prioridad de esta primera versión fue que el proceso fuera reproducible y que el flujo de análisis funcionara de principio a fin. Por eso se trabaja por lotes y no se incorporan captura en tiempo real, prevención activa ni clasificación de cada familia de ataque como una clase distinta.

## 7. Estado del arte (1/2)

En la primera parte del estado del arte se revisan tres trabajos. Maseer y colaboradores comparan varios algoritmos sobre CIC-IDS2017 y reportan resultados competitivos para Random Forest. Zhao y colaboradores proponen una arquitectura de aprendizaje profundo con técnicas de balanceo, y sus resultados varían entre las clases, especialmente en las minoritarias. Al Lail y colaboradores comparan varios clasificadores y dan importancia a métricas como F1 macro.

Estos estudios sirven como referencia para decisiones de diseño, pero sus cifras no deben leerse como una competencia directa con este proyecto. Cambian las particiones, las variables, el tratamiento de clases y las tareas evaluadas.

## 8. Estado del arte (2/2)

La segunda parte presenta el enfoque jerárquico de Verkerken y colaboradores y el Random Forest optimizado de Manurung y colaboradores. El primer trabajo distribuye la detección en etapas y estudia aspectos como eficiencia y ataques desconocidos. El segundo combina Random Forest con balanceo, selección de características y búsqueda de parámetros.

Son antecedentes útiles para identificar posibilidades futuras. Sin embargo, este proyecto no replica esos métodos: su modelo actual conserva 78 características y compara dos configuraciones de Random Forest sin SMOTE ni optimización exhaustiva.

## 9. Síntesis crítica: qué aporta la revisión

La revisión sugiere que Random Forest puede ser competitivo con datos tabulares, pero también que el resultado depende mucho de cómo se preparan y dividen los datos. En particular, las clases minoritarias pueden quedar ocultas detrás de una métrica global aparentemente alta.

Por eso, la contribución que propongo no es simplemente presentar un porcentaje elevado. Es integrar un prototipo reproducible y mostrar dos perspectivas de evaluación: una prueba agrupada por vectores de características y otra que deja días completos fuera. La diferencia entre ambas ayuda a entender los límites del resultado.

## 10. CIC-IDS2017: la base experimental

El conjunto CIC-IDS2017 contiene ocho archivos CSV con flujos benignos y flujos asociados con distintas familias de ataques. Cada fila describe características estadísticas del flujo, como tamaños de paquetes, tiempos entre paquetes, tasas y banderas de protocolo.

Después de la preparación quedaron **2.827.677 registros** y **78 características numéricas**. Las etiquetas originales incluyen tráfico benigno y 14 categorías de ataque; para este modelo las etiquetas de ataque se agruparon en una sola clase, `MALICIOUS`.

## 11. La distribución de clases importa

Entre los registros con etiqueta válida antes de preparar el conjunto, aproximadamente el 80,3 % era benigno y el 19,7 % correspondía a actividad maliciosa. Aunque el problema binario tiene una distribución relativamente manejable, las familias de ataques están mucho más desbalanceadas entre sí.

Por ejemplo, DDoS, DoS Hulk y PortScan tienen muchos registros, mientras que Heartbleed, Infiltration y SQL Injection tienen muy pocos. Por eso, además de medir el resultado global, revisé el *recall* por tipo de ataque y la matriz de confusión.

## 12. Antes de entrenar: depurar y reducir dependencias

La preparación eliminó **288.602 filas vacías**, **2.867 filas con características no utilizables** y **199 duplicados exactos**, sin modificar los CSV originales. Los infinitos se trataron como valores inválidos y se eliminaron las filas que tenían características faltantes o no finitas.

También se excluyeron del modelo Flow ID, direcciones IP, puertos y marca temporal. La idea fue reducir la dependencia de identidades o condiciones específicas de las capturas. El modelo conserva las características numéricas de flujo definidas en el esquema preparado.

## 13. Pipeline reproducible de preparación

El pipeline lee los ocho archivos por bloques, limpia los registros vacíos o inválidos, selecciona las 78 características, agrupa las etiquetas en `BENIGN` y `MALICIOUS`, y guarda el resultado en formato Parquet.

Junto con el conjunto se guardan metadatos del esquema y archivos auxiliares con información de procedencia. Esto permite verificar qué características recibe el modelo y conservar contexto para los análisis, sin usar esa procedencia como entrada del clasificador.

## 14. Ciclo de análisis y desarrollo

El trabajo se organizó siguiendo las fases analíticas de CRISP-DM: comprender el problema y los datos, preparar el conjunto, modelar y evaluar. Después se integró el modelo en el prototipo y se realizaron pruebas funcionales.

Una decisión importante fue reservar el conjunto de prueba para la evaluación final. Las configuraciones se compararon con los datos de validación; la prueba no se usó para elegir entre ellas.

## 15. ¿Por qué se seleccionó CRISP-DM?

CRISP-DM organiza el trabajo desde la comprensión del problema hasta la evaluación y el despliegue, y permite regresar a fases anteriores cuando los resultados lo requieren. También se consideraron KDD, SEMMA y TDSP, que tienen énfasis distintos en descubrimiento, análisis o trabajo de ciencia de datos.

Se eligió CRISP-DM porque cubre adecuadamente el ciclo analítico de este proyecto académico. Para el desarrollo del software se complementó con SecSDLC, que ayuda a estructurar requisitos, diseño, implementación, pruebas y mantenimiento.

## 16. Articulación metodológica

Cada referencia metodológica cumple una función diferente. CRISP-DM organiza el análisis de datos y la construcción del modelo; SecSDLC aporta estructura al desarrollo y validación del prototipo; y NIST SP 800-94 se utiliza como referencia técnica sobre sistemas de detección y prevención de intrusiones.

También se consideró PPDIOO, que está relacionado con el ciclo de vida de redes, pero no se tomó como metodología principal porque este trabajo no construye una infraestructura de red.

## 17. Random Forest para datos tabulares de flujo

Random Forest combina las decisiones de varios árboles. En este experimento se utilizaron 50 árboles, profundidad máxima de 20 y una muestra de la mitad de los registros disponibles para cada árbol. Se mantuvo la semilla 42 para hacer reproducible la ejecución.

Comparé una configuración sin ponderación de clases y otra con `class_weight="balanced"`. Esta ponderación modifica cuánto influye cada clase durante el ajuste; no crea registros sintéticos ni cambia las muestras de validación o prueba. La configuración balanceada fue seleccionada por su *balanced accuracy* en validación.

## 18. La configuración balanceada ganó por *balanced accuracy*

En validación, la configuración balanceada alcanzó una *balanced accuracy* de **99,8003 %**, frente a **99,7365 %** sin ponderación. También obtuvo un *recall* de `MALICIOUS` ligeramente mayor: **99,7342 %** frente a **99,5484 %**.

El intercambio es que la tasa de falsos positivos fue algo mayor: **0,1336 %** frente a **0,0754 %**. La selección priorizó la *balanced accuracy*, que considera el desempeño en ambas clases, y utilizó el *recall* y la tasa de falsos positivos como criterios secundarios.

## 19. Diseño de evaluación: dos preguntas distintas

La prueba principal agrupa los registros que tienen exactamente el mismo vector de 78 características y asigna cada grupo a una sola partición. Así se evita que una entrada idéntica aparezca a ambos lados de la partición. Sin embargo, los ocho archivos originales aparecen en entrenamiento, validación y prueba: no se están dejando sesiones o archivos completos fuera.

Como evaluación complementaria se realizó *leave-one-day-out*: se entrena sin un día y se prueba con ese día completo. Este protocolo responde a una pregunta más exigente sobre la transferencia entre días. Ambos análisis son internos a CIC-IDS2017 y ninguno sustituye una validación con tráfico externo.

## 20. Prueba agrupada: métricas altas para ataques conocidos

En la prueba agrupada, el modelo seleccionado obtuvo **99,80 % de accuracy**, **99,75 % de balanced accuracy** y **99,67 % de recall de `MALICIOUS`**. La tasa de falsos positivos fue de aproximadamente **0,18 %**.

La interpretación correcta es que el modelo reconoce bien patrones de ataques conocidos en vectores retenidos de este conjunto de datos. Debido a que las capturas están representadas en las distintas particiones, estas cifras no demuestran cómo funcionaría en días, sesiones o redes nuevas.

## 21. ¿Qué errores cometió el modelo?

La matriz de confusión resume 275.638 registros de prueba. De los registros benignos, **225.299** se clasificaron correctamente y **398** se marcaron como maliciosos: esos son los falsos positivos que podrían convertirse en falsas alertas.

De los registros maliciosos, **49.777** se detectaron y **164** se clasificaron como benignos: esos son los falsos negativos, es decir, ataques que el modelo no habría señalado. Esta distinción ayuda a entender por qué se reportan tanto el *recall* como la tasa de falsos positivos.

## 22. El desempeño depende de la familia de ataque

En la prueba agrupada, PortScan y DDoS alcanzaron un *recall* cercano al 100 %. En cambio, para Bot fue de aproximadamente **66,2 %**. Por tanto, una sola cifra global no describe completamente el comportamiento del modelo.

SQL Injection tuvo dos registros de prueba y se detectó uno; Infiltration tuvo cuatro y Heartbleed uno. Con muestras tan pequeñas, los porcentajes cambian mucho por cada registro y no deben interpretarse como estimaciones estables.

## 23. ¿Qué características influyen más?

Entre las variables con mayor importancia interna aparecen `Init_Win_bytes_forward`, `Max Packet Length`, `Average Packet Size`, `Min Packet Length` y `Packet Length Std`. En conjunto, varias de las variables destacadas describen tamaños y estadísticas de paquetes.

La importancia indica cuánto contribuye una variable a las decisiones de los árboles según el cálculo del modelo. No demuestra causalidad, ni significa que cada variable por sí sola identifique un ataque. Tampoco se utilizó esta lista para reducir las 78 características.

## 24. Al separar días completos, el *recall* cae con fuerza

Esta es la advertencia central de los resultados. En la evaluación por días completos, el *recall* medio fue aproximadamente **7,28 %** sin ponderación y **7,23 %** con ponderación balanceada, muy por debajo del resultado de la prueba agrupada.

Esto indica que el patrón de tráfico cambia entre los días de captura y que un modelo puede tener dificultades cuando se enfrenta a un escenario no representado de la misma manera durante el entrenamiento. Por eso el resultado agrupado no debe presentarse como garantía de desempeño operativo; hace falta evaluar con capturas independientes.

## 25. Del archivo a la alerta: arquitectura del prototipo

El flujo del prototipo empieza con un archivo CSV o Parquet. El motor comprueba que estén las 78 características requeridas, pasa los registros válidos al Random Forest persistido y obtiene una predicción y una probabilidad estimada.

Después, los resultados se muestran en la interfaz y se guardan en archivos CSV: uno con todos los resultados y otro con los registros predichos como `MALICIOUS`. La interfaz limita cada ejecución a las primeras 10.000 filas para mantener una vista manejable; los registros inválidos se identifican como errores de datos.

## 26. Una vista local para revisar flujos y alertas

La interfaz está construida con Tkinter. Permite abrir archivos, filtrar por clase o texto, revisar un resumen de conteos y seleccionar un flujo para consultar sus detalles. El color rojo indica una predicción maliciosa, el verde una benigna y el amarillo un registro con error de datos.

Su organización visual está inspirada en herramientas de análisis como Wireshark, pero no decodifica paquetes ni captura tráfico. Además, la probabilidad mostrada no fue calibrada, así que debe tratarse como una salida del clasificador y no como una confianza probabilística validada.

## 27. Validación funcional satisfactoria

La batería principal registró **nueve pruebas satisfactorias de nueve**. Se verificaron, entre otros puntos, la carga del modelo, el esquema de características, entradas CSV y Parquet, el rechazo de datos inválidos, la lógica de alertas y la inferencia de un lote de 1.000 filas. En esa ejecución, la inferencia tomó aproximadamente **0,044 segundos**, sin contar la carga inicial del modelo.

También se probó el flujo offline completo con 20 flujos derivados de CIC-IDS2017: se procesaron los 20, se generaron 10 alertas y no hubo errores de datos. Esa muestra comprueba que el flujo de software funciona; por su tamaño y origen no constituye una evaluación independiente del rendimiento predictivo.

## 28. Uso previsto y mantenimiento

El uso previsto es local en Windows: seleccionar un CSV o Parquet compatible, analizarlo, revisar predicciones y alertas y exportar los resultados. En una revisión de mantenimiento conviene observar cuántos registros fallan la validación, cómo cambian las predicciones, cuánto tarda el procesamiento y qué versión del modelo se está utilizando.

El modelo no se actualiza automáticamente. Para generar una nueva versión habría que preparar datos representativos, entrenar y validar sin utilizar la prueba para seleccionar el modelo, repetir las pruebas funcionales y conservar la versión anterior como respaldo. Este procedimiento está documentado, pero no implica que el prototipo esté desplegado en producción.

## 29. Qué puede afirmarse y qué sigue pendiente

Lo que sí puede afirmarse es que se implementó un prototipo local por lotes y que, en una partición agrupada interna a CIC-IDS2017, se obtuvo un *recall* alto para los ataques conocidos representados en el conjunto. También se encontró que el resultado cae fuertemente al evaluar días completos no vistos.

Los pasos futuros prioritarios son validar con capturas independientes, estudiar la robustez por sesión o captura, mejorar la cobertura de las clases minoritarias y revisar la calibración de probabilidades y los umbrales. Hasta contar con esa evidencia, no corresponde afirmar que el modelo está listo para una red productiva.

## 30. Referencias clave

En esta diapositiva aparecen los trabajos revisados y las referencias metodológicas y técnicas. No voy a leer la bibliografía completa; las referencias detalladas están en el documento de tesis. Las citas de los estudios comparativos deben entenderse dentro de sus respectivos protocolos, que no son idénticos al de este proyecto.

## 31. Conclusiones

Para cerrar, quiero destacar tres ideas. Primero, se implementó el flujo completo de un IDS experimental por lotes: preparación de datos, modelo, interfaz y generación de alertas. Segundo, la prueba agrupada mostró resultados altos al reconocer ataques conocidos dentro de CIC-IDS2017. Tercero, la evaluación por días completos reveló una transferencia débil y limita las conclusiones sobre generalización.

En síntesis, el proyecto cumple su propósito como prototipo y como experimento, y también deja claro qué evidencia falta antes de pensar en un uso operacional. Muchas gracias por su atención. Quedo atento a sus preguntas.

## Recordatorios para la exposición

- No presentar el **99,67 % de recall agrupado** como rendimiento en producción o en una red real.
- Al explicar la prueba agrupada, mencionar que no separa por día, sesión o archivo de captura.
- Contrastar ese valor con el **7,28 % / 7,23 % de recall medio** de la evaluación por días completos.
- Aclarar que las pruebas funcionales verifican el software, no la generalización del modelo.
- No llamar “probabilidad de confianza” al valor mostrado por la interfaz: no se calibró.

## Documentos del proyecto para consultar durante la preparación

- `thesis/00_resumen_conclusiones.md`
- `thesis/02_comprension_datos.md`
- `thesis/03_preparacion_diseno.md`
- `thesis/04_desarrollo_modelo.md`
- `thesis/05_integracion_prototipo.md`
- `thesis/06_pruebas_validacion.md`
- `thesis/07_despliegue_mantenimiento.md`
- `docs/resultados_modelado.json`
- `docs/resultados_validacion_por_dia.json``

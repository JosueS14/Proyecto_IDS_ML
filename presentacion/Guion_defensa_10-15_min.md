# Guion para la defensa (10–15 minutos; 21 diapositivas)

Presentación editable: `IDS_ML_defensa_10-15_min.pptx`.

Distribución sugerida: 8–10 minutos de exposición y 2–3 minutos para mostrar el prototipo.
La portada incluye los datos de identificación del PDF de tesis. Confirma que asesora, fecha y nombre de la licenciatura sean los definitivos.

## 1. Sistema de detección de intrusiones (IDS) basado en aprendizaje automático para la detección de tráfico malicioso en redes

Presento el desarrollo y la evaluación de un prototipo experimental de IDS basado en aprendizaje supervisado. La investigación utiliza CIC-IDS2017 y Random Forest para clasificar flujos como BENIGN o MALICIOUS.

## 2. Estructura de la exposición

La exposición cubre problema, estado del arte, metodología, datos, evaluación y sistema implementado. Reservaré aproximadamente dos minutos para mostrar el prototipo en funcionamiento.

## 3. Planteamiento del problema

El problema consiste en clasificar flujos de red como benignos o maliciosos. La investigación evalúa ataques etiquetados en CIC-IDS2017; no estudia la detección de ataques desconocidos ni afirma operación en redes reales.

## 4. Enfoques de detección y alcance del prototipo

La detección por firmas compara con ataques conocidos; la detección por anomalías busca desviaciones y puede producir falsas alarmas. El prototipo implementa clasificación supervisada con etiquetas existentes de CIC-IDS2017. Opera como IDS: informa y genera alertas, pero no bloquea tráfico ni funciona como IPS.

## 5. Objetivo de la investigación

Los objetivos son preparar los datos, comparar dos configuraciones de Random Forest, evaluar métricas complementarias e integrar la configuración elegida en una aplicación por lotes. La captura en tiempo real, el bloqueo de conexiones y la detección zero-day quedan fuera del alcance.

## 6. Comparación de investigaciones previas (1/2)

Maseer et al. reportan para Random Forest 99.54 % de accuracy y 99.55 % de F1 en su protocolo. Zhao et al. proponen TBGD y RUSK; los resultados mejoran algunas clases minoritarias, pero SQL Injection y Heartbleed siguen siendo difíciles. Al Lail et al. reportan cerca de 97 % de F1 macro para Random Forest. Las métricas no son comparables directamente.

## 7. Comparación de investigaciones previas (2/2)

Verkerken et al. combinan detección de anomalías y clasificación jerárquica; en la segunda etapa, Random Forest alcanzó 98.70 % de F1 ponderado. Manurung et al. combinan SMOTE, selección de características y optimización; reportan 98.14 % de accuracy y 96 % de F1 macro. Esas técnicas no se aplicaron en este proyecto.

## 8. Síntesis crítica y posicionamiento del proyecto

Los trabajos revisados respaldan la pertinencia de Random Forest y muestran los retos del desbalance. No corresponde comparar sus porcentajes directamente porque difieren en clases, características, balanceo y protocolos de prueba. La contribución de esta tesis es la integración reproducible del prototipo y el análisis explícito de la transferencia entre días; no se afirma superioridad frente a esos estudios.

## 9. CIC-IDS2017: conjunto y preparación

El conjunto contiene tráfico benigno y catorce familias de ataque. La preparación produjo 2,827,677 filas y 78 características. La distribución previa a la preparación fue aproximadamente 80.3 % BENIGN y 19.7 % MALICIOUS. Se eliminaron filas vacías, registros inválidos y duplicados; se excluyeron identificadores, IP, puertos y timestamp para reducir dependencia del escenario.

## 10. Metodología integrada

Se seleccionó CRISP-DM por cubrir el ciclo de análisis de datos de manera iterativa. KDD, SEMMA y TDSP se consideraron como alternativas. SecSDLC estructura requisitos, diseño, implementación, pruebas y mantenimiento; NIST SP 800-94 se utiliza como referencia técnica para IDPS, no como metodología de software.

## 11. Random Forest y selección de configuración

El modelo final utiliza 50 árboles, profundidad máxima 20, max_samples 0.5 y semilla 42 sobre 78 características. Se seleccionó la configuración balanceada por obtener mayor balanced accuracy en validación: 99.8003 % frente a 99.7365 %. Su recall de validación fue 99.7342 %, con FPR 0.1336 %. Las probabilidades no están calibradas.

## 12. Dos protocolos, dos preguntas de evaluación

La prueba agrupada asigna vectores idénticos a una sola partición, pero los ocho archivos están presentes en entrenamiento, validación y prueba. No aísla días ni sesiones. Leave-one-day-out deja días completos fuera para medir transferencia; ambos análisis permanecen dentro de CIC-IDS2017.

## 13. Resultados en la prueba agrupada

En la prueba agrupada, el recall de MALICIOUS fue 99.67 %, accuracy 99.80 %, balanced accuracy 99.75 % y FPR 0.176 %. Estas métricas no representan rendimiento en capturas o redes no vistas: los ocho archivos aparecen en las tres particiones.

## 14. Recall por familia de ataque

PortScan y DDoS superaron 99.9 % de recall en la prueba agrupada. Bot alcanzó 66.2 %. SQL Injection tuvo solo dos observaciones y su recall fue 50 %; Heartbleed e Infiltration tuvieron una y cuatro observaciones, respectivamente, por lo que sus estimaciones son inestables. La matriz de confusión registró 398 falsos positivos y 164 falsos negativos.

## 15. Transferencia a días completos no vistos

En leave-one-day-out, el recall medio fue 7.28 % sin balanceo y 7.23 % con balanceo, frente a 99.67 % en la prueba agrupada. Estas evaluaciones responden preguntas distintas. El cambio observado evidencia una limitación importante de transferencia y descarta presentar la métrica agrupada como desempeño operacional.

## 16. Arquitectura del prototipo por lotes

El flujo recibe un CSV o Parquet, valida el esquema de 78 características, ejecuta la inferencia de Random Forest y presenta los resultados en la interfaz. Los registros MALICIOUS se exportan como alertas. La vista de escritorio admite hasta diez mil filas.

## 17. Interfaz de análisis de flujos

La interfaz permite abrir archivos, analizar, filtrar y consultar detalles. Distingue visualmente MALICIOUS, BENIGN y ERROR_DATOS. Esta diapositiva es una representación esquemática; la demostración utilizará la aplicación implementada.

## 18. Demostración del prototipo

Mostrar la aplicación real. Abrir data/flujos_prueba_offline.csv, ejecutar el análisis, revisar predicciones y alertas, seleccionar un flujo y señalar los archivos de salida. El prototipo procesa archivos localmente; no captura ni bloquea tráfico. Si la interfaz no está disponible, utilizar la captura de pantalla incluida en la tesis.

## 19. Pruebas funcionales y limitaciones operativas

Las nueve pruebas principales aprobaron. La inferencia de mil filas tardó unos 0.044 segundos tras cargar el modelo. La prueba offline comprobó el flujo completo con muestras de CIC-IDS2017 y no constituye una validación independiente. El prototipo no captura tráfico en tiempo real, no bloquea conexiones y no ha sido probado con capturas externas.

## 20. Referencias principales

Las citas autor-año se muestran en los cuadros comparativos; la diapositiva reúne las referencias bibliográficas abreviadas. Las referencias completas se encuentran en la tesis.

## 21. Conclusiones

La investigación integró un IDS experimental por lotes con Random Forest. La prueba agrupada mostró recall alto para ataques conocidos, pero la evaluación por días completos evidenció transferencia débil. Se requiere validación con capturas independientes antes de considerar un uso operacional. Agradecer y abrir el espacio para preguntas.

## Fuentes principales

- Maseer, Z. K., et al. (2021). *Benchmarking of Machine Learning for Anomaly-Based Intrusion Detection Systems in the CIC-IDS2017 Dataset*. IEEE Access, 9, 22351–22370. https://doi.org/10.1109/ACCESS.2021.3056614
- Zhao, Y., Hu, Z., & Liu, R. (2023). *TBGD: Deep Learning Methods on Network Intrusion Detection Using CICIDS2017 Dataset*. Journal of Physics: Conference Series, 2670(1), 012025. https://doi.org/10.1088/1742-6596/2670/1/012025
- Al Lail, M., García, A. J., & Olivo, S. (2023). *Machine Learning for Network Intrusion Detection—A Comparative Study*. Future Internet, 15(7), 243. https://doi.org/10.3390/fi15070243
- Verkerken, M., et al. (2023). *A Novel Multi-Stage Approach for Hierarchical Intrusion Detection*. IEEE Transactions on Network and Service Management, 20(3), 3915–3929. https://doi.org/10.1109/TNSM.2023.3259474
- Manurung, J., Mardamsyah, A., & Sianipar, B. (2026). *Enhanced Cyber Attack Detection Using Optimized Random Forest with SMOTE-Based Class Balancing and Feature Selection*. Journal of Defense Technology and Engineering, 1(2), 65–80.
- Breiman, L. (2001). Random Forests. *Machine Learning*, 45, 5–32. https://doi.org/10.1023/A:1010933404324
- Chapman, P., et al. (2000). *CRISP-DM 1.0: Step-by-step Data Mining Guide*.
- National Institute of Standards and Technology. (2007). *Guide to Intrusion Detection and Prevention Systems (IDPS)* (SP 800-94). https://doi.org/10.6028/NIST.SP.800-94

## Fuentes de resultados del proyecto

- `thesis/00_resumen_conclusiones.md`
- `thesis/02_comprension_datos.md`
- `thesis/03_preparacion_diseno.md`
- `thesis/04_desarrollo_modelo.md`
- `thesis/05_integracion_prototipo.md`
- `thesis/06_pruebas_validacion.md`
- `thesis/07_despliegue_mantenimiento.md`
- `docs/resultados_modelado.json`
- `docs/resultados_validacion_por_dia.json`

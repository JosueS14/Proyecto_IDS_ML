# Guion para la presentación

Presentación editable: `IDS_ML_20_diapositivas.pptx`.

## 1. Detección de intrusiones en red con aprendizaje automático

Presenta el trabajo como un prototipo experimental de detección de intrusiones en flujos de red. La solución utiliza aprendizaje supervisado y Random Forest.

## 2. ¿Qué veremos?

Explica brevemente la secuencia: primero se define el problema, luego los datos y el modelo, después se contrastan los resultados con una evaluación más exigente y finalmente se muestra qué hace el prototipo.

## 3. El reto: identificar actividad maliciosa entre millones de flujos

El proyecto aborda la clasificación de flujos de red, no la inspección del contenido de paquetes. Además de medir detección, pregunta si el rendimiento se conserva cuando cambia el día de captura.

## 4. Un IDS informa; un IPS interviene

Aclara la diferencia entre detección y prevención. El sistema entrega predicciones y alertas sobre archivos; no actúa sobre conexiones ni sustituye a una solución operacional.

## 5. Objetivo y alcance experimental

El objetivo general es implementar y evaluar un prototipo supervisado con dos salidas. La versión inicial prioriza reproducibilidad e integración funcional sobre operación en tiempo real.

## 6. CIC-IDS2017: la base experimental

Los ocho CSV de CIC-IDS2017 contienen actividad benigna y distintas familias de ataques. Tras el proceso de preparación quedaron 2,827,677 registros y 78 características numéricas.

## 7. Antes de entrenar: depurar y reducir dependencias

La preparación elimina filas vacías, características faltantes o no finitas y duplicados exactos. Se excluyeron identificadores, IP, puertos y marcas de tiempo para reducir la dependencia de elementos específicos del escenario.

## 8. Pipeline reproducible de preparación

Resume las etapas de limpieza y transformación. La etiqueta original se convierte a un problema binario; la salida Parquet se acompaña de metadatos y trazabilidad.

## 9. El trabajo sigue un ciclo de análisis y desarrollo

El desarrollo está organizado en fases compatibles con el flujo de CRISP-DM: comprensión, preparación, modelado y evaluación, y se completa con la integración del prototipo. La selección del modelo usa validación, no el conjunto de prueba.

## 10. Random Forest para datos tabulares de flujo

Se compararon dos configuraciones del mismo algoritmo. La versión con pesos balanceados fue seleccionada por balanced accuracy de validación, con recall de la clase maliciosa y tasa de falsos positivos como criterios secundarios.

## 11. Diseño de evaluación: dos preguntas distintas

Distingue cuidadosamente ambos protocolos. La prueba agrupada responde cómo reconoce el modelo patrones conocidos separados por vector, mientras que leave-one-day-out evalúa una transferencia entre días completos.

## 12. Prueba agrupada: métricas altas para ataques conocidos

Presenta estas métricas con su contexto en la misma frase. El recall de 99.67% es alto en esta partición agrupada, pero no es evidencia de rendimiento operacional ni de generalización a escenarios externos.

## 13. ¿Qué errores cometió el modelo?

Explica las cuatro celdas. Los 164 falsos negativos son ataques clasificados como benignos; los 398 falsos positivos son flujos benignos que generarían una alerta.

## 14. El desempeño depende de la familia de ataque

Contrasta categorías abundantes con minoritarias. PortScan y DDoS muestran recall cercano a 100% en la prueba agrupada, mientras Bot es menor. SQL Injection tiene solo dos registros, así que el porcentaje no es una estimación estable.

## 15. Al separar días completos, el recall cae con fuerza

Esta es la advertencia metodológica central. Al dejar días completos fuera, el recall medio fue aproximadamente 7.28% sin balanceo y 7.23% con balanceo, muy por debajo de la prueba agrupada. Esto indica cambio de distribución y exige validación independiente.

## 16. Del archivo a la alerta: arquitectura del prototipo

Describe el flujo implementado: cargar un archivo, comprobar el esquema, inferir la clase de cada flujo y guardar resultados y alertas en archivos separados. La interfaz muestra como máximo diez mil filas por ejecución.

## 17. Una vista local para revisar flujos y alertas

La interfaz presenta los registros en una tabla, permite filtrar y consultar detalles. Los colores distinguen predicciones maliciosas, benignas y filas con errores de datos. La semejanza visual con Wireshark es de organización, no de captura de paquetes.

## 18. Validación funcional satisfactoria

La batería principal tuvo nueve pruebas satisfactorias. La inferencia de mil filas tomó cerca de 0.044 segundos después de cargar el modelo. Una prueba offline adicional comprobó el flujo completo; por su origen y tamaño no debe interpretarse como métrica de rendimiento.

## 19. Qué puede afirmarse y qué sigue pendiente

Separa los resultados obtenidos de los objetivos futuros. La prioridad es validar en datos independientes y estudiar robustez por captura o sesión antes de considerar un uso operacional.

## 20. Conclusiones

Cierra con tres ideas: el flujo técnico está implementado, el resultado de la partición agrupada es prometedor para patrones conocidos y la evaluación por días limita cualquier afirmación de generalización. Agradece y abre preguntas.

## Fuentes internas del proyecto

- `thesis/00_resumen_conclusiones.md`
- `thesis/02_comprension_datos.md`
- `thesis/03_preparacion_diseno.md`
- `thesis/04_desarrollo_modelo.md`
- `thesis/05_integracion_prototipo.md`
- `thesis/06_pruebas_validacion.md`
- `docs/resultados_modelado.json`
- `docs/resultados_validacion_por_dia.json`

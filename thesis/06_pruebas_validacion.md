# Fase 6. Pruebas y validación

## 1. Propósito

Esta fase verifica el funcionamiento del modelo integrado y del prototipo IDS mediante pruebas funcionales, de integración, de robustez y de rendimiento básico. No se reentrena el modelo ni se modifica el conjunto preparado.

Las pruebas se ejecutan mediante `src/pruebas/06_validar_prototipo.py` y generan `docs/resultados_validacion.json`.

## 2. Casos de prueba

| Prueba | Objetivo | Resultado |
| --- | --- | --- |
| Carga del modelo y esquema | Verificar que el artefacto contiene las clases y 78 características esperadas. | PASÓ |
| Inferencia con Parquet preparado | Clasificar un lote válido del dataset preparado. | PASÓ |
| Inferencia con CSV original | Clasificar un lote original y conservar campos contextuales cuando existan. | PASÓ |
| Rechazo de esquema inválido | Comprobar que una característica faltante sea reportada. | PASÓ |
| Manejo de valores inválidos | Marcar registros con valores infinitos como `ERROR_DATOS`. | PASÓ |
| Consistencia de alertas | Verificar que `MALICIOUS` produzca `ALERTA` y `BENIGN` produzca `NO`. | PASÓ |
| Filtro de interfaz | Comprobar filtros por tráfico malicioso. | PASÓ |
| Inferencia de lote de 1,000 filas | Medir el procesamiento básico de un lote. | PASÓ |
| Compilación de componentes | Verificar la sintaxis del motor y de la interfaz Tkinter. | PASÓ |

## 3. Resultados

Se ejecutaron 9 pruebas y las 9 finalizaron correctamente.

### 3.1 Parquet preparado

En una muestra de 200 registros:

- 199 fueron clasificados como `BENIGN`.
- 1 fue clasificado como `MALICIOUS`.
- 0 registros presentaron errores de datos.

### 3.2 CSV original

En una muestra de 200 registros del archivo Monday:

- 192 fueron clasificados como `BENIGN`.
- 0 fueron clasificados como `MALICIOUS`.
- 8 fueron marcados como `ERROR_DATOS` debido a valores no utilizables.
- Los campos `Flow ID`, `Timestamp`, `Source IP` y `Destination IP` estuvieron disponibles en los registros válidos.

Marcar un registro inválido como `ERROR_DATOS` evita producir una predicción silenciosamente incorrecta.

### 3.3 Rendimiento básico

La inferencia sobre 1,000 filas se completó en aproximadamente 0.08 segundos después de cargar el modelo. El tiempo total de la prueba, incluyendo carga y preparación, fue inferior a un segundo en el entorno utilizado.

## 4. Validación de alertas

La validación comprobó las siguientes reglas:

- Predicción `MALICIOUS` implica alerta `ALERTA`.
- Predicción `BENIGN` implica alerta `NO`.
- Los registros inválidos no generan una alerta de ataque y se marcan como `ERROR_DATOS`.
- La interfaz conserva la etiqueta real cuando el archivo de entrada la contiene.
- Los resultados pueden filtrarse por clase o alerta.

## 5. Limitaciones de las pruebas

- Las pruebas funcionales utilizan muestras pequeñas y no sustituyen una evaluación estadística completa.
- La evaluación del desempeño predictivo corresponde a la fase 4 y se conserva en `docs/resultados_modelado.json`.
- La interfaz Tkinter requiere una verificación manual de interacción visual.
- No se probó captura de paquetes ni procesamiento en tiempo real porque están fuera del alcance inicial.
- No se probó la respuesta activa porque el prototipo funciona como IDS, no como IPS.

## 6. Artefactos

- `src/pruebas/06_validar_prototipo.py`: batería reproducible de pruebas.
- `docs/resultados_validacion.json`: resultado de las pruebas.
- `thesis/06_pruebas_validacion.md`: documentación de la validación.

Con estas pruebas se cierra la **fase 6. Pruebas y validación**. La siguiente etapa será la **fase 7. Despliegue y mantenimiento**, donde se prepararán la guía de uso, instalación, monitoreo y actualización del modelo.

# Contribuciones

El enunciado pide que cada integrante sea responsable de al menos una de estas
areas: **datos**, **entrenamiento**, o **validacion y errores**.

| Area | Tarea | Responsable | Evidencia |
|---|---|---|---|
| Datos | 12 esquemas propios con `COMMENT`, en espanol, ingles y abreviados | Cindy Gualim | `datos/esquemas/*.sql`, commit `04ce606` |
| Datos | Poblador generico con semilla fija sobre `information_schema` | Cindy Gualim | `scripts/poblar_datos.py`, commits `04ce606`, `db3a9dc` |
| Datos | 32 plantillas de generacion en tres niveles | Cindy Gualim | `scripts/generar_pares.py`, commit `742de7d` |
| Datos | Validacion por ejecucion y reporte de descartes | Cindy Gualim | `scripts/validar_pares.py`, `datos/descartes.csv`, commit `3795ec3` |
| Validacion | 2 esquemas nuevos y 40 preguntas escritas a mano | Cindy Gualim | `datos/validacion/`, commit `2f400c3` |
| Entrega | `solucion.py` y pruebas de la limpieza de salida | Cindy Gualim | `solucion.py`, `scripts/test_extraccion.py` |
| Validacion | Evaluador de EX ponderada y sus pruebas | Cindy Gualim | `scripts/evaluar.py`, `scripts/test_comparacion.py` |
| Entrenamiento | Script de LoRA / QLoRA y las dos configuraciones | _(pendiente)_ | `scripts/entrenar.py`, `resultados/configs_lora.md` |
| Entrenamiento | Corrida en Colab T4 y curvas de loss | _(pendiente)_ | `resultados/loss_r8.csv`, `resultados/loss_r32.csv`, `resultados/curvas_loss.png` |
| Validacion | Experimento de inferencia: few-shot y autocorreccion | _(pendiente)_ | `resultados/experimento_inferencia.md` |
| Validacion | Analisis de errores por categoria | _(pendiente)_ | `scripts/analizar_errores.py`, `resultados/analisis_errores.csv` |
| Entrega | Presentacion y prediccion de EX | _(pendiente)_ | `presentacion.pdf`, `resultados/prediccion_ex.md` |

## Estado de la colaboracion

A la fecha de este documento, **todos los commits del repositorio son de una
sola cuenta**. El enunciado es explicito: un repositorio sin commits de ambos
integrantes recibe 0 en el componente de colaboracion, que vale 7 puntos.

Las filas marcadas como pendientes estan asignadas al segundo integrante y deben
cerrarse con commits hechos desde su propia cuenta de GitHub. Las areas
disponibles, y que no se solapan con lo ya hecho, son:

- **entrenamiento**: correr las dos configuraciones en Colab, documentar los
  parametros entrenables, el tiempo y las curvas, y elegir el adapter que se
  entrega;
- **validacion y errores**: correr las tres variantes de inferencia, clasificar
  los fallos por categoria e interpretar que cuesta mas peso en la metrica.

Este documento debe actualizarse con el nombre real y el hash de los commits
correspondientes antes de la entrega.

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
| Entrenamiento | Script de LoRA / QLoRA y las dos configuraciones | Gadiel Ocana | `scripts/entrenar.py`, `resultados/configs_lora.md` |
| Entrenamiento | Corrida en Colab T4 y curvas de loss | Gadiel Ocana | `resultados/loss_r8.csv`, `resultados/loss_r32.csv`, `resultados/curvas_loss.png` |
| Validacion | Experimento de inferencia: few-shot y autocorreccion | Gadiel Ocana | `resultados/experimento_inferencia.md` |
| Validacion | Analisis de errores por categoria | Gadiel Ocana | `scripts/analizar_errores.py`, `resultados/analisis_errores.csv` |
| Entrega | Presentacion y prediccion de EX | Gadiel Ocana | `presentacion.pdf`, `resultados/prediccion_ex.md` |

## Estado de la colaboracion

Ambos integrantes tienen commits propios en el repositorio, hechos desde su
cuenta y repartidos a lo largo del desarrollo:

| Cuenta | Correo | Commits |
|---|---|---|
| Cindy Gualim | gua21226@uvg.edu.gt | 8 |
| GAOV314 (Gadiel Ocana) | oca231270@uvg.edu.gt | 5 |

El detalle, con fecha y archivos de cada commit, esta en `historial_git.txt`.

Nota: dos de los commits de Cindy aparecen con nombres de autor distintos
(`Cindy Gualim` y `MishelLearning 3`) aunque usan el mismo correo. Es la misma
persona; se puede unificar con `git config user.name`.

## Lo que falta

| Tarea | Responsable | Estado |
|---|---|---|
| Correr las dos configuraciones de LoRA en Colab T4 | Gadiel Ocana | pendiente |
| Copiar el adapter ganador a `adapter/` | Gadiel Ocana | pendiente |
| Evaluar con adapter y llenar `resultados/configs_lora.md` | Gadiel Ocana | pendiente |
| Correr las tres variantes de inferencia | Gadiel Ocana | pendiente |

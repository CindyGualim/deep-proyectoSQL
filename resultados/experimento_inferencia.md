# Experimento de inferencia

Se comparan tres variantes **sobre el mismo adapter y el mismo criterio de EX**,
cambiando solo como se arma la inferencia. Las tres se corren con
`scripts/evaluar.py` sobre las 40 preguntas de la validacion propia.

| Variante | Comando | Que cambia |
|---|---|---|
| directa | `--etiqueta adapter` | el prompt del contrato, una sola generacion |
| few-shot | `--etiqueta adapter_fewshot --few-shot` | tres ejemplos resueltos antes de la pregunta |
| autocorreccion | `--etiqueta adapter_autocorr --autocorreccion` | ejecuta la consulta y la reescribe con el error |

## Como funciona la autocorreccion

El evaluador puede entregar `ejecutar(sql)`, que corre la consulta con un usuario
de solo lectura y devuelve `ok`, `columnas`, `filas` y `error`, con un tope de
**3 llamadas por pregunta**. El ciclo esta en `solucion._autocorregir`:

1. Se ejecuta la consulta generada. Si corre y devuelve filas, se entrega.
2. Si falla, se vuelve a generar agregando al prompt la consulta anterior y el
   error del motor, y se repite.
3. Una consulta que se ejecuta pero devuelve cero filas se guarda como respaldo
   y se intenta mejorar; si los intentos siguientes fallan, se entrega el
   respaldo antes que una consulta rota.

El contador de llamadas vive fuera del modelo, asi que nunca se pasa de 3 aunque
el ciclo quiera seguir. El numero de llamadas usadas por pregunta queda en la
columna `llamadas_ejecutar` de `resultados/validacion_propia.csv`.

## Hipotesis, escritas antes de correrlo

**Few-shot.** Esperamos una mejora pequena o nula *despues* del fine-tuning, y
una mejora visible sobre el modelo base. El adapter ya aprende el formato de
salida con 2,320 ejemplos; tres ejemplos mas en el prompt no agregan informacion
nueva, solo alargan el contexto. Si few-shot mejora mucho al modelo ya ajustado,
seria senal de que el adapter no aprendio el formato.

**Autocorreccion.** Esperamos la mejora mas grande de las tres, concentrada en
los errores de `columna_inexistente` y `tabla_inexistente`: son los unicos que el
motor reporta de forma explicita y accionable (`Unknown column 'x' in 'field
list'`). No esperamos mejora en `resultado_distinto`, porque ahi la consulta
corre sin error y el modelo no recibe ninguna senal de que esta equivocada: ese
es el limite duro del metodo.

El costo es tiempo: cada correccion es una generacion mas. Con hasta 2
regeneraciones por pregunta, el peor caso triplica el tiempo, y hay que
verificar que siga por debajo de los 30 segundos del contrato.

## Resultados

| Variante | EX | facil | media | dificil | seg/pregunta | llamadas a ejecutar |
|---|---|---|---|---|---|---|
| directa | _(pendiente)_ | | | | | 0 |
| few-shot | _(pendiente)_ | | | | | 0 |
| autocorreccion | _(pendiente)_ | | | | | |

## Analisis de errores

`scripts/analizar_errores.py` clasifica cada fallo en sintaxis, tabla o columna
inexistente, join, agregacion, filtro o resultado distinto, y reporta tanto el
numero de preguntas como el **peso perdido** por categoria, que es lo que de
verdad mueve la EX: fallar una dificil cuesta lo mismo que fallar tres faciles.

Resultados en `resultados/analisis_errores.csv`.

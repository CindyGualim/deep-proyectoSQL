# Bitacora

Entradas fechadas del desarrollo del Proyecto 3. Cada una indica su autor.

---

## 2026-10-25 — Estructura del repositorio y contrato vacio
**Autor:** Cindy Gualim

Se arma el esqueleto: `config.json` con las cuatro claves del enunciado,
`requirements.txt` y las carpetas `datos/`, `notebooks/`, `resultados/`,
`scripts/` y `adapter/`.

Decision: `torch` queda sin version exacta en `requirements.txt`. Fijarlo obliga
a Colab a reinstalar las ruedas de CUDA, que tardan varios minutos y pueden
quedar desalineadas con el driver del entorno.

Commit: `chore: estructura del proyecto y requirements`

---

## 2026-10-25 — Doce esquemas propios en MySQL 8.4.10
**Autor:** Cindy Gualim

Se escriben 12 esquemas de 6 a 7 tablas con `COMMENT` en cada tabla y cada
columna, porque es lo que el evaluador entrega al modelo via `SHOW CREATE TABLE`.

Se mezclan idiomas y estilos a proposito, siguiendo lo que anuncia el enunciado
sobre la evaluacion oculta: cinco en espanol, tres en ingles, dos abreviados
(`clinica` con `pac`/`med`/`cita`, `gym` con `mbr`/`cls`/`bkg`) y dos mezclados,
uno de ellos con clave primaria no numerica (`aeropuertos.iata`) y otro con tabla
puente.

En vez de escribir los INSERT a mano se hace un poblador generico que lee
`information_schema`, ordena las tablas por dependencias y genera valores con
semilla fija. Asi el mismo codigo sirve para los esquemas de validacion y los
datos no "se parecen" entre particiones por haberlos escrito con la misma mano.

Commit: `feat(datos): 12 esquemas propios y carga en MySQL 8.4.10`

---

## 2026-10-25 — Generador de pares pregunta-SQL
**Autor:** Cindy Gualim

32 plantillas parametricas: 11 faciles (una tabla), 10 medias (JOIN, GROUP BY,
HAVING) y 11 dificiles (subconsultas, WITH, funciones de ventana, fechas).

Decision importante: los umbrales de los filtros no son constantes inventadas,
salen de muestrear 80 filas de cada tabla y tomar p25, p50 y p75. Un filtro que
no coincide con ningun dato produce un par inutil.

Cada `GROUP BY` incluye la clave primaria ademas de la etiqueta, por
`ONLY_FULL_GROUP_BY`.

Commit: `feat(datos): generacion de pares pregunta-SQL`

---

## 2026-10-25 — Primera corrida real contra el motor
**Autor:** Cindy Gualim

Se levanta `mysql:8.4.10` en Docker y se cargan los 12 esquemas. El poblador
falla tres veces seguidas, y las tres son errores reales que no se ven leyendo
el codigo:

1. `1264 Out of range value for 'max_cls'`: la pista "capacidad" generaba hasta
   200 en un `TINYINT`.
2. `1406 Data too long for 'room'`: texto de direccion en un `VARCHAR(20)`.
3. `1062 Duplicate entry '40' for 'mesas.numero'`: la deduplicacion de columnas
   `UNIQUE` solo cubria texto, no numeros.

Corregidos los tres: 78 tablas, 9,525 filas. El dataset queda 47% facil, asi que
se cambia el tope por uno por nivel y pasa a 37/37/25.

Commit: `fix(datos): acotar valores al tipo de columna y balancear niveles`

---

## 2026-10-25 — Validacion por ejecucion y descartes
**Autor:** Cindy Gualim

Se ejecutan los 2,464 pares con el usuario `lector`, sin permisos de escritura,
para replicar la condicion del evaluador. Cero errores de sintaxis.

La verificacion de preguntas duplicadas destapa algo mas serio que una
repeticion: ambiguedad real. `vuelos` tiene dos claves foraneas a `aeropuertos`
(`origen` y `destino`), y `prestamos` apunta a `clientes` y a `sucursales`, que
ademas tienen las dos una columna `nombre`. La pregunta no determinaba cual usar.

Lo grave no era el par descartado sino el que se quedaba: entrenaba al modelo a
adivinar. Se agrega `columnas_ambiguas()` al generador y se corrigen cuatro
redacciones que omitian el nombre de la tabla. Las preguntas duplicadas pasan de
19 a 13 a 0.

Quedan 2,320 pares de entrenamiento y 71 de dev; 73 descartes, todos por
devolver cero filas.

Commit: `feat(datos): validacion por ejecucion y reporte de descartes`

---

## 2026-10-25 — Validation set propio
**Autor:** Cindy Gualim

Dos esquemas nuevos, `veterinaria` (espanol) y `hotel` (ingles), y 40 preguntas
escritas a mano: 13 faciles, 13 medias, 14 dificiles, peso total 81. Las
preguntas van en espanol tambien sobre el esquema en ingles, que es el caso
cruzado que anuncia el enunciado.

Escribirlas a mano encuentra dos defectos del poblador que ninguna prueba
automatica habria encontrado: las mascotas recibian fechas de nacimiento de
persona (perros de 60 anios) y el `score` de las resenas llegaba a 100 cuando su
`COMMENT` dice 1 a 5.

Se renombra `hotel.reviews` a `guest_reviews`: era el unico nombre de tabla que
se repetia con el entrenamiento. La particion por esquema queda sin ninguna
interseccion, que es la condicion para no perder 15 puntos.

Commit: `feat(datos): validation set propio con 40 preguntas`

---

## 2026-10-25 — Contrato de entrega
**Autor:** Cindy Gualim

`solucion.py` con `generar_sql`, carga perezosa y generacion determinista.

`extraer_sql` corta en el primer punto y coma y rechaza cualquier cosa que
empiece por `INSERT`, `UPDATE`, `DELETE` o DDL, devolviendo `SELECT 1`. Se pierde
esa pregunta, pero no se arriesgan los 10 puntos de penalizacion por consultas
que modifican la base. 11 casos de prueba en `scripts/test_extraccion.py`.

Prueba de humo con el 0.5B en CPU: carga 133.8 s (tope 300), generacion de 5 a
8 s por pregunta (tope 30), y la misma pregunta dos veces da exactamente lo
mismo. El modelo base ya acierta las faciles y falla en cuanto hay que recorrer
dos claves foraneas.

Commit: `feat: solucion.py con contrato generar_sql`

---

## 2026-10-25 — Evaluador por ejecucion
**Autor:** Cindy Gualim

`coincide()` implementa las cuatro reglas del enunciado. La decision discutible
es la de las columnas: se acepta una columna de mas, pero se exige que las
columnas pedidas aparezcan en su orden relativo. Aceptar cualquier permutacion
inflaria la EX medida y haria inutil la prediccion final.

Se reescribio antes de usarla: la primera version ordenaba las filas crudas por
`str()` para comparar conjuntos, y eso falla cuando la referencia trae
`Decimal('2.50')` y la prediccion `2.5`. Ahora normaliza primero y ordena
despues. 20 casos de prueba en `scripts/test_comparacion.py`.

Commit: `feat(eval): evaluador EX y baseline sin adapter`

---

## 2026-10-25 — Entrenamiento LoRA
**Autor:** Gadiel Ocana

Dos configuraciones que difieren en un solo factor, el rank: `r=8` y `r=32`, con
`alpha=32` fijo en ambas. Escalar `alpha` con el rank habria cambiado dos cosas a
la vez y no se podria atribuir la diferencia.

El prompt de entrenamiento se importa de `solucion.py` en vez de copiarse:
entrenar con un formato y generar con otro es la forma mas silenciosa de perder
puntos. La perdida se calcula solo sobre la consulta; el esquema y la pregunta
van enmascarados con `-100`.

Hipotesis previas en `resultados/configs_lora.md`.

Commit: `feat(train): LoRA r8 vs r32 y adapter final`

---

## 2026-10-25 — Experimento de inferencia y analisis de errores
**Autor:** Gadiel Ocana

Tres variantes sobre el mismo adapter: directa, few-shot y autocorreccion con
`ejecutar`, con el tope de 3 llamadas controlado fuera del modelo.

La hipotesis es que la autocorreccion solo puede arreglar lo que el motor reporta
explicitamente (`Unknown column`, `Table doesn't exist`) y no hara nada por los
`resultado_distinto`, donde la consulta corre sin error y el modelo no recibe
ninguna senal de que esta equivocada.

Commit: `feat(eval): autocorreccion con ejecutar y analisis de errores`

---

## Pendiente — Commits de Gadiel Ocana

Este repositorio todavia no tiene commits del segundo integrante. El enunciado
exige commits de ambas cuentas y penaliza con 0 en colaboracion si falta uno.
Las entradas de esta bitacora que corresponden a su trabajo deben escribirse y
firmarse por el, no por la otra integrante.

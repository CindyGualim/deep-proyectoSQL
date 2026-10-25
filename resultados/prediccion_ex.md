# Prediccion justificada de la EX en la evaluacion oculta

## Prediccion

**EX entre 0.45 y 0.60, con 0.52 como valor mas probable.**

Por nivel esperamos aproximadamente:

| Nivel | Peso | EX esperada |
|---|---|---|
| facil | 1 | 0.80 – 0.90 |
| media | 2 | 0.45 – 0.60 |
| dificil | 3 | 0.20 – 0.35 |

La EX ponderada castiga el nivel dificil tres veces mas que el facil, asi que el
numero global queda mucho mas cerca del desempeno en dificil que del de facil.
Con 13/13/14 preguntas y pesos 1/2/3, el 63% del peso total esta en media y
dificil.

## De donde sale el numero

**1. Nuestra validacion propia es optimista.** Las 40 preguntas las escribimos
nosotros sobre esquemas que diseniamos nosotros, con el mismo estilo de
redaccion que usamos para pensar el problema. El docente escribira las suyas sin
conocer nuestras convenciones. Historicamente la caida entre una validacion
propia y una ciega esta entre 0.10 y 0.20 de EX; descontamos 0.15.

**2. El dataset viene de 32 plantillas, no de lenguaje natural libre.** Es la
limitacion mas seria de la entrega. El modelo vera formas de preguntar que no
aparecen en el entrenamiento: elipsis, sinonimos del dominio, preguntas que no
nombran la columna. Mitigamos con dos parafrasis por plantilla y alternando el
nombre literal de la columna con su etiqueta tomada del `COMMENT`, pero no
sustituye la variedad de preguntas escritas por personas distintas.

**3. Los esquemas ocultos tendran de 5 a 10 tablas.** Los nuestros tienen de 6 a
7, asi que el tamanio es comparable. Incluimos a proposito nombres abreviados
(`pac`, `med`, `mbr`, `cls`), mezcla de espanol e ingles, clave primaria no
numerica y tabla puente, porque el enunciado anuncia esas condiciones.

**4. Lo que ya medimos del modelo base.** En la prueba de humo, el modelo sin
adapter acierta las preguntas de una tabla y falla en cuanto hay que recorrer
dos claves foraneas: invento `bookings.type_id` cuando `type_id` esta en `rooms`.
Ese es exactamente el error que el fine-tuning puede corregir, porque es
anclaje al esquema y no razonamiento. Por eso esperamos la mayor ganancia en el
nivel medio.

**5. Donde no esperamos ganar.** Las preguntas dificiles que exigen elegir entre
una subconsulta correlacionada, una funcion de ventana y un CTE dependen de
entender la pregunta, no de recordar el formato. 564 ejemplos dificiles ayudan,
pero un modelo de 1.5B tiene un techo ahi.

## Sobre la mejora respecto del modelo sin adapter

Esperamos **entre +0.20 y +0.30 de EX**, por encima del umbral de +0.15 que pide
el enunciado para los 10 puntos completos.

La razon es que buena parte de los fallos del modelo base no son de SQL sino de
formato y de anclaje: responde con explicaciones, con markdown, o usa columnas
que no existen en la tabla que eligio. Son errores baratos de corregir con
2,320 ejemplos de formato consistente, y el baseline parte de un piso bajo.

Esta es la parte de la prediccion de la que estamos mas seguros. La EX absoluta
depende de como redacte las preguntas el docente; la **diferencia** entre las dos
versiones se mide sobre las mismas preguntas y absorbe ese factor.

## Que la cambiaria

- Si la autocorreccion con `ejecutar` funciona como esperamos, sumaria entre
  0.05 y 0.10, concentrado en `columna_inexistente` y `tabla_inexistente`. El
  evaluador la ofrece, y es el unico mecanismo que ve el esquema real en vez de
  su descripcion.
- Si las preguntas ocultas piden columnas con nombres que no aparecen literal en
  la pregunta, la EX cae por debajo de 0.45.
- Si los esquemas ocultos usan tipos o construcciones que no cubrimos (vistas,
  claves compuestas mas alla de la tabla puente, `DECIMAL` de alta precision), el
  nivel dificil cae mas.

## Como verificar esta prediccion

Los numeros de arriba se contrastan con `resultados/validacion_propia.csv`. Si la
EX con adapter en nuestra validacion queda cerca de 0.67, la prediccion de 0.52
en la oculta es consistente con el descuento de 0.15 que aplicamos. Si queda muy
por encima, probablemente estemos sobreajustados a nuestras propias plantillas y
habria que bajar la prediccion.

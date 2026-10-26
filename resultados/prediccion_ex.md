# Prediccion justificada de la EX en la evaluacion oculta

## Prediccion

**EX entre 0.45 y 0.65, con 0.55 como valor mas probable.**
**Mejora sobre el modelo sin adapter: entre +0.08 y +0.19.**

Por nivel esperamos aproximadamente:

| Nivel | Peso | EX esperada |
|---|---|---|
| facil | 1 | 0.80 - 0.90 |
| media | 2 | 0.60 - 0.75 |
| dificil | 3 | 0.30 - 0.45 |

## El punto de partida: el baseline medido

El modelo base, sin adapter y con el mismo prompt, obtiene **EX 0.580** sobre
nuestra validacion propia (47 de 81 puntos de peso):

| Nivel | Preguntas | Peso acertado | EX |
|---|---|---|---|
| facil | 12/13 | 12/13 | 0.92 |
| media | 10/13 | 20/26 | 0.77 |
| dificil | 5/14 | 15/42 | 0.36 |
| **total** | **27/40** | **47/81** | **0.580** |

Este numero es mas alto de lo que anticipabamos y cambia la lectura de la
entrega. Los 10 puntos por "mejorar el EX en al menos 0.15" se miden contra esta
base, asi que el margen por arriba es estrecho.

## De donde sale la prediccion

**1. Descuento por evaluacion ciega.** Las 40 preguntas las escribimos nosotros
sobre esquemas que disenamos nosotros. El docente escribira las suyas sin conocer
nuestras convenciones de redaccion. Descontamos 0.15 sobre el absoluto.

**2. El techo del adapter se puede calcular.** El analisis de errores dice donde
se pierden los 34 puntos de peso del baseline:

| Categoria | Preguntas | Peso perdido |
|---|---|---|
| columna inexistente | 5 | 12 |
| join | 3 | 8 |
| agregacion | 3 | 8 |
| tabla inexistente | 1 | 3 |
| sintaxis | 1 | 3 |

Columna y tabla inexistente suman **15 de los 34 puntos, el 44%**. Son errores de
anclaje al esquema, no de razonamiento: el modelo invento una tabla `payments`
que no existe en la base `hotel`, a partir de lo que sabe de otros esquemas. Es
exactamente lo que 2,320 ejemplos con el esquema en el prompt pueden corregir.

Si el adapter recuperara **todos** esos 15 puntos, la EX subiria a 0.765 y la
mejora seria +0.185. Ese es el techo optimista, no la expectativa. Lo realista es
recuperar entre la mitad y dos tercios, mas algo de los 8 puntos de agregacion,
donde el formato consistente del dataset deberia ayudar con ONLY_FULL_GROUP_BY.
De ahi el rango +0.08 a +0.19.

**3. Donde no esperamos ganar.** Los errores de join y de agregacion suman 16
puntos y exigen entender la pregunta, no recordar un formato. 564 ejemplos
dificiles ayudan, pero un modelo de 1.5B tiene un techo ahi.

**4. La limitacion que asumimos.** El dataset viene de 32 plantillas, no de
lenguaje natural libre. El modelo vera formas de preguntar que no aparecen en el
entrenamiento. Lo mitigamos con dos parafrasis por plantilla y alternando el
nombre literal de la columna con su etiqueta tomada del COMMENT, pero no
sustituye la variedad de preguntas escritas por personas distintas.

## Que la cambiaria

- **La autocorreccion con `ejecutar`** es la palanca mas prometedora que nos
  queda: ataca justo las dos categorias que el motor reporta de forma explicita,
  que son el 44% del peso perdido. Si funciona, sumaria entre 0.05 y 0.10.
- Si el adapter no supera +0.15, la nota de ese componente es proporcional, no
  cero. Conviene entregarlo igual y reportar el numero honesto.
- Si los esquemas ocultos usan construcciones que no cubrimos (vistas, claves
  compuestas mas alla de la tabla puente), el nivel dificil cae mas.

## Riesgo operativo medido

El tiempo por pregunta del baseline fue de **26.8 s de media y 76.1 s de maximo**,
pero medido en CPU. El contrato permite 30 s. En la GPU T4 del entorno de
evaluacion se espera un orden de magnitud menos, pero **hay que verificarlo ahi**
antes de entregar: si una sola pregunta pasa de 30 s, esa pregunta se pierde.

## Como verificar esta prediccion

Con el adapter entrenado, `scripts/evaluar.py --etiqueta adapter` sobre la misma
validacion da el numero comparable. Si la EX con adapter queda cerca de 0.70, la
prediccion de 0.55 en la oculta es consistente con el descuento de 0.15. Si queda
muy por encima de 0.80, es probable que estemos sobreajustados a nuestras propias
plantillas y habria que bajar la prediccion.

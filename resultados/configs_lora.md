# Dos configuraciones de LoRA

Las dos corridas difieren en **un solo factor: el rank**. Todo lo demas se
mantiene fijo: `alpha=32`, `dropout=0.05`, `lr=2e-4`, 2 epocas, lote efectivo 16,
scheduler coseno, semilla 2026, y los mismos siete modulos objetivo
(`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`).

Mantener `alpha` fijo mientras cambia `r` es intencional: si se escalara
`alpha = 2r`, cambiarian a la vez la capacidad del adapter y la magnitud
efectiva de su contribucion, y no se podria atribuir la diferencia a ninguno de
los dos.

## Hipotesis, escritas antes de entrenar

**Configuracion A (`r=8`).** Capacidad baja, ~9M parametros entrenables.
Hipotesis: alcanza para aprender el *formato* de salida (una sola consulta, sin
markdown, nombres exactos del esquema) y para las preguntas faciles y medias,
que son patrones repetidos. Esperamos que la mayor parte de la mejora sobre el
baseline venga de aqui, porque el error dominante del modelo base no es de
razonamiento sino de formato y de anclaje al esquema.

**Configuracion B (`r=32`).** Cuatro veces mas capacidad, ~36M parametros
entrenables. Hipotesis: mejora sobre A en el nivel dificil, donde hace falta
recordar la forma de una subconsulta correlacionada o de una funcion de ventana,
pero con mas riesgo de sobreajuste a las 32 plantillas del dataset. La senal a
vigilar es la loss de validacion sobre `datos/dev.jsonl`: si A y B tienen la
misma loss de dev, la capacidad extra no se esta usando.

**Prediccion.** Esperamos que B gane por poco en EX global (menos de 0.05) y que
la diferencia se concentre en las preguntas de peso 3. Si B no mejora a A,
entregamos A: menos parametros, menos riesgo de sobreajuste y un adapter mas
liviano.

## Resultados

| | A (`r=8`) | B (`r=32`) |
|---|---|---|
| Parametros entrenables | _(pendiente)_ | _(pendiente)_ |
| Tiempo de entrenamiento | _(pendiente)_ | _(pendiente)_ |
| Loss final de entrenamiento | _(pendiente)_ | _(pendiente)_ |
| Loss final de validacion (dev) | _(pendiente)_ | _(pendiente)_ |
| EX en validacion propia | _(pendiente)_ | _(pendiente)_ |

Las curvas quedan en `resultados/loss_r8.csv` y `resultados/loss_r32.csv`, y la
ficha de cada corrida en `resultados/corrida_r8.json` y
`resultados/corrida_r32.json`. El notebook `02_entrenamiento.ipynb` las grafica.

El adapter de la configuracion elegida se copia a `adapter/`, que es la carpeta
que lee `config.json`.

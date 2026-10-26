# Proyecto 3 — Text-to-SQL con LoRA

Fine-tuning de `Qwen/Qwen2.5-Coder-1.5B-Instruct` con LoRA para traducir preguntas en
espanol a consultas MySQL 8.4.10, dado el esquema de la base en formato `SHOW CREATE TABLE`.

Universidad del Valle — Deep Learning 2026 — Kevin Recinos.

**Integrantes:** Cindy Gualim · Gadiel Ocana

## Ejecucion rapida

```bash
pip install -r requirements.txt
```

```python
from solucion import generar_sql

esquema = open("datos/validacion/esquemas/veterinaria.sql").read()
print(generar_sql(esquema, "Cuantas mascotas hay registradas?"))
```

`generar_sql(esquema, pregunta, ejecutar=None)` devuelve **una sola** consulta
`SELECT` o `WITH ... SELECT`. Si el evaluador entrega `ejecutar(sql)` y
`autocorreccion` esta activa, la consulta se verifica y se corrige con el error
del motor, con un tope de 3 llamadas por pregunta. La generacion es determinista
(`do_sample=False`, `num_beams=1`, semilla 2026).

## Configuracion

```json
{
  "modelo_base": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
  "adapter": "adapter/",
  "usar_adapter": true,
  "semilla": 2026
}
```

Con `"usar_adapter": false` se carga el modelo base con **el mismo prompt**, que es
la version de baseline. Las claves opcionales `"few_shot"` y `"autocorreccion"`
activan las dos variantes de inferencia que se miden en
`resultados/experimento_inferencia.md`.

Si `usar_adapter` es `true` pero `adapter/` no contiene `adapter_config.json`, el
programa avisa y sigue con el modelo base en vez de fallar.

## Como se reproduce todo

```bash
# 1. MySQL 8.4.10 con la configuracion por defecto (incluye ONLY_FULL_GROUP_BY)
bash scripts/mysql_setup.sh docker        # o: bash scripts/mysql_setup.sh colab
export MYSQL_HOST=127.0.0.1 MYSQL_PORT=3306 MYSQL_USER=root MYSQL_PASSWORD=proyecto3

# 2. Datos
python scripts/cargar_esquemas.py --dir datos/esquemas --poblar
python scripts/cargar_esquemas.py --dir datos/validacion/esquemas --poblar
python scripts/generar_pares.py --limite 20
MYSQL_USER=lector MYSQL_PASSWORD=lector python scripts/validar_pares.py

# 3. Entrenamiento (necesita GPU)
python scripts/entrenar.py --etiqueta r8  --rank 8  --alpha 32
python scripts/entrenar.py --etiqueta r32 --rank 32 --alpha 32

# 4. Evaluacion
MYSQL_USER=lector MYSQL_PASSWORD=lector python scripts/evaluar.py --etiqueta baseline --sin-adapter
MYSQL_USER=lector MYSQL_PASSWORD=lector python scripts/evaluar.py --etiqueta adapter
python scripts/analizar_errores.py
```

Pruebas de las dos funciones de las que depende toda la medicion:

```bash
python scripts/test_extraccion.py     # 11 casos: limpieza de la salida del modelo
python scripts/test_comparacion.py    # 20 casos: criterio de exactitud por ejecucion
```

## Estructura del repositorio

```
solucion.py                  contrato de entrega: generar_sql()
config.json                  modelo base, adapter, semilla
requirements.txt             dependencias verificadas en Colab T4
adapter/                     adapter LoRA entrenado

datos/
  esquemas/                  12 esquemas propios de entrenamiento
  entrenamiento.jsonl        2,320 pares validados en MySQL 8.4.10
  dev.jsonl                  71 pares para vigilar la loss
  descartes.csv              pares rechazados, con su motivo
  pares_crudos.jsonl         salida del generador, antes de validar
  esquemas_show_create.json  esquema de cada base, como lo ve el modelo
  validacion/
    esquemas/                2 esquemas que NO aparecen en el entrenamiento
    preguntas.jsonl          40 preguntas escritas a mano, en tres niveles

scripts/
  mysql_setup.sh             levanta MySQL 8.4.10 (docker o colab)
  db.py                      conexion y SHOW CREATE TABLE
  cargar_esquemas.py         crea una base por archivo .sql
  poblar_datos.py            poblador generico con semilla fija
  generar_pares.py           32 plantillas en tres niveles
  validar_pares.py           validacion por ejecucion y descartes
  entrenar.py                LoRA / QLoRA
  evaluar.py                 EX ponderada
  analizar_errores.py        clasificacion de fallos por categoria
  test_extraccion.py         pruebas de la limpieza de salida
  test_comparacion.py        pruebas del criterio de EX

notebooks/
  01_datos.ipynb             generacion y validacion del dataset
  02_entrenamiento.ipynb     las dos configuraciones de LoRA y sus curvas
  03_evaluacion.ipynb        baseline, adapter y comparacion

resultados/
  validacion_propia.csv      una fila por pregunta y por corrida
  descartes_resumen.csv      conteo de descartes por motivo
  configs_lora.md            hipotesis y resultados de las dos configuraciones
  experimento_inferencia.md  few-shot y autocorreccion
  analisis_errores.csv       fallos clasificados por categoria
  prediccion_ex.md           prediccion justificada de la EX oculta
```

## El dataset

2,464 pares generados con 32 plantillas parametricas sobre los 12 esquemas
propios, instanciadas con columnas reales y con umbrales tomados de los datos
(p25, p50, p75) para que los filtros no devuelvan conjuntos vacios.

Se ejecutaron **los 2,464 en MySQL 8.4.10** con un usuario de solo lectura:

| | pares | |
|---|---|---|
| generados | 2,464 | |
| validos | 2,391 | 97.0% |
| descartados | 73 | todos por devolver cero filas |

Quedan 2,320 de entrenamiento (894 faciles, 862 medias, 564 dificiles) y 71 de
dev. Cero errores de sintaxis y cero violaciones de `ONLY_FULL_GROUP_BY`.

Un par cuyo resultado es vacio se descarta a proposito: con cero filas la
comparacion por ejecucion no distingue una consulta correcta de una rota, porque
cualquier error que tambien devuelva vacio "acierta".

La particion es **por esquema**: las bases `veterinaria` y `hotel` de la
validacion no aparecen en el entrenamiento, y no comparten ni un nombre de tabla
con las 12 bases de entrenamiento.

## Requisitos del entorno

- Python 3.11 y GPU T4 (Google Colab) para entrenar.
- MySQL 8.4.10 con la configuracion por defecto. Imagen `mysql:8.4.10` de Docker,
  o el binario oficial para Linux en Colab.
- No se usan APIs externas al generar la consulta.

## Licencias

| Recurso | Licencia |
|---|---|
| Qwen/Qwen2.5-Coder-1.5B-Instruct | Apache 2.0 |
| Codigo de este repositorio | MIT |

El dataset de entrenamiento es propio: los 12 esquemas, los datos y las 2,464
preguntas se generaron para este proyecto. No se usaron Spider ni BIRD, asi que
no aplican sus licencias.

## Uso de IA

Se uso Claude (Anthropic) como asistente de programacion durante el desarrollo,
en estas tareas:

- redaccion del DDL de los 14 esquemas y del poblador generico de datos;
- implementacion de los scripts de generacion, validacion, entrenamiento y
  evaluacion;
- redaccion de este README y de los documentos de `resultados/`.

Las decisiones de diseno que se documentan en cada archivo (descartar los pares
de resultado vacio, comparar columnas conservando su orden relativo, variar solo
el rank entre las dos configuraciones de LoRA) se tomaron y se revisaron por los
integrantes. **Las 40 preguntas de validacion y sus consultas de referencia se
escribieron a mano**, no se generaron con un modelo, y cada una se verifico
ejecutandola. Todo el codigo se ejecuto y se probo: los scripts no se entregan
sin haber corrido.

No se uso ninguna IA dentro de `solucion.py` ni en la generacion de la consulta
que se evalua: el unico modelo que participa ahi es el Qwen permitido por el
enunciado, con su adapter.

## Documentos del proyecto

- [BITACORA.md](BITACORA.md) — entradas fechadas por autor
- [CONTRIBUCIONES.md](CONTRIBUCIONES.md) — tarea, responsable y evidencia
- `historial_git.txt` — salida de `git log --all --date=iso --stat`

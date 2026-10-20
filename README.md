# Proyecto 3 — Text-to-SQL con LoRA

Fine-tuning de `Qwen/Qwen2.5-Coder-1.5B-Instruct` con LoRA para traducir preguntas en
espanol a consultas MySQL 8.4.10, dado el esquema de la base en formato `SHOW CREATE TABLE`.

Universidad del Valle — Deep Learning 2026 — Kevin Recinos.

**Integrantes:** Cindy Gualim · _(pendiente: nombre del segundo integrante)_

## Ejecucion rapida

```bash
pip install -r requirements.txt
```

```python
from solucion import generar_sql

esquema = open("datos/validacion/esquemas/biblioteca.sql").read()
sql = generar_sql(esquema, "Cuantos libros se prestaron en 2025?")
print(sql)
```

`generar_sql(esquema, pregunta, ejecutar=None)` devuelve **una sola** consulta
`SELECT` o `WITH ... SELECT`. El parametro opcional `ejecutar(sql)` se usa, cuando el
evaluador lo entrega, para verificar y corregir la consulta (maximo 3 llamadas por
pregunta). La generacion es determinista (`do_sample=False`, semilla 2026).

## Configuracion

`config.json` controla que modelo se carga:

```json
{
  "modelo_base": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
  "adapter": "adapter/",
  "usar_adapter": true,
  "semilla": 2026
}
```

Con `"usar_adapter": false` se usa el modelo base con el mismo prompt, que es la
version de baseline contra la que se mide el aporte del fine-tuning.

## Estructura del repositorio

```
solucion.py              contrato de entrega: generar_sql()
config.json              modelo base, adapter, semilla
requirements.txt         dependencias verificadas en Colab T4
adapter/                 adapter LoRA entrenado
datos/
  esquemas/              esquemas propios usados para generar el entrenamiento
  entrenamiento.jsonl    pares pregunta-SQL validados en MySQL 8.4.10
  descartes.csv          pares rechazados con su motivo
  validacion/            esquemas y preguntas del validation set propio
notebooks/
  01_datos.ipynb         generacion del dataset
  02_entrenamiento.ipynb entrenamiento LoRA y curvas de loss
  03_evaluacion.ipynb    baseline, EX con adapter y analisis de errores
resultados/
  validacion_propia.csv  resultados por pregunta en la validacion propia
scripts/                 utilidades de datos, validacion y evaluacion
```

## Requisitos del entorno

- Python 3.11 y GPU T4 (Google Colab) para entrenamiento e inferencia.
- MySQL 8.4.10 con la configuracion por defecto (incluye `ONLY_FULL_GROUP_BY`) para
  validar los pares por ejecucion. Se puede usar la imagen `mysql:8.4.10` de Docker.
- No se usan APIs externas al generar la consulta.

## Licencias

| Recurso | Licencia |
|---|---|
| Qwen/Qwen2.5-Coder-1.5B-Instruct | Apache 2.0 |
| Spider | CC BY-SA 4.0 |
| BIRD | CC BY-SA 4.0 |
| Codigo de este repositorio | MIT |

## Uso de IA

_(pendiente: se documenta al cierre del proyecto — herramientas usadas, en que
partes y con que supervision)_

## Documentos del proyecto

- [BITACORA.md](BITACORA.md) — entradas fechadas por autor
- [CONTRIBUCIONES.md](CONTRIBUCIONES.md) — tarea, responsable y evidencia
- `historial_git.txt` — `git log --all --date=iso --stat`

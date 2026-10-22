"""Pruebas de extraer_sql, la funcion que limpia lo que genera el modelo.

Son las unicas salidas del modelo que podemos controlar: si el modelo escribe
explicaciones, bloques markdown o algo que modifique la base, el evaluador igual
recibe una sola consulta de lectura.

    python scripts/test_extraccion.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from solucion import extraer_sql  # noqa: E402

CASOS = [
    ("consulta limpia",
     "SELECT COUNT(*) AS total FROM mascotas",
     "SELECT COUNT(*) AS total FROM mascotas"),

    ("bloque markdown",
     "```sql\nSELECT nombre FROM duenos\n```",
     "SELECT nombre FROM duenos"),

    ("con punto y coma",
     "SELECT nombre FROM duenos;",
     "SELECT nombre FROM duenos"),

    ("explicacion antes",
     "Claro, aqui tienes la consulta:\nSELECT id FROM rooms",
     "SELECT id FROM rooms"),

    ("explicacion despues",
     "SELECT id FROM rooms\n\nEsta consulta devuelve todas las habitaciones.",
     "SELECT id FROM rooms"),

    ("dos sentencias",
     "SELECT 1 FROM t; DROP TABLE t",
     "SELECT 1 FROM t"),

    ("empieza con WITH",
     "WITH x AS (SELECT 1 AS a) SELECT a FROM x",
     "WITH x AS (SELECT 1 AS a) SELECT a FROM x"),

    ("sentencia de escritura",
     "DELETE FROM mascotas WHERE id = 1",
     "SELECT 1"),

    ("salida vacia",
     "",
     "SELECT 1"),

    ("solo texto",
     "No puedo responder esa pregunta.",
     "SELECT 1"),

    ("espacios de sobra",
     "SELECT   nombre,    peso_kg   FROM   mascotas",
     "SELECT nombre, peso_kg FROM mascotas"),
]


def main():
    fallos = 0
    for nombre, entrada, esperado in CASOS:
        obtenido = extraer_sql(entrada)
        ok = obtenido == esperado
        fallos += not ok
        print("%-24s %s" % (nombre, "ok" if ok else "FALLA"))
        if not ok:
            print("   esperado: %r" % esperado)
            print("   obtenido: %r" % obtenido)
    print("\n%d/%d casos correctos" % (len(CASOS) - fallos, len(CASOS)))
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())

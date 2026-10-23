"""Pruebas de coincide(), el criterio con el que se mide la EX.

Si esta funcion se equivoca, todos los numeros del reporte se equivocan con
ella, asi que se prueba cada regla del enunciado por separado.

    python scripts/test_comparacion.py
"""

import datetime
import decimal
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from evaluar import coincide  # noqa: E402

D = decimal.Decimal

CASOS = [
    # (nombre, referencia, prediccion, orden_importa, esperado)
    ("identicas", [(1, "a")], [(1, "a")], False, True),

    ("columna adicional no penaliza",
     [("a", 2)], [("a", 2, "extra")], False, True),

    ("columna adicional al inicio",
     [("a", 2)], [("extra", "a", 2)], False, True),

    ("falta una columna",
     [("a", 2)], [("a",)], False, False),

    ("columnas invertidas cuentan como error",
     [("a", 2)], [(2, "a")], False, False),

    ("orden de filas libre cuando no se pide",
     [(1,), (2,)], [(2,), (1,)], False, True),

    ("orden de filas cuenta cuando se pide",
     [(1,), (2,)], [(2,), (1,)], True, False),

    ("orden correcto cuando se pide",
     [(2,), (1,)], [(2,), (1,)], True, True),

    ("entero contra decimal",
     [(60,)], [(D("60.00"),)], False, True),

    ("redondeo a 2 decimales",
     [(D("10.126"),)], [(10.13,)], False, True),

    ("diferencia mas alla del segundo decimal",
     [(D("10.10"),)], [(10.19,)], False, False),

    ("distinto numero de filas",
     [(1,), (2,)], [(1,)], False, False),

    ("valores distintos",
     [("a",)], [("b",)], False, False),

    ("fecha contra texto de fecha",
     [(datetime.date(2025, 3, 1),)], [("2025-03-01",)], False, True),

    ("nulos",
     [(None, 1)], [(None, 1)], False, True),

    ("nulo contra cero",
     [(None,)], [(0,)], False, False),

    ("prediccion que fallo",
     [(1,)], None, False, False),

    ("ambas vacias",
     [], [], False, True),

    ("filas repetidas se cuentan",
     [(1,), (1,)], [(1,), (2,)], False, False),

    ("extra columna con orden exigido",
     [("a", 2), ("b", 1)], [("a", 2, 9), ("b", 1, 8)], True, True),
]


def main():
    fallos = 0
    for nombre, ref, pred, orden, esperado in CASOS:
        obtenido = coincide(ref, pred, orden)
        ok = obtenido == esperado
        fallos += not ok
        print("%-38s %s" % (nombre, "ok" if ok else "FALLA (esperaba %s)" % esperado))
    print("\n%d/%d casos correctos" % (len(CASOS) - fallos, len(CASOS)))
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())

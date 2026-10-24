"""Clasifica los fallos de una corrida en las categorias que pide el enunciado.

    sintaxis            la consulta no parsea
    tabla_inexistente   usa una tabla que no esta en el esquema
    columna_inexistente usa una columna que no existe o que no pertenece a la tabla
    join                relaciona mal las tablas: falta un JOIN, sobra, o la clave es otra
    agregacion          error de GROUP BY, de funcion agregada o de ONLY_FULL_GROUP_BY
    filtro              las condiciones del WHERE o del HAVING no son las pedidas
    resultado_distinto  la consulta corre y es plausible, pero el resultado no coincide

Las dos primeras familias se deducen del codigo de error de MySQL; las demas,
comparando la forma de la consulta generada contra la de referencia.

Uso:
    python scripts/analizar_errores.py --etiqueta adapter
"""

import argparse
import collections
import csv
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent

CODIGOS = [
    (r"\b1064\b|You have an error in your SQL syntax", "sintaxis"),
    (r"\b1146\b|Table '.*' doesn't exist", "tabla_inexistente"),
    (r"\b1054\b|Unknown column", "columna_inexistente"),
    (r"\b1055\b|only_full_group_by", "agregacion"),
    (r"\b1111\b|Invalid use of group function", "agregacion"),
    (r"\b1052\b|Column '.*' in .* is ambiguous", "join"),
    (r"\b1066\b|Not unique table", "join"),
    (r"\b1140\b", "agregacion"),
    (r"\b3065\b|ORDER BY clause is not in SELECT list", "agregacion"),
    (r"limite de 3 llamadas", "resultado_distinto"),
]

AGREGADOS = re.compile(r"\b(count|sum|avg|min|max)\s*\(", re.IGNORECASE)
VENTANA = re.compile(r"\bover\s*\(", re.IGNORECASE)


def tablas_de(sql):
    """Tablas que menciona una consulta, por FROM y por JOIN."""
    encontradas = re.findall(r"\b(?:from|join)\s+`?(\w+)`?", sql, flags=re.IGNORECASE)
    return {t.lower() for t in encontradas}


def condiciones_de(sql):
    """Texto del WHERE y del HAVING, normalizado."""
    partes = []
    for palabra in ("where", "having"):
        for trozo in re.findall(
            r"\b%s\b(.*?)(?=\b(?:group by|order by|limit|having|window)\b|$)" % palabra,
            sql, flags=re.IGNORECASE | re.DOTALL,
        ):
            partes.append(re.sub(r"\s+", " ", trozo).strip().lower())
    return partes


def clasificar(fila):
    error = (fila.get("error") or "").strip()
    generado = fila["sql_generado"]
    referencia = fila["sql_referencia"]

    if error:
        for patron, categoria in CODIGOS:
            if re.search(patron, error, flags=re.IGNORECASE):
                return categoria
        return "sintaxis"

    # La consulta corre pero el resultado no coincide: se compara su forma.
    if tablas_de(generado) != tablas_de(referencia):
        return "join"

    agr_gen = bool(AGREGADOS.search(generado)) or bool(VENTANA.search(generado))
    agr_ref = bool(AGREGADOS.search(referencia)) or bool(VENTANA.search(referencia))
    group_gen = "group by" in generado.lower()
    group_ref = "group by" in referencia.lower()
    if agr_gen != agr_ref or group_gen != group_ref:
        return "agregacion"

    if condiciones_de(generado) != condiciones_de(referencia):
        return "filtro"

    return "resultado_distinto"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", default="resultados/validacion_propia.csv")
    parser.add_argument("--etiqueta", default=None,
                        help="Analiza solo esa corrida; por defecto, todas")
    parser.add_argument("--salida", default="resultados/analisis_errores.csv")
    args = parser.parse_args()

    with open(RAIZ / args.entrada, encoding="utf-8", newline="") as fh:
        filas = list(csv.DictReader(fh))
    if args.etiqueta:
        filas = [f for f in filas if f["etiqueta"] == args.etiqueta]
    if not filas:
        raise SystemExit("no hay filas que analizar en %s" % args.entrada)

    fallos = [f for f in filas if f["ok"] == "0"]
    for f in fallos:
        f["categoria"] = clasificar(f)

    campos = ["etiqueta", "id", "base", "nivel", "peso", "categoria",
              "pregunta", "sql_referencia", "sql_generado", "error"]
    destino = RAIZ / args.salida
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8", newline="") as fh:
        escritor = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(fallos)

    por_etiqueta = collections.defaultdict(collections.Counter)
    for f in fallos:
        por_etiqueta[f["etiqueta"]][f["categoria"]] += 1
    total_por_etiqueta = collections.Counter(f["etiqueta"] for f in filas)

    for etiqueta, cuenta in sorted(por_etiqueta.items()):
        fallidas = sum(cuenta.values())
        print("\n%s: %d fallos de %d preguntas" % (etiqueta, fallidas,
                                                   total_por_etiqueta[etiqueta]))
        for categoria, n in cuenta.most_common():
            print("  %-20s %2d  (%.0f%% de los fallos)" % (categoria, n, 100 * n / fallidas))

    # Peso perdido: lo que cuesta cada categoria en la metrica, que no es lo
    # mismo que cuantas preguntas falla.
    print("\npeso perdido por categoria")
    peso = collections.Counter()
    for f in fallos:
        peso[f["categoria"]] += int(f["peso"])
    for categoria, p in peso.most_common():
        print("  %-20s %3d" % (categoria, p))
    print("\ndetalle en %s" % destino)


if __name__ == "__main__":
    main()

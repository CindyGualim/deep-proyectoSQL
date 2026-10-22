"""Valida los pares generados ejecutandolos en MySQL 8.4.10.

Solo sobreviven los pares cuya consulta se ejecuta sin error y devuelve un
resultado util. El enunciado pide reportar cuantos pares se descartan y por que,
asi que cada descarte queda registrado con su motivo en datos/descartes.csv.

Motivos de descarte:

    error_sql          la consulta falla en el motor
    resultado_vacio    se ejecuta pero no devuelve filas
    resultado_nulo     devuelve una sola celda con NULL
    limit_sin_orden    usa LIMIT sin ORDER BY, el resultado no es determinista
    sql_duplicado      otra pregunta ya produjo exactamente la misma consulta
    pregunta_duplicada la misma pregunta ya aparece con otra consulta
    no_es_select       no empieza por SELECT ni por WITH

Salidas:
    datos/entrenamiento.jsonl          pares validos
    datos/dev.jsonl                    muestra para vigilar la loss al entrenar
    datos/esquemas_show_create.json    esquema de cada base, como lo ve el modelo
    datos/descartes.csv                un renglon por par descartado
    resultados/descartes_resumen.csv   conteo por motivo y nivel

Uso:
    MYSQL_USER=lector MYSQL_PASSWORD=lector python scripts/validar_pares.py
"""

import argparse
import collections
import csv
import json
import pathlib
import random
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import db  # noqa: E402

SEMILLA = 2026
LIMITE_MS = 5000


def normalizar(sql):
    return re.sub(r"\s+", " ", sql.strip().lower()).rstrip(";")


def revisar_forma(sql):
    """Descartes que no requieren tocar la base."""
    limpio = sql.strip().lower()
    if not (limpio.startswith("select") or limpio.startswith("with")):
        return "no_es_select", "la consulta no empieza por SELECT ni WITH"
    if " limit " in (" " + limpio + " ") and "order by" not in limpio:
        return "limit_sin_orden", "LIMIT sin ORDER BY produce filas arbitrarias"
    return None, ""


def ejecutar(cur, base, sql):
    cur.execute("USE `%s`" % base)
    cur.execute(sql)
    return cur.fetchall(), [d[0] for d in cur.description]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", default="datos/pares_crudos.jsonl")
    parser.add_argument("--salida", default="datos/entrenamiento.jsonl")
    parser.add_argument("--dev", type=float, default=0.03,
                        help="Fraccion de pares reservados para vigilar la loss")
    args = parser.parse_args()

    pares = [json.loads(l) for l in open(args.entrada, encoding="utf-8")]
    conn = db.conectar()
    cur = conn.cursor()
    cur.execute("SET SESSION max_execution_time = %d" % LIMITE_MS)

    bases = sorted({p["base"] for p in pares})
    esquemas = {b: db.show_create(conn, b) for b in bases}

    validos, descartes = [], []
    sql_vistos, preguntas_vistas = set(), set()

    for par in pares:
        motivo, detalle = revisar_forma(par["sql"])

        if motivo is None:
            clave_sql = (par["base"], normalizar(par["sql"]))
            clave_pregunta = (par["base"], par["pregunta"].strip().lower())
            if clave_sql in sql_vistos:
                motivo, detalle = "sql_duplicado", "consulta repetida en la misma base"
            elif clave_pregunta in preguntas_vistas:
                motivo, detalle = "pregunta_duplicada", "pregunta repetida con otra consulta"

        filas, columnas = [], []
        if motivo is None:
            try:
                filas, columnas = ejecutar(cur, par["base"], par["sql"])
            except Exception as exc:  # noqa: BLE001 - el motivo se reporta tal cual
                motivo, detalle = "error_sql", str(exc)[:200]

        if motivo is None:
            if not filas:
                motivo, detalle = "resultado_vacio", "la consulta devuelve 0 filas"
            elif len(filas) == 1 and len(filas[0]) == 1 and filas[0][0] is None:
                motivo, detalle = "resultado_nulo", "la consulta devuelve una sola celda NULL"

        if motivo is not None:
            descartes.append({**par, "motivo": motivo, "detalle": detalle})
            continue

        sql_vistos.add((par["base"], normalizar(par["sql"])))
        preguntas_vistas.add((par["base"], par["pregunta"].strip().lower()))
        validos.append(
            {"base": par["base"], "nivel": par["nivel"], "plantilla": par["plantilla"],
             "pregunta": par["pregunta"], "sql": par["sql"],
             "filas_resultado": len(filas), "columnas_resultado": len(columnas)}
        )

    conn.close()

    # Particion interna solo para vigilar la loss: la validacion que cuenta se
    # hace sobre esquemas que no aparecen aqui (datos/validacion).
    rng = random.Random(SEMILLA)
    rng.shuffle(validos)
    corte = int(len(validos) * args.dev)
    dev, entrenamiento = validos[:corte], validos[corte:]
    entrenamiento.sort(key=lambda p: (p["base"], p["nivel"], p["plantilla"]))

    _escribir_jsonl(args.salida, entrenamiento)
    _escribir_jsonl("datos/dev.jsonl", dev)
    pathlib.Path("datos/esquemas_show_create.json").write_text(
        json.dumps(esquemas, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    with open("datos/descartes.csv", "w", encoding="utf-8", newline="") as fh:
        campos = ["base", "nivel", "plantilla", "motivo", "detalle", "pregunta", "sql"]
        escritor = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(descartes)

    _resumen(pares, entrenamiento, dev, descartes)


def _escribir_jsonl(ruta, registros):
    destino = pathlib.Path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8") as fh:
        for registro in registros:
            fh.write(json.dumps(registro, ensure_ascii=False) + "\n")


def _resumen(pares, entrenamiento, dev, descartes):
    por_motivo = collections.Counter(d["motivo"] for d in descartes)
    por_nivel = collections.Counter(p["nivel"] for p in entrenamiento)

    print("pares generados      %5d" % len(pares))
    print("pares validos        %5d (%.1f%%)"
          % (len(entrenamiento) + len(dev),
             100 * (len(entrenamiento) + len(dev)) / max(1, len(pares))))
    print("  entrenamiento      %5d" % len(entrenamiento))
    print("  dev interno        %5d" % len(dev))
    print("pares descartados    %5d" % len(descartes))
    for motivo, n in por_motivo.most_common():
        print("  %-18s %5d" % (motivo, n))
    print("\nniveles en entrenamiento")
    for nivel in ("facil", "media", "dificil"):
        print("  %-8s %5d (%.0f%%)"
              % (nivel, por_nivel[nivel],
                 100 * por_nivel[nivel] / max(1, len(entrenamiento))))

    pathlib.Path("resultados").mkdir(exist_ok=True)
    with open("resultados/descartes_resumen.csv", "w", encoding="utf-8", newline="") as fh:
        escritor = csv.writer(fh)
        escritor.writerow(["motivo", "pares", "porcentaje_de_generados"])
        for motivo, n in por_motivo.most_common():
            escritor.writerow([motivo, n, round(100 * n / max(1, len(pares)), 2)])
        escritor.writerow(["TOTAL_DESCARTADOS", len(descartes),
                           round(100 * len(descartes) / max(1, len(pares)), 2)])
        escritor.writerow(["TOTAL_VALIDOS", len(entrenamiento) + len(dev),
                           round(100 * (len(entrenamiento) + len(dev)) / max(1, len(pares)), 2)])


if __name__ == "__main__":
    main()

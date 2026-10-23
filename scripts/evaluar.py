"""Evalua una version del modelo sobre la validacion propia, con exactitud por ejecucion.

La comparacion replica el criterio de la evaluacion oculta:

  - se comparan los resultados de ejecutar las consultas, nunca su texto;
  - el orden de las filas solo cuenta si la pregunta lo pide;
  - los numeros se redondean a 2 decimales;
  - una columna adicional no penaliza, siempre que las columnas pedidas
    aparezcan y en el orden en que se pidieron.

Metrica: EX ponderada, la suma de los pesos de las preguntas acertadas entre la
suma de todos los pesos (facil 1, media 2, dificil 3).

Uso:
    python scripts/evaluar.py --etiqueta baseline --sin-adapter
    python scripts/evaluar.py --etiqueta adapter
"""

import argparse
import collections
import csv
import datetime
import decimal
import itertools
import json
import pathlib
import sys
import time

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

import db  # noqa: E402

LIMITE_MS = 10000


# --------------------------------------------------------------------------
# Comparacion de resultados
# --------------------------------------------------------------------------

def normalizar(valor):
    """Lleva una celda a una forma comparable entre dos consultas distintas."""
    if valor is None:
        return None
    if isinstance(valor, bool):
        return int(valor)
    if isinstance(valor, decimal.Decimal):
        return round(float(valor), 2)
    if isinstance(valor, float):
        return round(valor, 2)
    if isinstance(valor, int):
        return round(float(valor), 2)
    if isinstance(valor, (datetime.date, datetime.datetime)):
        return valor.isoformat()
    if isinstance(valor, datetime.timedelta):
        return str(valor)
    if isinstance(valor, (bytes, bytearray)):
        return valor.decode("utf-8", "replace").strip()
    return str(valor).strip()


def normalizar_filas(filas):
    return [tuple(normalizar(v) for v in fila) for fila in filas]


def _clave(fila):
    return tuple((v is None, str(v)) for v in fila)


def coincide(referencia, prediccion, orden_importa):
    """True si la prediccion contiene lo que pide la referencia.

    Se prueban las combinaciones de columnas de la prediccion que conservan el
    orden relativo pedido: asi una columna de mas no penaliza, pero devolver
    las columnas al reves si cuenta como error.
    """
    if referencia is None or prediccion is None:
        return False
    if len(referencia) != len(prediccion):
        return False
    if not referencia:
        return True

    ref = normalizar_filas(referencia)
    pred = normalizar_filas(prediccion)
    n_ref, n_pred = len(ref[0]), len(pred[0])
    if n_pred < n_ref:
        return False

    objetivo = ref if orden_importa else sorted(ref, key=_clave)
    for indices in itertools.combinations(range(n_pred), n_ref):
        proyeccion = [tuple(fila[j] for j in indices) for fila in pred]
        if not orden_importa:
            proyeccion = sorted(proyeccion, key=_clave)
        if proyeccion == objetivo:
            return True
    return False


# --------------------------------------------------------------------------
# Ejecucion
# --------------------------------------------------------------------------

def ejecutar(cur, base, sql):
    cur.execute("USE `%s`" % base)
    cur.execute(sql)
    return cur.fetchall()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preguntas", default="datos/validacion/preguntas.jsonl")
    parser.add_argument("--esquemas", default="datos/validacion/esquemas_show_create.json")
    parser.add_argument("--etiqueta", default="adapter",
                        help="Nombre de la corrida, va en el CSV y en el resumen")
    parser.add_argument("--sin-adapter", action="store_true",
                        help="Fuerza usar_adapter=false: es la corrida de baseline")
    parser.add_argument("--modelo", default=None,
                        help="Sobreescribe modelo_base, solo para pruebas")
    parser.add_argument("--adapter", default=None,
                        help="Carpeta del adapter a evaluar, por ejemplo adapter_r32")
    parser.add_argument("--few-shot", action="store_true",
                        help="Agrega los tres ejemplos resueltos al prompt")
    parser.add_argument("--autocorreccion", action="store_true",
                        help="Entrega `ejecutar` al modelo para que corrija su consulta")
    parser.add_argument("--salida", default="resultados/validacion_propia.csv")
    args = parser.parse_args()

    import solucion

    if args.sin_adapter:
        solucion.CONFIG["usar_adapter"] = False
    if args.modelo:
        solucion.CONFIG["modelo_base"] = args.modelo
    if args.adapter:
        solucion.CONFIG["adapter"] = args.adapter
        solucion.CONFIG["usar_adapter"] = True
    solucion.CONFIG["few_shot"] = args.few_shot
    solucion.CONFIG["autocorreccion"] = args.autocorreccion

    preguntas = [json.loads(l) for l in open(RAIZ / args.preguntas, encoding="utf-8")]
    esquemas = json.loads((RAIZ / args.esquemas).read_text(encoding="utf-8"))

    t0 = time.time()
    solucion.cargar_modelo()
    print("carga del modelo: %.1f s\n" % (time.time() - t0))

    conn = db.conectar()
    cur = conn.cursor()
    cur.execute("SET SESSION max_execution_time = %d" % LIMITE_MS)

    registros = []
    for q in preguntas:
        llamadas = [0]

        def ejecutar_para_el_modelo(consulta, base=q["base"], contador=llamadas):
            """Replica el `ejecutar` que entrega el evaluador: solo lectura,
            hasta 10 filas y un maximo de 3 llamadas por pregunta."""
            if contador[0] >= 3:
                return {"ok": False, "columnas": [], "filas": [],
                        "error": "limite de 3 llamadas alcanzado"}
            contador[0] += 1
            try:
                filas = ejecutar(cur, base, consulta)
                nombres = [d[0] for d in cur.description]
                return {"ok": True, "columnas": nombres, "filas": list(filas[:10]),
                        "error": None}
            except Exception as exc:  # noqa: BLE001
                return {"ok": False, "columnas": [], "filas": [], "error": str(exc)[:300]}

        inicio = time.time()
        try:
            sql = solucion.generar_sql(
                esquemas[q["base"]], q["pregunta"],
                ejecutar=ejecutar_para_el_modelo if args.autocorreccion else None)
            fallo_generacion = ""
        except Exception as exc:  # noqa: BLE001
            sql, fallo_generacion = "SELECT 1", str(exc)[:200]
        segundos = time.time() - inicio

        try:
            esperado = ejecutar(cur, q["base"], q["sql_referencia"])
        except Exception as exc:  # noqa: BLE001
            raise SystemExit("la consulta de referencia %d no corre: %s" % (q["id"], exc))

        error = fallo_generacion
        try:
            obtenido = ejecutar(cur, q["base"], sql)
        except Exception as exc:  # noqa: BLE001
            obtenido, error = None, str(exc)[:200]

        ok = coincide(esperado, obtenido, q["orden_importa"])
        registros.append(
            {"etiqueta": args.etiqueta, "id": q["id"], "base": q["base"],
             "nivel": q["nivel"], "peso": q["peso"], "orden_importa": q["orden_importa"],
             "pregunta": q["pregunta"], "sql_referencia": q["sql_referencia"],
             "sql_generado": sql, "ok": int(ok), "segundos": round(segundos, 2),
             "llamadas_ejecutar": llamadas[0], "error": error}
        )
        print("%2d %-11s %-7s %s %5.1fs %s"
              % (q["id"], q["base"], q["nivel"], "ok   " if ok else "FALLA",
                 segundos, (error[:60] if error else "")))

    conn.close()
    _guardar(RAIZ / args.salida, registros, args.etiqueta)
    _resumen(registros, args.etiqueta)


def _guardar(ruta, registros, etiqueta):
    """Acumula corridas en el mismo CSV, reemplazando la de igual etiqueta."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    previos = []
    if ruta.is_file():
        with ruta.open(encoding="utf-8", newline="") as fh:
            previos = [f for f in csv.DictReader(fh) if f.get("etiqueta") != etiqueta]
    campos = list(registros[0])
    with ruta.open("w", encoding="utf-8", newline="") as fh:
        escritor = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(previos + registros)
    print("\nresultados en %s" % ruta)


def _resumen(registros, etiqueta):
    peso_total = sum(r["peso"] for r in registros)
    peso_ok = sum(r["peso"] for r in registros if r["ok"])
    print("\nEX ponderada (%s): %.3f  (%d/%d puntos de peso)"
          % (etiqueta, peso_ok / peso_total, peso_ok, peso_total))

    por_nivel = collections.defaultdict(lambda: [0, 0])
    for r in registros:
        por_nivel[r["nivel"]][0] += r["ok"]
        por_nivel[r["nivel"]][1] += 1
    for nivel in ("facil", "media", "dificil"):
        ok, n = por_nivel[nivel]
        print("  %-8s %2d/%2d  %.0f%%" % (nivel, ok, n, 100 * ok / max(1, n)))

    tiempos = [r["segundos"] for r in registros]
    print("  tiempo por pregunta: media %.1f s, maximo %.1f s (tope 30 s)"
          % (sum(tiempos) / len(tiempos), max(tiempos)))
    con_error = sum(1 for r in registros if r["error"])
    print("  consultas que no ejecutan: %d/%d" % (con_error, len(registros)))


if __name__ == "__main__":
    main()

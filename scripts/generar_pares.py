"""Genera pares pregunta-SQL por plantillas sobre los esquemas propios.

Cada plantilla se instancia con tablas, columnas y valores reales tomados de la
base: los valores de los filtros salen de una muestra de filas, de modo que las
consultas devuelven resultados no vacios y la verificacion del commit siguiente
es informativa.

Las plantillas cubren los tres niveles de la evaluacion oculta:

    facil    una sola tabla
    media    JOIN, GROUP BY, HAVING
    dificil  subconsultas, WITH, funciones de ventana, fechas

Salida: datos/pares_crudos.jsonl. Todavia sin validar contra MySQL; eso lo hace
scripts/validar_pares.py.

Uso:
    python scripts/generar_pares.py --limite 12
"""

import argparse
import collections
import json
import pathlib
import random
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import db  # noqa: E402

SEMILLA = 2026
NUMERICOS = {"int", "bigint", "smallint", "mediumint", "tinyint", "decimal", "float", "double"}
TEXTOS = {"varchar", "char", "text"}
FECHAS = {"date", "datetime", "timestamp"}


# --------------------------------------------------------------------------
# Lectura del esquema y de una muestra de filas
# --------------------------------------------------------------------------

def inspeccionar(conn, base):
    with conn.cursor() as cur:
        cur.execute("USE `%s`" % base)
        cur.execute(
            "SELECT TABLE_NAME, TABLE_COMMENT FROM information_schema.TABLES"
            " WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'",
            (base,),
        )
        comentarios = dict(cur.fetchall())

        cur.execute(
            "SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, COLUMN_COMMENT,"
            "       IS_NULLABLE, COLUMN_KEY, EXTRA"
            "  FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s"
            " ORDER BY TABLE_NAME, ORDINAL_POSITION",
            (base,),
        )
        tablas = {}
        for t, c, tipo, tipo_completo, comentario, nulo, clave, extra in cur.fetchall():
            tablas.setdefault(
                t,
                {"nombre": t, "comentario": comentarios.get(t, ""), "columnas": [],
                 "pk": [], "fks": {}, "muestras": {}},
            )
            tablas[t]["columnas"].append(
                {"nombre": c, "tipo": tipo, "tipo_completo": tipo_completo,
                 "comentario": comentario, "nulo": nulo == "YES", "clave": clave,
                 "auto": "auto_increment" in extra}
            )
            if clave == "PRI":
                tablas[t]["pk"].append(c)

        cur.execute(
            "SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME"
            "  FROM information_schema.KEY_COLUMN_USAGE"
            " WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL",
            (base,),
        )
        relaciones = []
        for hijo, col, padre, col_padre in cur.fetchall():
            tablas[hijo]["fks"][col] = (padre, col_padre)
            if padre != hijo:
                relaciones.append((hijo, col, padre, col_padre))

        for t in tablas:
            cur.execute("SELECT * FROM `%s` LIMIT 80" % t)
            nombres = [d[0] for d in cur.description]
            filas = cur.fetchall()
            for i, nombre in enumerate(nombres):
                tablas[t]["muestras"][nombre] = [f[i] for f in filas if f[i] is not None]

    return {"base": base, "tablas": tablas, "relaciones": relaciones}


# --------------------------------------------------------------------------
# Selectores sobre el esquema
# --------------------------------------------------------------------------

def es_bool(c):
    return c["tipo_completo"].startswith("tinyint(1)")


def numericas(t):
    return [
        c for c in t["columnas"]
        if c["tipo"] in NUMERICOS and not es_bool(c) and not c["auto"]
        and c["nombre"] not in t["fks"] and c["clave"] != "PRI"
        and not c["nombre"].endswith("_id")
    ]


def fechas(t):
    return [c for c in t["columnas"] if c["tipo"] in FECHAS]


def enums(t):
    return [c for c in t["columnas"] if c["tipo"] == "enum"]


def booleanas(t):
    return [c for c in t["columnas"] if es_bool(c)]


def textos(t):
    return [
        c for c in t["columnas"]
        if c["tipo"] in TEXTOS and c["nombre"] not in t["fks"]
    ]


def etiqueta(t):
    """Columna que identifica una fila al mostrarla (nombre, titulo, codigo...)."""
    candidatas = textos(t)
    for patron in (r"nombre|titulo|name|nm$|razon_social|desc_", r"codigo|sku|guia|numero"):
        for c in candidatas:
            if re.search(patron, c["nombre"]):
                return c["nombre"]
    if candidatas:
        return candidatas[0]["nombre"]
    return t["pk"][0] if t["pk"] else t["columnas"][0]["nombre"]


def _redondear(c, v):
    if c["tipo"] in ("int", "bigint", "smallint", "mediumint", "tinyint"):
        return int(v)
    return round(v, 2)


def muestra_num(t, c):
    valores = [float(v) for v in t["muestras"].get(c["nombre"], []) if v is not None]
    if len(valores) < 5:
        return None
    valores.sort()
    return _redondear(c, valores[len(valores) // 2])


def cuantiles(t, c):
    """Tres umbrales tomados de los datos reales: p25, p50 y p75.

    Variar el umbral multiplica los pares sin repetir la consulta, y mantiene
    los resultados no vacios porque los valores existen en la tabla.
    """
    valores = [float(v) for v in t["muestras"].get(c["nombre"], []) if v is not None]
    if len(valores) < 5:
        return []
    valores.sort()
    n = len(valores)
    vistos, salida = set(), []
    for pos in (n // 4, n // 2, (3 * n) // 4):
        v = _redondear(c, valores[pos])
        if v not in vistos:
            vistos.add(v)
            salida.append(v)
    return salida


def muestra_txt(t, c):
    valores = [v for v in t["muestras"].get(c["nombre"], []) if isinstance(v, str)]
    return valores[len(valores) // 2] if valores else None


def valores_enum(c):
    return re.findall(r"'([^']*)'", c["tipo_completo"])


def anios(t, c):
    vistos = {v.year for v in t["muestras"].get(c["nombre"], []) if hasattr(v, "year")}
    return sorted(vistos)


def legible(nombre):
    return nombre.replace("_", " ")


def etiqueta_col(c):
    """Nombre en lenguaje natural de una columna, tomado de su COMMENT."""
    comentario = (c["comentario"] or "").strip().rstrip(".")
    if comentario:
        corto = ", ".join(comentario.split(", ")[:1])
        palabras = corto.split()
        if 1 <= len(palabras) <= 7:
            return corto[0].lower() + corto[1:]
    return legible(c["nombre"])


def frase(rng, *variantes):
    return rng.choice(variantes)


def cardinal(t):
    """Como se nombra en plural el contenido de una tabla."""
    return legible(t["nombre"])


# --------------------------------------------------------------------------
# Plantillas: nivel facil (una sola tabla)
# --------------------------------------------------------------------------

def f_conteo_total(esq, rng):
    for t in esq["tablas"].values():
        yield frase(
            rng,
            "Cuantos registros hay en la tabla %s? Devuelve solo el total." % t["nombre"],
            "Cuenta cuantas filas tiene %s y devuelve el total." % t["nombre"],
            "Cual es el numero total de %s? Devuelve unicamente la cantidad." % cardinal(t),
        ), "SELECT COUNT(*) AS total FROM %s" % t["nombre"]


def f_filtro_numerico(esq, rng):
    for t in esq["tablas"].values():
        etq = etiqueta(t)
        for c in numericas(t):
            for v in cuantiles(t, c):
                yield frase(
                    rng,
                    "Muestra %s y %s de %s donde %s sea mayor que %s."
                    % (etq, c["nombre"], t["nombre"], c["nombre"], v),
                    "Devuelve %s y %s de los %s cuyo %s supere %s."
                    % (etq, c["nombre"], cardinal(t), etiqueta_col(c), v),
                ), "SELECT %s, %s FROM %s WHERE %s > %s" % (
                    etq, c["nombre"], t["nombre"], c["nombre"], v)


def f_top_n(esq, rng):
    for t in esq["tablas"].values():
        etq = etiqueta(t)
        for c in numericas(t):
            if muestra_num(t, c) is None:
                continue
            for n in (3, 5, 10):
                yield frase(
                    rng,
                    "Devuelve %s y %s de los %d %s con mayor %s, ordenados de mayor a "
                    "menor." % (etq, c["nombre"], n, cardinal(t), c["nombre"]),
                    "Cuales son los %d %s con el %s mas alto? Devuelve %s y %s ordenados "
                    "de mayor a menor." % (n, cardinal(t), etiqueta_col(c), etq, c["nombre"]),
                ), "SELECT %s, %s FROM %s ORDER BY %s DESC LIMIT %d" % (
                    etq, c["nombre"], t["nombre"], c["nombre"], n)


def f_filtro_enum(esq, rng):
    for t in esq["tablas"].values():
        for c in enums(t):
            for v in valores_enum(c):
                yield frase(
                    rng,
                    "Cuantos %s tienen %s igual a '%s'? Devuelve solo la cantidad."
                    % (cardinal(t), c["nombre"], v),
                    "Cuenta los registros de %s cuyo %s sea '%s'."
                    % (t["nombre"], c["nombre"], v),
                ), "SELECT COUNT(*) AS total FROM %s WHERE %s = '%s'" % (
                    t["nombre"], c["nombre"], v)


def f_agregado_simple(esq, rng):
    etiquetas = {"AVG": "el promedio", "SUM": "la suma", "MAX": "el valor maximo",
                 "MIN": "el valor minimo"}
    for t in esq["tablas"].values():
        for c in numericas(t):
            if muestra_num(t, c) is None:
                continue
            for agg in etiquetas:
                yield frase(
                    rng,
                    "Cual es %s de %s en %s? Devuelve un solo valor."
                    % (etiquetas[agg], c["nombre"], t["nombre"]),
                    "Calcula %s de %s para todos los %s."
                    % (etiquetas[agg], etiqueta_col(c), cardinal(t)),
                ), "SELECT %s(%s) AS resultado FROM %s" % (agg, c["nombre"], t["nombre"])


def f_distintos(esq, rng):
    for t in esq["tablas"].values():
        for c in (enums(t) + textos(t))[:2]:
            yield frase(
                rng,
                "Lista los valores distintos de %s en %s." % (c["nombre"], t["nombre"]),
                "Que valores diferentes de %s existen en %s? Devuelve solo esa columna."
                % (c["nombre"], t["nombre"]),
            ), "SELECT DISTINCT %s FROM %s" % (c["nombre"], t["nombre"])


def f_anio(esq, rng):
    for t in esq["tablas"].values():
        for c in fechas(t):
            for anio in anios(t, c):
                yield frase(
                    rng,
                    "Cuantos %s tienen %s en el anio %d? Devuelve la cantidad."
                    % (cardinal(t), c["nombre"], anio),
                    "Cuenta los registros de %s cuyo %s sea del anio %d."
                    % (t["nombre"], c["nombre"], anio),
                ), "SELECT COUNT(*) AS total FROM %s WHERE YEAR(%s) = %d" % (
                    t["nombre"], c["nombre"], anio)


def f_booleano(esq, rng):
    for t in esq["tablas"].values():
        etq = etiqueta(t)
        for c in booleanas(t)[:2]:
            yield frase(
                rng,
                "Devuelve %s de los %s donde %s sea 1." % (etq, cardinal(t), c["nombre"]),
                "Muestra %s de %s que tengan %s igual a 1." % (etq, t["nombre"], c["nombre"]),
            ), "SELECT %s FROM %s WHERE %s = 1" % (etq, t["nombre"], c["nombre"])


def f_nulos(esq, rng):
    for t in esq["tablas"].values():
        opcionales = [c for c in t["columnas"] if c["nulo"] and c["nombre"] not in t["fks"]]
        for c in opcionales[:2]:
            yield frase(
                rng,
                "Cuantos %s no tienen valor en %s? Devuelve la cantidad."
                % (cardinal(t), c["nombre"]),
                "Cuenta los registros de %s donde %s esta vacio." % (t["nombre"], c["nombre"]),
            ), "SELECT COUNT(*) AS total FROM %s WHERE %s IS NULL" % (
                t["nombre"], c["nombre"])


def f_rango_fecha(esq, rng):
    for t in esq["tablas"].values():
        etq = etiqueta(t)
        for c in fechas(t)[:1]:
            disponibles = anios(t, c)
            if not disponibles:
                continue
            anio = rng.choice(disponibles)
            yield frase(
                rng,
                "Devuelve %s y %s de los %s registrados entre el 1 de enero de %d y el "
                "30 de junio de %d." % (etq, c["nombre"], cardinal(t), anio, anio),
                "Muestra %s y %s de %s con %s en el primer semestre de %d."
                % (etq, c["nombre"], t["nombre"], c["nombre"], anio),
            ), "SELECT %s, %s FROM %s WHERE %s >= '%d-01-01' AND %s < '%d-07-01'" % (
                etq, c["nombre"], t["nombre"], c["nombre"], anio, c["nombre"], anio)


def f_texto_like(esq, rng):
    for t in esq["tablas"].values():
        for c in textos(t)[:2]:
            v = muestra_txt(t, c)
            if not v or len(v) < 2:
                continue
            prefijo = v[0]
            yield frase(
                rng,
                "Devuelve %s de %s cuyo %s empiece con la letra '%s'."
                % (c["nombre"], t["nombre"], c["nombre"], prefijo),
                "Muestra los valores de %s en %s que comienzan con '%s'."
                % (c["nombre"], t["nombre"], prefijo),
            ), "SELECT %s FROM %s WHERE %s LIKE '%s%%'" % (
                c["nombre"], t["nombre"], c["nombre"], prefijo)


# --------------------------------------------------------------------------
# Plantillas: nivel medio (JOIN, GROUP BY, HAVING)
# --------------------------------------------------------------------------

def m_conteo_por_padre(esq, rng):
    for hijo, col, padre, col_padre in esq["relaciones"]:
        tp = esq["tablas"][padre]
        etq = etiqueta(tp)
        yield frase(
            rng,
            "Cuantos %s tiene cada %s? Devuelve %s y la cantidad."
            % (legible(hijo), legible(padre), etq),
            "Para cada %s, cuenta sus %s. Devuelve %s y el total."
            % (legible(padre), legible(hijo), etq),
        ), (
            "SELECT p.%s, COUNT(*) AS total FROM %s h JOIN %s p ON h.%s = p.%s "
            "GROUP BY p.%s, p.%s" % (etq, hijo, padre, col, col_padre, col_padre, etq)
        )


def m_suma_por_padre(esq, rng):
    for hijo, col, padre, col_padre in esq["relaciones"]:
        th, tp = esq["tablas"][hijo], esq["tablas"][padre]
        etq = etiqueta(tp)
        for c in numericas(th):
            if muestra_num(th, c) is None:
                continue
            yield frase(
                rng,
                "Devuelve %s de %s y la suma de %s de sus %s."
                % (etq, legible(padre), c["nombre"], legible(hijo)),
                "Para cada %s, calcula el total de %s en %s. Devuelve %s y la suma."
                % (legible(padre), c["nombre"], legible(hijo), etq),
            ), (
                "SELECT p.%s, SUM(h.%s) AS total FROM %s h JOIN %s p ON h.%s = p.%s "
                "GROUP BY p.%s, p.%s"
                % (etq, c["nombre"], hijo, padre, col, col_padre, col_padre, etq)
            )


def m_promedio_por_enum(esq, rng):
    for t in esq["tablas"].values():
        for e in enums(t):
            for c in numericas(t):
                if muestra_num(t, c) is None:
                    continue
                yield frase(
                    rng,
                    "Cual es el promedio de %s por %s en %s? Devuelve %s y el promedio "
                    "redondeado a 2 decimales."
                    % (c["nombre"], e["nombre"], t["nombre"], e["nombre"]),
                    "Agrupa %s por %s y devuelve %s junto al promedio de %s redondeado "
                    "a 2 decimales." % (t["nombre"], e["nombre"], e["nombre"], c["nombre"]),
                ), (
                    "SELECT %s, ROUND(AVG(%s), 2) AS promedio FROM %s GROUP BY %s"
                    % (e["nombre"], c["nombre"], t["nombre"], e["nombre"])
                )


def m_having(esq, rng):
    for hijo, col, padre, col_padre in esq["relaciones"]:
        tp = esq["tablas"][padre]
        etq = etiqueta(tp)
        for n in (2, 3, 5):
            yield frase(
                rng,
                "Devuelve %s y la cantidad de %s, solo para los %s que tengan mas de %d."
                % (etq, legible(hijo), legible(padre), n),
                "Que %s tienen mas de %d %s? Devuelve %s y la cantidad."
                % (legible(padre), n, legible(hijo), etq),
            ), (
                "SELECT p.%s, COUNT(*) AS total FROM %s h JOIN %s p ON h.%s = p.%s "
                "GROUP BY p.%s, p.%s HAVING COUNT(*) > %d"
                % (etq, hijo, padre, col, col_padre, col_padre, etq, n)
            )


def m_join_filtro(esq, rng):
    for hijo, col, padre, col_padre in esq["relaciones"]:
        th, tp = esq["tablas"][hijo], esq["tablas"][padre]
        etq_h, etq_p = etiqueta(th), etiqueta(tp)
        for c in numericas(th):
            for v in cuantiles(th, c):
                yield frase(
                    rng,
                    "Muestra %s de %s y %s de %s para los registros con %s mayor que %s."
                    % (etq_h, legible(hijo), etq_p, legible(padre), c["nombre"], v),
                    "Devuelve %s de %s y %s de %s para los %s cuyo %s supere %s."
                    % (etq_h, legible(hijo), etq_p, legible(padre), legible(hijo),
                       c["nombre"], v),
                ), (
                    "SELECT h.%s, p.%s FROM %s h JOIN %s p ON h.%s = p.%s WHERE h.%s > %s"
                    % (etq_h, etq_p, hijo, padre, col, col_padre, c["nombre"], v)
                )


def m_top_padres(esq, rng):
    for hijo, col, padre, col_padre in esq["relaciones"]:
        tp = esq["tablas"][padre]
        etq = etiqueta(tp)
        n = rng.choice([3, 5])
        yield frase(
            rng,
            "Cuales son los %d %s con mas %s? Devuelve %s y la cantidad, ordenados de "
            "mayor a menor." % (n, legible(padre), legible(hijo), etq),
            "Devuelve los %d %s que acumulan mas %s, con %s y el total, de mayor a menor."
            % (n, legible(padre), legible(hijo), etq),
        ), (
            "SELECT p.%s, COUNT(*) AS total FROM %s h JOIN %s p ON h.%s = p.%s "
            "GROUP BY p.%s, p.%s ORDER BY total DESC LIMIT %d"
            % (etq, hijo, padre, col, col_padre, col_padre, etq, n)
        )


def m_distintos_con_join(esq, rng):
    for hijo, col, padre, col_padre in esq["relaciones"]:
        yield frase(
            rng,
            "Cuantos %s distintos aparecen en %s? Devuelve solo la cantidad."
            % (legible(padre), legible(hijo)),
            "Cuenta cuantos %s diferentes tienen al menos un %s."
            % (legible(padre), legible(hijo)),
        ), "SELECT COUNT(DISTINCT %s) AS total FROM %s" % (col, hijo)


def m_por_mes(esq, rng):
    for t in esq["tablas"].values():
        for c in fechas(t)[:1]:
            disponibles = anios(t, c)
            if not disponibles:
                continue
            anio = rng.choice(disponibles)
            yield frase(
                rng,
                "Cuantos %s hubo por mes en %d? Devuelve el mes y la cantidad, ordenados "
                "por mes." % (cardinal(t), anio),
                "Agrupa los %s de %d por mes de %s y devuelve el mes y el total, "
                "ordenados por mes." % (cardinal(t), anio, c["nombre"]),
            ), (
                "SELECT MONTH(%s) AS mes, COUNT(*) AS total FROM %s WHERE YEAR(%s) = %d "
                "GROUP BY MONTH(%s) ORDER BY mes"
                % (c["nombre"], t["nombre"], c["nombre"], anio, c["nombre"])
            )


def m_having_promedio(esq, rng):
    for t in esq["tablas"].values():
        for e in enums(t):
            for c in numericas(t):
                v = muestra_num(t, c)
                if v is None:
                    continue
                yield frase(
                    rng,
                    "Devuelve %s y el promedio de %s, solo para los grupos cuyo promedio "
                    "supere %s. Redondea a 2 decimales." % (e["nombre"], c["nombre"], v),
                    "Que valores de %s tienen un promedio de %s mayor que %s? Devuelve %s "
                    "y el promedio redondeado a 2 decimales."
                    % (e["nombre"], c["nombre"], v, e["nombre"]),
                ), (
                    "SELECT %s, ROUND(AVG(%s), 2) AS promedio FROM %s GROUP BY %s "
                    "HAVING AVG(%s) > %s"
                    % (e["nombre"], c["nombre"], t["nombre"], e["nombre"], c["nombre"], v)
                )


def m_dos_joins(esq, rng):
    por_hijo = {}
    for hijo, col, padre, col_padre in esq["relaciones"]:
        por_hijo.setdefault(hijo, []).append((col, padre, col_padre))
    for hijo, relaciones in por_hijo.items():
        if len(relaciones) < 2:
            continue
        (c1, p1, k1), (c2, p2, k2) = relaciones[0], relaciones[1]
        e1, e2 = etiqueta(esq["tablas"][p1]), etiqueta(esq["tablas"][p2])
        yield frase(
            rng,
            "Devuelve %s de %s, %s de %s y la cantidad de %s que los relacionan."
            % (e1, legible(p1), e2, legible(p2), legible(hijo)),
            "Para cada combinacion de %s y %s, cuenta los %s. Devuelve %s, %s y el total."
            % (legible(p1), legible(p2), legible(hijo), e1, e2),
        ), (
            "SELECT a.%s, b.%s, COUNT(*) AS total FROM %s h "
            "JOIN %s a ON h.%s = a.%s JOIN %s b ON h.%s = b.%s "
            "GROUP BY a.%s, a.%s, b.%s, b.%s"
            % (e1, e2, hijo, p1, c1, k1, p2, c2, k2, k1, e1, k2, e2)
        )


# --------------------------------------------------------------------------
# Plantillas: nivel dificil (subconsultas, WITH, ventana, fechas)
# --------------------------------------------------------------------------

def d_sobre_promedio(esq, rng):
    for t in esq["tablas"].values():
        etq = etiqueta(t)
        for c in numericas(t):
            if muestra_num(t, c) is None:
                continue
            yield frase(
                rng,
                "Devuelve %s y %s de los %s cuyo %s sea mayor que el promedio de %s de "
                "toda la tabla." % (etq, c["nombre"], cardinal(t), c["nombre"], c["nombre"]),
                "Que %s superan el %s promedio? Devuelve %s y %s."
                % (cardinal(t), etiqueta_col(c), etq, c["nombre"]),
            ), (
                "SELECT %s, %s FROM %s WHERE %s > (SELECT AVG(%s) FROM %s)"
                % (etq, c["nombre"], t["nombre"], c["nombre"], c["nombre"], t["nombre"])
            )


def d_sobre_promedio_grupo(esq, rng):
    for t in esq["tablas"].values():
        etq = etiqueta(t)
        for e in enums(t):
            for c in numericas(t):
                if muestra_num(t, c) is None:
                    continue
                yield frase(
                    rng,
                    "Devuelve %s, %s y %s de los %s cuyo %s supere el promedio de su "
                    "propio %s." % (etq, e["nombre"], c["nombre"], cardinal(t),
                                    c["nombre"], e["nombre"]),
                    "Que %s tienen un %s mayor que el promedio de su %s? Devuelve %s, %s y %s."
                    % (cardinal(t), c["nombre"], e["nombre"], etq, e["nombre"], c["nombre"]),
                ), (
                    "SELECT %s, %s, %s FROM %s t WHERE %s > "
                    "(SELECT AVG(x.%s) FROM %s x WHERE x.%s = t.%s)"
                    % (etq, e["nombre"], c["nombre"], t["nombre"], c["nombre"],
                       c["nombre"], t["nombre"], e["nombre"], e["nombre"])
                )


def d_ventana_por_grupo(esq, rng):
    for t in esq["tablas"].values():
        etq = etiqueta(t)
        for e in enums(t):
            for c in numericas(t):
                if muestra_num(t, c) is None:
                    continue
                yield frase(
                    rng,
                    "Para cada %s, devuelve el %s con mayor %s. Devuelve %s, %s y %s."
                    % (e["nombre"], legible(t["nombre"]), c["nombre"], e["nombre"], etq,
                       c["nombre"]),
                    "Usando una funcion de ventana, obten el registro con el %s mas alto "
                    "de cada %s. Devuelve %s, %s y %s."
                    % (c["nombre"], e["nombre"], e["nombre"], etq, c["nombre"]),
                ), (
                    "WITH ordenados AS (SELECT %s, %s, %s, ROW_NUMBER() OVER "
                    "(PARTITION BY %s ORDER BY %s DESC) AS posicion FROM %s) "
                    "SELECT %s, %s, %s FROM ordenados WHERE posicion = 1"
                    % (e["nombre"], etq, c["nombre"], e["nombre"], c["nombre"],
                       t["nombre"], e["nombre"], etq, c["nombre"])
                )


def d_porcentaje_del_total(esq, rng):
    for t in esq["tablas"].values():
        for e in enums(t):
            for c in numericas(t):
                if muestra_num(t, c) is None:
                    continue
                yield frase(
                    rng,
                    "Devuelve %s, la suma de %s y su porcentaje sobre el total, "
                    "redondeado a 2 decimales." % (e["nombre"], c["nombre"]),
                    "Para cada %s calcula el total de %s y que porcentaje representa del "
                    "total general, redondeado a 2 decimales. Devuelve %s, la suma y el "
                    "porcentaje." % (e["nombre"], c["nombre"], e["nombre"]),
                ), (
                    "WITH totales AS (SELECT %s, SUM(%s) AS suma FROM %s GROUP BY %s) "
                    "SELECT %s, suma, ROUND(100 * suma / SUM(suma) OVER (), 2) AS porcentaje "
                    "FROM totales" % (e["nombre"], c["nombre"], t["nombre"], e["nombre"],
                                      e["nombre"])
                )


def d_sin_hijos(esq, rng):
    for hijo, col, padre, col_padre in esq["relaciones"]:
        tp = esq["tablas"][padre]
        etq = etiqueta(tp)
        yield frase(
            rng,
            "Devuelve %s de los %s que no tienen ningun %s."
            % (etq, legible(padre), legible(hijo)),
            "Que %s no aparecen en %s? Devuelve %s." % (legible(padre), legible(hijo), etq),
        ), (
            "SELECT p.%s FROM %s p WHERE NOT EXISTS "
            "(SELECT 1 FROM %s h WHERE h.%s = p.%s)"
            % (etq, padre, hijo, col, col_padre)
        )


def d_subconsulta_in(esq, rng):
    for hijo, col, padre, col_padre in esq["relaciones"]:
        tp = esq["tablas"][padre]
        etq = etiqueta(tp)
        n = rng.choice([3, 5])
        yield frase(
            rng,
            "Devuelve %s de los %s que tienen mas de %d %s, usando una subconsulta."
            % (etq, legible(padre), n, legible(hijo)),
            "Que %s acumulan mas de %d %s? Devuelve %s."
            % (legible(padre), n, legible(hijo), etq),
        ), (
            "SELECT %s FROM %s WHERE %s IN "
            "(SELECT %s FROM %s GROUP BY %s HAVING COUNT(*) > %d)"
            % (etq, padre, col_padre, col, hijo, col, n)
        )


def d_diferencia_fechas(esq, rng):
    for t in esq["tablas"].values():
        columnas = fechas(t)
        if len(columnas) < 2:
            continue
        a, b = columnas[0], columnas[1]
        yield frase(
            rng,
            "Cual es el promedio de dias entre %s y %s en %s? Redondea a 2 decimales."
            % (a["nombre"], b["nombre"], t["nombre"]),
            "Calcula cuantos dias pasan en promedio entre %s y %s en %s, redondeado a "
            "2 decimales." % (a["nombre"], b["nombre"], t["nombre"]),
        ), (
            "SELECT ROUND(AVG(DATEDIFF(%s, %s)), 2) AS promedio_dias FROM %s "
            "WHERE %s IS NOT NULL AND %s IS NOT NULL"
            % (b["nombre"], a["nombre"], t["nombre"], a["nombre"], b["nombre"])
        )


def d_total_por_anio(esq, rng):
    for t in esq["tablas"].values():
        columnas = fechas(t)
        nums = numericas(t)
        if not columnas or not nums:
            continue
        f, c = columnas[0], nums[0]
        if muestra_num(t, c) is None:
            continue
        yield frase(
            rng,
            "Usando WITH, devuelve el anio de %s y el total de %s de cada anio, "
            "ordenado por anio." % (f["nombre"], c["nombre"]),
            "Calcula el total de %s por anio de %s y devuelve el anio y el total, "
            "ordenados por anio." % (c["nombre"], f["nombre"]),
        ), (
            "WITH por_anio AS (SELECT YEAR(%s) AS anio, SUM(%s) AS total FROM %s "
            "GROUP BY YEAR(%s)) SELECT anio, total FROM por_anio ORDER BY anio"
            % (f["nombre"], c["nombre"], t["nombre"], f["nombre"])
        )


def d_ranking_padres(esq, rng):
    for hijo, col, padre, col_padre in esq["relaciones"]:
        th, tp = esq["tablas"][hijo], esq["tablas"][padre]
        etq = etiqueta(tp)
        nums = numericas(th)
        if not nums or muestra_num(th, nums[0]) is None:
            continue
        c = nums[0]
        yield frase(
            rng,
            "Devuelve %s de %s, el total de %s de sus %s y su posicion en el ranking de "
            "mayor a menor." % (etq, legible(padre), c["nombre"], legible(hijo)),
            "Usando una funcion de ventana, ordena los %s por el total de %s y devuelve "
            "%s, el total y la posicion." % (legible(padre), c["nombre"], etq),
        ), (
            "WITH totales AS (SELECT p.%s AS etiqueta, SUM(h.%s) AS total FROM %s h "
            "JOIN %s p ON h.%s = p.%s GROUP BY p.%s, p.%s) "
            "SELECT etiqueta, total, RANK() OVER (ORDER BY total DESC) AS posicion "
            "FROM totales"
            % (etq, c["nombre"], hijo, padre, col, col_padre, col_padre, etq)
        )


def d_comparar_con_maximo(esq, rng):
    for t in esq["tablas"].values():
        etq = etiqueta(t)
        for c in numericas(t):
            if muestra_num(t, c) is None:
                continue
            yield frase(
                rng,
                "Devuelve %s, %s y la diferencia entre %s y el valor maximo de %s, "
                "redondeada a 2 decimales."
                % (etq, c["nombre"], c["nombre"], t["nombre"]),
                "Para cada %s calcula cuanto le falta a su %s para alcanzar el maximo. "
                "Devuelve %s, %s y la diferencia redondeada a 2 decimales."
                % (legible(t["nombre"]), c["nombre"], etq, c["nombre"]),
            ), (
                "SELECT %s, %s, ROUND(MAX(%s) OVER () - %s, 2) AS diferencia FROM %s"
                % (etq, c["nombre"], c["nombre"], c["nombre"], t["nombre"])
            )


def d_mes_con_mas(esq, rng):
    for t in esq["tablas"].values():
        columnas = fechas(t)
        if not columnas:
            continue
        f = columnas[0]
        disponibles = anios(t, f)
        if not disponibles:
            continue
        anio = rng.choice(disponibles)
        yield frase(
            rng,
            "En %d, cual fue el mes con mas %s? Devuelve el mes y la cantidad."
            % (anio, cardinal(t)),
            "Usando WITH, encuentra el mes de %d con mayor numero de %s y devuelve el "
            "mes y el total." % (anio, cardinal(t)),
        ), (
            "WITH por_mes AS (SELECT MONTH(%s) AS mes, COUNT(*) AS total FROM %s "
            "WHERE YEAR(%s) = %d GROUP BY MONTH(%s)) "
            "SELECT mes, total FROM por_mes WHERE total = (SELECT MAX(total) FROM por_mes)"
            % (f["nombre"], t["nombre"], f["nombre"], anio, f["nombre"])
        )


PLANTILLAS = [
    ("facil", "conteo_total", f_conteo_total),
    ("facil", "filtro_numerico", f_filtro_numerico),
    ("facil", "top_n", f_top_n),
    ("facil", "filtro_enum", f_filtro_enum),
    ("facil", "agregado_simple", f_agregado_simple),
    ("facil", "distintos", f_distintos),
    ("facil", "conteo_anio", f_anio),
    ("facil", "booleano", f_booleano),
    ("facil", "nulos", f_nulos),
    ("facil", "rango_fecha", f_rango_fecha),
    ("facil", "texto_like", f_texto_like),
    ("media", "conteo_por_padre", m_conteo_por_padre),
    ("media", "suma_por_padre", m_suma_por_padre),
    ("media", "promedio_por_enum", m_promedio_por_enum),
    ("media", "having", m_having),
    ("media", "join_filtro", m_join_filtro),
    ("media", "top_padres", m_top_padres),
    ("media", "distintos_con_join", m_distintos_con_join),
    ("media", "por_mes", m_por_mes),
    ("media", "having_promedio", m_having_promedio),
    ("media", "dos_joins", m_dos_joins),
    ("dificil", "sobre_promedio", d_sobre_promedio),
    ("dificil", "sobre_promedio_grupo", d_sobre_promedio_grupo),
    ("dificil", "ventana_por_grupo", d_ventana_por_grupo),
    ("dificil", "porcentaje_del_total", d_porcentaje_del_total),
    ("dificil", "sin_hijos", d_sin_hijos),
    ("dificil", "subconsulta_in", d_subconsulta_in),
    ("dificil", "diferencia_fechas", d_diferencia_fechas),
    ("dificil", "total_por_anio", d_total_por_anio),
    ("dificil", "ranking_padres", d_ranking_padres),
    ("dificil", "comparar_con_maximo", d_comparar_con_maximo),
    ("dificil", "mes_con_mas", d_mes_con_mas),
]


def columnas_ambiguas(esq):
    """Columnas FK de tablas que apuntan dos veces a la misma tabla.

    En aerolinea, vuelos.origen y vuelos.destino apuntan a aeropuertos: una
    pregunta que solo diga "los vuelos de cada aeropuerto" no determina por cual
    de las dos se une, y ningun modelo puede acertar a adivinarla.
    """
    cuenta = collections.Counter((hijo, padre) for hijo, _, padre, _ in esq["relaciones"])
    return {
        col for hijo, col, padre, _ in esq["relaciones"] if cuenta[(hijo, padre)] > 1
    }


def desambiguar(pregunta, sql, ambiguas):
    for col in sorted(ambiguas):
        if re.search(r"\b%s\b" % re.escape(col), sql) and col not in pregunta:
            return "%s Relaciona las tablas por %s." % (pregunta, col)
    return pregunta


def generar(esq, limite, rng):
    # Las plantillas faciles se instancian de muchas mas formas que las
    # dificiles, asi que el tope se ajusta por nivel para que el dataset no
    # quede dominado por consultas de una sola tabla.
    topes = {"facil": max(1, limite // 2), "media": limite, "dificil": limite * 2}
    ambiguas = columnas_ambiguas(esq)
    pares, vistos = [], set()
    for nivel, nombre, funcion in PLANTILLAS:
        n = 0
        for pregunta, sql in funcion(esq, rng):
            if n >= topes[nivel]:
                break
            clave = sql.lower()
            if clave in vistos:
                continue
            vistos.add(clave)
            pregunta = desambiguar(pregunta, sql, ambiguas)
            pares.append(
                {"base": esq["base"], "nivel": nivel, "plantilla": nombre,
                 "pregunta": pregunta, "sql": sql}
            )
            n += 1
    return pares


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", default="datos/esquemas", help="Directorio con los .sql")
    parser.add_argument("--salida", default="datos/pares_crudos.jsonl")
    parser.add_argument("--limite", type=int, default=12,
                        help="Maximo de pares por plantilla y por base")
    args = parser.parse_args()

    bases = [p.stem for p in sorted(pathlib.Path(args.dir).glob("*.sql"))]
    conn = db.conectar()
    rng = random.Random(SEMILLA)
    todos = []
    for base in bases:
        esq = inspeccionar(conn, base)
        pares = generar(esq, args.limite, rng)
        todos.extend(pares)
        print("[ok] %-14s %4d pares" % (base, len(pares)))
    conn.close()

    salida = pathlib.Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    with salida.open("w", encoding="utf-8") as fh:
        for par in todos:
            fh.write(json.dumps(par, ensure_ascii=False) + "\n")

    print("\n%d pares escritos en %s" % (len(todos), salida))
    for nivel in ("facil", "media", "dificil"):
        n = sum(1 for p in todos if p["nivel"] == nivel)
        print("  %-8s %4d (%.0f%%)" % (nivel, n, 100 * n / max(1, len(todos))))


if __name__ == "__main__":
    main()

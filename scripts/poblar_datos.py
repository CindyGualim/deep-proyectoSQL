"""Inserta filas de prueba en las bases cargadas, con semilla fija.

El poblador es generico: lee information_schema para descubrir columnas, tipos,
claves foraneas y restricciones UNIQUE, y genera valores plausibles a partir del
tipo de la columna y de pistas en su nombre (precio, ciudad, fecha_nacimiento...).

Asi un mismo script sirve para los 12 esquemas de entrenamiento y para los de
validacion, y la misma semilla reproduce exactamente las mismas filas.
"""

import datetime
import random
import re
import zlib

SEMILLA = 2026

# Numero de filas segun el papel de la tabla en el esquema.
FILAS_CATALOGO = 25      # tabla referenciada y sin claves foraneas propias
FILAS_DIMENSION = 60     # tabla referenciada por otras
FILAS_HECHO = 300        # tabla que nadie referencia (movimientos, detalles)

HOY = datetime.date(2026, 6, 30)
INICIO = datetime.date(2023, 1, 1)

NOMBRES = [
    "Ana", "Luis", "Maria", "Carlos", "Sofia", "Jorge", "Lucia", "Pedro", "Elena",
    "Diego", "Valeria", "Andres", "Camila", "Javier", "Daniela", "Rodrigo", "Paula",
    "Fernando", "Gabriela", "Mateo", "Isabel", "Oscar", "Natalia", "Hector", "Rebeca",
]
APELLIDOS = [
    "Gomez", "Lopez", "Perez", "Ramirez", "Castillo", "Morales", "Herrera", "Vargas",
    "Mendez", "Ortiz", "Rivera", "Juarez", "Solis", "Navarro", "Cabrera", "Estrada",
    "Figueroa", "Pineda", "Aguilar", "Sandoval", "Barrios", "Quinonez", "Reyes",
]
CIUDADES = [
    "Guatemala", "Quetzaltenango", "Antigua", "Escuintla", "Coban", "Huehuetenango",
    "Mazatenango", "Peten", "Zacapa", "Retalhuleu", "Chimaltenango", "Solola",
]
PAISES = [
    "Guatemala", "Mexico", "Espana", "Colombia", "Argentina", "Chile", "Peru",
    "Estados Unidos", "Costa Rica", "Panama", "Ecuador", "Uruguay",
]
COSAS = [
    "Central", "Norte", "Sur", "Oriente", "Occidente", "Premium", "Clasico",
    "Express", "Familiar", "Ejecutivo", "Basico", "Integral", "Dorado", "Plata",
    "Azul", "Verde", "Rojo", "Maya", "Colonial", "Moderno",
]
FARMACOS = [
    "Amoxicilina", "Ibuprofeno", "Paracetamol", "Omeprazol", "Loratadina",
    "Metformina", "Losartan", "Azitromicina", "Diclofenaco", "Salbutamol",
]
ESPECIALIDADES = [
    "Cardiologia", "Pediatria", "Dermatologia", "Traumatologia", "Neurologia",
    "Ginecologia", "Oftalmologia", "Medicina interna", "Psiquiatria", "Urologia",
]

# Pistas en los nombres de columna -> rango numerico (minimo, maximo, decimales).
RANGOS = [
    (r"pct|porcentaje|comision|discount|tasa|interes", (0, 25, 2)),
    (r"precio_m2", (900, 9000, 2)),
    (r"presupuesto|budget", (50000, 2000000, 2)),
    (r"salario|salary|gross|net|ingreso", (3000, 45000, 2)),
    (r"deduction|mora", (0, 1200, 2)),
    (r"saldo|limite", (0, 250000, 2)),
    (r"monto|amount|paid|costo|cost|fee|tarifa|arancel|precio|price", (25, 8000, 2)),
    (r"nota_final|score", (0, 100, 2)),
    (r"rating", (1, 10, 1)),
    (r"anio_fundacion", (1890, 2015, 0)),
    (r"release_year", (1975, 2026, 0)),
    (r"anio|year", (1995, 2026, 0)),
    (r"paginas", (80, 900, 0)),
    (r"creditos", (2, 6, 0)),
    (r"dias", (3, 21, 0)),
    (r"plazo_meses", (6, 72, 0)),
    (r"retraso_min", (0, 180, 0)),
    (r"dur_min|duration_min|minutes_watched|hours$|_hours", (15, 240, 0)),
    (r"hours_worked", (4, 10, 2)),
    (r"horas_estimadas", (1, 14, 2)),
    (r"horas_vuelo", (300, 12000, 0)),
    (r"millas", (0, 90000, 0)),
    (r"distancia_km", (15, 600, 2)),
    (r"peso_kg|capacidad_kg", (1, 2500, 2)),
    (r"metros2", (45, 850, 2)),
    (r"capacidad|^cap$|stock|max_cls", (4, 200, 0)),
    (r"cantidad|quantity|comensales|habitaciones|banos|season|ejemplares", (1, 6, 0)),
    (r"number|numero", (1, 60, 0)),
]


def _rng(base, tabla):
    """Generador reproducible por base y tabla."""
    semilla = SEMILLA + zlib.crc32(("%s.%s" % (base, tabla)).encode("utf-8"))
    return random.Random(semilla)


def _coincide(patron, nombre):
    return re.search(patron, nombre) is not None


def _es_persona(tabla, columna):
    personas = (
        "socio", "cliente", "autor", "profesor", "estudiante", "mesero", "agente",
        "conductor", "pasajero", "tripulacion", "med", "pac", "employee", "mbr",
        "trn", "customer", "user",
    )
    return any(p in tabla for p in personas) and _coincide(
        r"nombre|^nom$|full_name|first_name|fname|trn_nm|razon_social", columna
    )


# --------------------------------------------------------------------------
# Lectura del esquema
# --------------------------------------------------------------------------

def _metadatos(conn, base):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, IS_NULLABLE,"
            "       EXTRA, COLUMN_KEY, NUMERIC_PRECISION, NUMERIC_SCALE,"
            "       CHARACTER_MAXIMUM_LENGTH, ORDINAL_POSITION"
            "  FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s"
            " ORDER BY TABLE_NAME, ORDINAL_POSITION",
            (base,),
        )
        columnas = {}
        for fila in cur.fetchall():
            columnas.setdefault(fila[0], []).append(
                {
                    "nombre": fila[1],
                    "tipo": fila[2],
                    "tipo_completo": fila[3],
                    "nulo": fila[4] == "YES",
                    "extra": fila[5],
                    "clave": fila[6],
                    "precision": fila[7],
                    "escala": fila[8],
                    "largo": fila[9],
                }
            )

        cur.execute(
            "SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME"
            "  FROM information_schema.KEY_COLUMN_USAGE"
            " WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL",
            (base,),
        )
        fks = {(f[0], f[1]): (f[2], f[3]) for f in cur.fetchall()}

        cur.execute(
            "SELECT k.TABLE_NAME, k.COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE k"
            "  JOIN information_schema.TABLE_CONSTRAINTS t"
            "    ON t.CONSTRAINT_NAME = k.CONSTRAINT_NAME"
            "   AND t.TABLE_SCHEMA = k.TABLE_SCHEMA AND t.TABLE_NAME = k.TABLE_NAME"
            " WHERE k.TABLE_SCHEMA = %s AND t.CONSTRAINT_TYPE IN ('UNIQUE','PRIMARY KEY')",
            (base,),
        )
        unicas = {(f[0], f[1]) for f in cur.fetchall()}
    return columnas, fks, unicas


def _orden_topologico(tablas, fks):
    """Ordena las tablas para que los padres se inserten antes que los hijos."""
    pendientes = list(tablas)
    listas, orden = set(), []
    while pendientes:
        avanzo = False
        for tabla in list(pendientes):
            padres = {
                destino
                for (t, _), (destino, _) in fks.items()
                if t == tabla and destino != tabla
            }
            if padres <= listas:
                orden.append(tabla)
                listas.add(tabla)
                pendientes.remove(tabla)
                avanzo = True
        if not avanzo:  # ciclo entre tablas: se resuelve por orden alfabetico
            orden.extend(sorted(pendientes))
            break
    return orden


# --------------------------------------------------------------------------
# Generacion de valores
# --------------------------------------------------------------------------

def _texto(tabla, col, rng, i):
    nombre = col["nombre"]
    largo = col["largo"] or 60

    if _coincide(r"email|correo", nombre):
        return ("%s.%s%d@correo.com" % (
            rng.choice(NOMBRES).lower(), rng.choice(APELLIDOS).lower(), i))[:largo]
    if _es_persona(tabla, nombre):
        return "%s %s" % (rng.choice(NOMBRES), rng.choice(APELLIDOS))
    if _coincide(r"apellido|^ape$|last_name|lname", nombre):
        return rng.choice(APELLIDOS)
    if _coincide(r"ciudad|city", nombre):
        return rng.choice(CIUDADES)
    if _coincide(r"pais|country|nacionalidad", nombre):
        return rng.choice(PAISES)
    if _coincide(r"tel|phone", nombre):
        return "5%03d-%04d" % (rng.randint(0, 999), rng.randint(0, 9999))
    if _coincide(r"direccion|address|location|edificio|room", nombre):
        return "%d calle %d-%02d zona %d" % (
            rng.randint(1, 30), rng.randint(1, 40), rng.randint(1, 99), rng.randint(1, 21))
    if _coincide(r"farmaco", nombre):
        return rng.choice(FARMACOS)
    if _coincide(r"specialty|especialidad|desc_esp", nombre):
        return rng.choice(ESPECIALIDADES)
    if _coincide(r"isbn", nombre):
        return "978%010d" % i
    if _coincide(r"iata", nombre):
        return "%s%s%s" % tuple(rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(3))
    if _coincide(r"period", nombre):
        return "%d-%02d" % (rng.choice([2024, 2025, 2026]), rng.randint(1, 12))
    if _coincide(r"ciclo", nombre):
        return "%d-%d" % (rng.choice([2024, 2025, 2026]), rng.randint(1, 2))
    if _coincide(r"asiento|seat", nombre):
        return "%d%s" % (rng.randint(1, 38), rng.choice("ABCDEF"))
    if _coincide(r"cod_cie", nombre):
        return "%s%02d" % (rng.choice("ABCDEFGHIJKLM"), rng.randint(0, 99))
    if _coincide(r"dosis", nombre):
        return "%d mg cada %d horas" % (rng.choice([100, 250, 500, 750]), rng.choice([6, 8, 12]))
    if _coincide(r"desc|comment|nota$|descripcion", nombre):
        return "Registro %s de %s" % (rng.choice(COSAS).lower(), tabla)
    if _coincide(
        r"sku|codigo|guia|matricula|placa|licencia|carnet|dpi|nit|pasaporte|numero"
        r"|numero_enmascarado", nombre
    ):
        return ("%s%06d" % (tabla[:3].upper(), i))[:largo]

    # Nombre generico de una cosa: suficiente para agrupar y filtrar por texto.
    return ("%s %s %d" % (tabla.rstrip("s").capitalize(), rng.choice(COSAS), i))[:largo]


def _numero(col, rng):
    nombre = col["nombre"]
    for patron, (lo, hi, dec) in RANGOS:
        if _coincide(patron, nombre):
            if dec == 0:
                return rng.randint(int(lo), int(hi))
            return round(rng.uniform(lo, hi), dec)

    if col["tipo"] in ("decimal", "float", "double"):
        escala = col["escala"] or 2
        return round(rng.uniform(10, 5000), escala)
    if col["tipo"] == "tinyint":
        return rng.randint(1, 20)
    return rng.randint(1, 100)


def _booleano(rng):
    return 1 if rng.random() < 0.7 else 0


def _enum(col, rng):
    valores = re.findall(r"'([^']*)'", col["tipo_completo"])
    return rng.choice(valores) if valores else None


def _clase_fecha(nombre):
    if _coincide(r"nacimiento|birth|fnac", nombre):
        return "nacimiento"
    if _coincide(r"vencimiento|expir", nombre):
        return "futuro"
    return "normal"


def _fecha_base(nombre, rng):
    clase = _clase_fecha(nombre)
    if clase == "nacimiento":
        inicio, fin = datetime.date(1955, 1, 1), datetime.date(2007, 12, 31)
    elif clase == "futuro":
        inicio, fin = datetime.date(2026, 7, 1), datetime.date(2030, 12, 31)
    else:
        inicio, fin = INICIO, HOY
    return inicio + datetime.timedelta(days=rng.randint(0, (fin - inicio).days))


def _fechas_de_fila(columnas, rng):
    """Genera las fechas de una fila manteniendo el orden cronologico.

    Las columnas de fecha que no son de nacimiento ni de vencimiento se tratan
    como una secuencia: la primera se sortea y las siguientes se derivan
    sumando un intervalo, de modo que fecha_devolucion cae despues de
    fecha_prestamo y hora_fin despues de hora_inicio.
    """
    valores = {}
    secuencia = [
        c for c in columnas
        if c["tipo"] in ("date", "datetime", "timestamp", "time")
        and _clase_fecha(c["nombre"]) == "normal"
    ]
    aparte = [
        c for c in columnas
        if c["tipo"] in ("date", "datetime", "timestamp", "time")
        and _clase_fecha(c["nombre"]) != "normal"
    ]

    for col in aparte:
        valores[col["nombre"]] = _fecha_base(col["nombre"], rng)

    anterior = None
    for col in secuencia:
        if col["tipo"] == "time":
            if anterior is None:
                momento = datetime.datetime(2026, 1, 1, rng.randint(7, 17), rng.choice([0, 30]))
            else:
                momento = anterior + datetime.timedelta(hours=rng.randint(1, 2))
            anterior = momento
            valores[col["nombre"]] = momento.strftime("%H:%M:%S")
            continue

        if anterior is None or not isinstance(anterior, datetime.datetime):
            dia = _fecha_base(col["nombre"], rng)
            momento = datetime.datetime(
                dia.year, dia.month, dia.day, rng.randint(6, 22), rng.choice([0, 15, 30, 45])
            )
        else:
            momento = anterior + datetime.timedelta(
                days=rng.randint(0, 45), hours=rng.randint(1, 10)
            )
        anterior = momento
        if col["tipo"] == "date":
            valores[col["nombre"]] = momento.date()
        else:
            valores[col["nombre"]] = momento.replace(microsecond=0)
    return valores


def _nulo(col, rng):
    """Decide si una columna opcional queda vacia."""
    if not col["nulo"]:
        return False
    if _coincide(r"devolucion|entrega|end_dt|end_date|completed_at", col["nombre"]):
        return rng.random() < 0.25
    return rng.random() < 0.15


# --------------------------------------------------------------------------
# Insercion
# --------------------------------------------------------------------------

def _filas_objetivo(tabla, columnas, fks, referenciadas):
    propias = [c for c in columnas if (tabla, c["nombre"]) in fks]
    if tabla in referenciadas:
        return FILAS_CATALOGO if not propias else FILAS_DIMENSION
    return FILAS_HECHO


def poblar(conn, base):
    columnas, fks, unicas = _metadatos(conn, base)
    referenciadas = {destino for destino, _ in fks.values()}
    total = 0
    claves = {}  # tabla -> lista de valores de su clave primaria

    with conn.cursor() as cur:
        cur.execute("USE `%s`" % base)
        for tabla in _orden_topologico(list(columnas), fks):
            cols = columnas[tabla]
            rng = _rng(base, tabla)
            auto = [c for c in cols if "auto_increment" in c["extra"]]
            insertables = [c for c in cols if c not in auto]
            objetivo = _filas_objetivo(tabla, cols, fks, referenciadas)

            # Tabla puente: la clave primaria son solo claves foraneas, asi que
            # se generan combinaciones distintas en lugar de filas sueltas.
            pk = [c["nombre"] for c in cols if c["clave"] == "PRI"]
            es_puente = len(pk) > 1 and all((tabla, p) in fks for p in pk)

            vistos = {c["nombre"]: set() for c in insertables}
            filas, combinaciones = [], set()
            intentos = 0
            while len(filas) < objetivo and intentos < objetivo * 8:
                intentos += 1
                fila = _construir_fila(tabla, insertables, fks, unicas, claves, rng,
                                       vistos, len(filas) + 1)
                if fila is None:
                    break
                if es_puente:
                    combo = tuple(fila[p] for p in pk)
                    if combo in combinaciones:
                        continue
                    combinaciones.add(combo)
                filas.append(fila)

            if not filas:
                continue

            nombres = [c["nombre"] for c in insertables]
            sql = "INSERT INTO `%s` (%s) VALUES (%s)" % (
                tabla,
                ", ".join("`%s`" % n for n in nombres),
                ", ".join(["%s"] * len(nombres)),
            )
            datos = [tuple(fila[n] for n in nombres) for fila in filas]
            for i in range(0, len(datos), 200):
                cur.executemany(sql, datos[i:i + 200])
            total += len(datos)

            if auto:
                claves[tabla] = list(range(1, len(filas) + 1))
            elif len(pk) == 1:
                claves[tabla] = [fila[pk[0]] for fila in filas]
    return total


def _construir_fila(tabla, insertables, fks, unicas, claves, rng, vistos, indice):
    fila = {}
    fechas = _fechas_de_fila(insertables, rng)

    for col in insertables:
        nombre = col["nombre"]
        referencia = fks.get((tabla, nombre))

        if referencia:
            destino = referencia[0]
            if destino == tabla:
                # Autorreferencia: apunta a una fila ya insertada o queda vacia.
                fila[nombre] = rng.randint(1, max(1, indice - 1)) if (
                    indice > 3 and rng.random() < 0.6) else None
                if not col["nulo"] and fila[nombre] is None:
                    fila[nombre] = 1
                continue
            disponibles = claves.get(destino)
            if not disponibles:
                return None
            fila[nombre] = rng.choice(disponibles)
            continue

        if _nulo(col, rng) and (tabla, nombre) not in unicas:
            fila[nombre] = None
            continue

        if col["tipo"] == "enum":
            valor = _enum(col, rng)
        elif col["tipo"] in ("date", "datetime", "timestamp", "time"):
            valor = fechas[nombre]
        elif col["tipo_completo"].startswith("tinyint(1)"):
            valor = _booleano(rng)
        elif col["tipo"] in ("int", "bigint", "smallint", "mediumint", "tinyint",
                             "decimal", "float", "double"):
            valor = _numero(col, rng)
        else:
            valor = _texto(tabla, col, rng, indice)

        # Las columnas UNIQUE llevan sufijo hasta que el valor no se repita.
        if (tabla, nombre) in unicas and isinstance(valor, str):
            intento, original = 0, valor
            while valor in vistos[nombre]:
                intento += 1
                sufijo = str(intento)
                largo = col["largo"] or 60
                valor = original[: largo - len(sufijo)] + sufijo
            vistos[nombre].add(valor)

        fila[nombre] = valor
    return fila

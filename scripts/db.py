"""Conexion a MySQL 8.4.10 compartida por los scripts de datos.

La configuracion se lee de variables de entorno para que el mismo codigo sirva
en local (Docker) y en Colab (binario descomprimido):

    MYSQL_HOST      por defecto 127.0.0.1
    MYSQL_PORT      por defecto 3306
    MYSQL_USER      por defecto root
    MYSQL_PASSWORD  por defecto cadena vacia
"""

import os

import pymysql

SEMILLA = 2026


def parametros():
    return {
        "host": os.environ.get("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.environ.get("MYSQL_PORT", "3306")),
        "user": os.environ.get("MYSQL_USER", "root"),
        "password": os.environ.get("MYSQL_PASSWORD", ""),
        "charset": "utf8mb4",
        "autocommit": True,
    }


def conectar(base=None):
    """Abre una conexion, opcionalmente posicionada en una base."""
    kwargs = parametros()
    if base:
        kwargs["database"] = base
    return pymysql.connect(**kwargs)


def bases_de_datos(conn, prefijo=""):
    """Lista las bases creadas por el proyecto, excluyendo las del sistema."""
    sistema = {"mysql", "information_schema", "performance_schema", "sys"}
    with conn.cursor() as cur:
        cur.execute("SHOW DATABASES")
        nombres = [fila[0] for fila in cur.fetchall()]
    return [n for n in nombres if n not in sistema and n.startswith(prefijo)]


def show_create(conn, base):
    """Devuelve el esquema de una base tal como lo ve el evaluador.

    Concatena SHOW CREATE TABLE de todas las tablas, que es exactamente el
    formato que recibe generar_sql() en el argumento `esquema`.
    """
    with conn.cursor() as cur:
        cur.execute("USE `%s`" % base)
        cur.execute("SHOW TABLES")
        tablas = [fila[0] for fila in cur.fetchall()]
        partes = []
        for tabla in tablas:
            cur.execute("SHOW CREATE TABLE `%s`" % tabla)
            partes.append(cur.fetchone()[1] + ";")
    return "\n\n".join(partes)

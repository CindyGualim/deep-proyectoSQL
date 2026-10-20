"""Crea en MySQL una base por cada archivo .sql de un directorio.

El nombre de la base es el nombre del archivo sin extension. Cada archivo
contiene solo sentencias CREATE TABLE, de modo que el esquema que se entrega al
modelo se obtiene despues con SHOW CREATE TABLE.

Uso:
    python scripts/cargar_esquemas.py --dir datos/esquemas
    python scripts/cargar_esquemas.py --dir datos/validacion/esquemas --poblar
"""

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import db  # noqa: E402


def sentencias(texto):
    """Divide un archivo .sql en sentencias.

    Los esquemas del proyecto no contienen punto y coma dentro de literales,
    asi que basta con cortar por ';'.
    """
    for bruto in texto.split(";"):
        limpio = "\n".join(
            linea for linea in bruto.splitlines() if not linea.strip().startswith("--")
        ).strip()
        if limpio:
            yield limpio


def cargar(conn, ruta, recrear=True):
    base = ruta.stem
    with conn.cursor() as cur:
        if recrear:
            cur.execute("DROP DATABASE IF EXISTS `%s`" % base)
        cur.execute(
            "CREATE DATABASE IF NOT EXISTS `%s` CHARACTER SET utf8mb4 "
            "COLLATE utf8mb4_0900_ai_ci" % base
        )
        cur.execute("USE `%s`" % base)
        n = 0
        for sentencia in sentencias(ruta.read_text(encoding="utf-8")):
            cur.execute(sentencia)
            n += 1
    return base, n


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", default="datos/esquemas", help="Directorio con los .sql")
    parser.add_argument("--poblar", action="store_true", help="Insertar filas de prueba")
    parser.add_argument(
        "--conservar",
        action="store_true",
        help="No hacer DROP DATABASE antes de crear",
    )
    args = parser.parse_args()

    rutas = sorted(pathlib.Path(args.dir).glob("*.sql"))
    if not rutas:
        raise SystemExit("No se encontraron archivos .sql en %s" % args.dir)

    conn = db.conectar()
    bases = []
    for ruta in rutas:
        base, n = cargar(conn, ruta, recrear=not args.conservar)
        bases.append(base)
        print("[ok] %-14s %2d tablas" % (base, n))

    if args.poblar:
        import poblar_datos

        print()
        for base in bases:
            total = poblar_datos.poblar(conn, base)
            print("[ok] %-14s %5d filas insertadas" % (base, total))

    conn.close()
    print("\n%d bases cargadas desde %s" % (len(bases), args.dir))


if __name__ == "__main__":
    main()

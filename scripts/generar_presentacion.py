"""Convierte presentacion.md en presentacion.pdf, una diapositiva por bloque.

Las diapositivas se separan con `---` en el markdown. Se soportan titulos,
vinetas, tablas simples y bloques de codigo, que es todo lo que usa la
presentacion.

    pip install reportlab
    python scripts/generar_presentacion.py
"""

import pathlib
import re
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as rl_canvas

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ANCHO, ALTO = landscape(A4)
MARGEN = 2.2 * cm

TINTA = colors.HexColor("#1a1a1a")
SUAVE = colors.HexColor("#5a5a5a")
ACENTO = colors.HexColor("#1f6f8b")
FONDO_CODIGO = colors.HexColor("#f2f4f6")


def partir(texto):
    bloques = [b.strip() for b in re.split(r"^---$", texto, flags=re.MULTILINE)]
    return [b for b in bloques if b]


def envolver(c, texto, fuente, tamano, ancho):
    """Parte un texto en lineas que quepan en `ancho`."""
    c.setFont(fuente, tamano)
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = (actual + " " + palabra).strip()
        if c.stringWidth(prueba, fuente, tamano) <= ancho:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas or [""]


def limpiar(texto):
    """Quita el marcado en linea que no se va a renderizar."""
    texto = re.sub(r"`([^`]*)`", r"\1", texto)
    texto = re.sub(r"\*\*([^*]*)\*\*", r"\1", texto)
    texto = re.sub(r"_([^_]*)_", r"\1", texto)
    return texto.strip()


def dibujar(c, bloque, numero, total):
    y = ALTO - MARGEN
    ancho_util = ANCHO - 2 * MARGEN
    en_codigo = False

    for linea in bloque.splitlines():
        cruda = linea.rstrip()

        if cruda.startswith("```"):
            en_codigo = not en_codigo
            y -= 0.2 * cm
            continue

        if en_codigo:
            c.setFillColor(FONDO_CODIGO)
            c.rect(MARGEN - 0.3 * cm, y - 0.35 * cm, ancho_util + 0.6 * cm,
                   0.62 * cm, stroke=0, fill=1)
            c.setFillColor(TINTA)
            c.setFont("Courier", 11)
            c.drawString(MARGEN, y - 0.18 * cm, cruda)
            y -= 0.62 * cm
            continue

        if not cruda:
            y -= 0.35 * cm
            continue

        if cruda.startswith("# "):
            c.setFillColor(TINTA)
            for i, l in enumerate(envolver(c, limpiar(cruda[2:]), "Helvetica-Bold", 30, ancho_util)):
                c.setFont("Helvetica-Bold", 30)
                c.drawString(MARGEN, y, l)
                y -= 1.1 * cm
            c.setStrokeColor(ACENTO)
            c.setLineWidth(2)
            c.line(MARGEN, y + 0.5 * cm, MARGEN + 3.5 * cm, y + 0.5 * cm)
            y -= 0.5 * cm
            continue

        if cruda.startswith("## "):
            c.setFillColor(SUAVE)
            c.setFont("Helvetica", 18)
            c.drawString(MARGEN, y, limpiar(cruda[3:]))
            y -= 0.95 * cm
            continue

        if cruda.startswith("|"):
            celdas = [limpiar(x) for x in cruda.strip("|").split("|")]
            if all(set(x) <= set("-: ") for x in celdas):
                c.setStrokeColor(colors.HexColor("#cccccc"))
                c.setLineWidth(0.7)
                c.line(MARGEN, y + 0.35 * cm, ANCHO - MARGEN, y + 0.35 * cm)
                continue
            ancho_celda = ancho_util / max(1, len(celdas))
            c.setFillColor(TINTA)
            c.setFont("Helvetica", 13)
            for i, celda in enumerate(celdas):
                c.drawString(MARGEN + i * ancho_celda, y, celda[:38])
            y -= 0.72 * cm
            continue

        if cruda.startswith(("- ", "* ")):
            c.setFillColor(ACENTO)
            c.setFont("Helvetica", 14)
            c.drawString(MARGEN, y, "•")
            c.setFillColor(TINTA)
            for i, l in enumerate(envolver(c, limpiar(cruda[2:]), "Helvetica", 14,
                                           ancho_util - 0.8 * cm)):
                c.setFont("Helvetica", 14)
                c.drawString(MARGEN + 0.65 * cm, y, l)
                y -= 0.62 * cm
            y -= 0.12 * cm
            continue

        numerada = re.match(r"^(\d+)\.\s+(.*)$", cruda)
        if numerada:
            c.setFillColor(ACENTO)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(MARGEN, y, numerada.group(1) + ".")
            c.setFillColor(TINTA)
            for l in envolver(c, limpiar(numerada.group(2)), "Helvetica", 14,
                              ancho_util - 0.8 * cm):
                c.setFont("Helvetica", 14)
                c.drawString(MARGEN + 0.75 * cm, y, l)
                y -= 0.62 * cm
            y -= 0.12 * cm
            continue

        c.setFillColor(TINTA)
        for l in envolver(c, limpiar(cruda), "Helvetica", 14, ancho_util):
            c.setFont("Helvetica", 14)
            c.drawString(MARGEN, y, l)
            y -= 0.62 * cm
        y -= 0.1 * cm

    c.setFillColor(SUAVE)
    c.setFont("Helvetica", 9)
    c.drawRightString(ANCHO - MARGEN, MARGEN - 0.8 * cm, "%d / %d" % (numero, total))


def main():
    origen = RAIZ / "presentacion.md"
    destino = RAIZ / "presentacion.pdf"
    bloques = partir(origen.read_text(encoding="utf-8"))

    if len(bloques) > 12:
        raise SystemExit("son %d diapositivas y el maximo es 12" % len(bloques))

    c = rl_canvas.Canvas(str(destino), pagesize=landscape(A4))
    for i, bloque in enumerate(bloques, 1):
        dibujar(c, bloque, i, len(bloques))
        c.showPage()
    c.save()
    print("%s con %d diapositivas" % (destino, len(bloques)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

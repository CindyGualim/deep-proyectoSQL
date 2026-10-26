"""Genera presentacion.pdf: 12 diapositivas, maximo del enunciado.

El contenido vive aqui, en LAMINAS, y se dibuja con primitivas de maquetacion
(tiles de dato, barras, flujos, paneles de codigo) en vez de volcar markdown.
Para cambiar el texto de una diapositiva se edita su entrada en LAMINAS.

Paleta: slots categoricos 1-3 y colores de estado de la guia de visualizacion.
Las barras usan un solo tono porque son una sola serie a lo largo de categorias;
el color de estado nunca va solo, siempre con su etiqueta.

    pip install reportlab
    python scripts/generar_presentacion.py
"""

import pathlib
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as rl_canvas

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ANCHO, ALTO = landscape(A4)
MARGEN = 1.9 * cm
UTIL = ANCHO - 2 * MARGEN

SUPERFICIE = colors.HexColor("#fcfcfb")
TINTA = colors.HexColor("#0b0b0b")
TINTA2 = colors.HexColor("#52514e")
TINTA3 = colors.HexColor("#8d8c86")
AZUL = colors.HexColor("#2a78d6")
NARANJA = colors.HexColor("#eb6834")
AQUA = colors.HexColor("#1baf7a")
BIEN = colors.HexColor("#0ca30c")
MAL = colors.HexColor("#d03b3b")
PAPEL = colors.HexColor("#f2f4f6")
LINEA = colors.HexColor("#dedddA")


# --------------------------------------------------------------------------
# Primitivas
# --------------------------------------------------------------------------

def envolver(c, texto, fuente, tamano, ancho):
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


def parrafo(c, texto, x, y, ancho, tamano=13, fuente="Helvetica", color=TINTA2,
            interlinea=0.58):
    c.setFillColor(color)
    for linea in envolver(c, texto, fuente, tamano, ancho):
        c.setFont(fuente, tamano)
        c.drawString(x, y, linea)
        y -= interlinea * cm
    return y


def encabezado(c, kicker, titulo):
    y = ALTO - MARGEN - 0.2 * cm
    c.setFillColor(AZUL)
    c.rect(MARGEN, y + 0.42 * cm, 1.1 * cm, 0.11 * cm, stroke=0, fill=1)
    c.setFillColor(TINTA3)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGEN + 1.35 * cm, y + 0.38 * cm, kicker.upper())
    y -= 0.95 * cm
    c.setFillColor(TINTA)
    for linea in envolver(c, titulo, "Helvetica-Bold", 25, UTIL):
        c.setFont("Helvetica-Bold", 25)
        c.drawString(MARGEN, y, linea)
        y -= 0.95 * cm
    return y - 0.55 * cm


def pie(c, numero, total):
    c.setStrokeColor(LINEA)
    c.setLineWidth(0.6)
    c.line(MARGEN, MARGEN - 0.55 * cm, ANCHO - MARGEN, MARGEN - 0.55 * cm)
    c.setFillColor(TINTA3)
    c.setFont("Helvetica", 8.5)
    c.drawString(MARGEN, MARGEN - 1.05 * cm, "Proyecto 3 · Text-to-SQL con LoRA")
    c.drawRightString(ANCHO - MARGEN, MARGEN - 1.05 * cm, "%d / %d" % (numero, total))


def tiles(c, datos, y, ancho=UTIL, x0=MARGEN):
    """Fila de numeros grandes. Para un dato que es un titular, no un grafico."""
    paso = ancho / len(datos)
    alto = 2.9 * cm
    for i, (numero, etiqueta, nota) in enumerate(datos):
        x = x0 + i * paso
        c.setFillColor(PAPEL)
        c.roundRect(x, y - alto, paso - 0.35 * cm, alto, 0.22 * cm, stroke=0, fill=1)
        c.setFillColor(AZUL)
        c.rect(x, y - alto, 0.09 * cm, alto, stroke=0, fill=1)
        c.setFillColor(TINTA)
        c.setFont("Helvetica-Bold", 25)
        c.drawString(x + 0.55 * cm, y - 1.35 * cm, numero)
        c.setFillColor(TINTA2)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x + 0.55 * cm, y - 1.95 * cm, etiqueta)
        c.setFillColor(TINTA3)
        c.setFont("Helvetica", 9)
        c.drawString(x + 0.55 * cm, y - 2.45 * cm, nota)
    return y - alto - 0.5 * cm


def barras(c, datos, y, titulo=None, ancho=UTIL * 0.62, x0=MARGEN):
    """Barras horizontales, una sola serie, con etiqueta directa en cada una."""
    if titulo:
        c.setFillColor(TINTA2)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x0, y, titulo)
        y -= 0.72 * cm
    tope = max(v for _, v in datos)
    # El ancho de la columna de etiquetas sale del texto mas largo, para que
    # ninguna etiqueta toque su barra.
    etiqueta_ancho = max(c.stringWidth(n, "Helvetica", 11.5)
                         for n, _ in datos) + 0.55 * cm
    for nombre, valor in datos:
        largo = (ancho - etiqueta_ancho) * valor / tope
        c.setFillColor(TINTA2)
        c.setFont("Helvetica", 11.5)
        c.drawString(x0, y, nombre)
        c.setFillColor(AZUL)
        c.roundRect(x0 + etiqueta_ancho, y - 0.11 * cm, max(largo, 0.12 * cm),
                    0.46 * cm, 0.12 * cm, stroke=0, fill=1)
        c.setFillColor(TINTA)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x0 + etiqueta_ancho + largo + 0.25 * cm, y, "{:,}".format(valor))
        y -= 0.98 * cm
    return y


def flecha(c, x, y, largo=0.9 * cm, color=TINTA3):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(1.1)
    c.line(x, y, x + largo - 0.18 * cm, y)
    p = c.beginPath()
    p.moveTo(x + largo, y)
    p.lineTo(x + largo - 0.26 * cm, y + 0.13 * cm)
    p.lineTo(x + largo - 0.26 * cm, y - 0.13 * cm)
    p.close()
    c.drawPath(p, stroke=0, fill=1)


def flujo(c, pasos, y, x0=MARGEN, ancho=UTIL, alto=2.05 * cm, destacar=None):
    """Cajas encadenadas con flechas: un pipeline."""
    hueco = 1.05 * cm
    caja = (ancho - hueco * (len(pasos) - 1)) / len(pasos)
    for i, (titulo, detalle) in enumerate(pasos):
        x = x0 + i * (caja + hueco)
        resaltada = destacar is not None and i == destacar
        c.setFillColor(colors.HexColor("#e8f0fb") if resaltada else PAPEL)
        c.setStrokeColor(AZUL if resaltada else LINEA)
        c.setLineWidth(1.1 if resaltada else 0.7)
        c.roundRect(x, y - alto, caja, alto, 0.22 * cm, stroke=1, fill=1)
        c.setFillColor(TINTA)
        ty = y - 0.72 * cm
        for linea in envolver(c, titulo, "Helvetica-Bold", 11.5, caja - 0.5 * cm)[:2]:
            c.setFont("Helvetica-Bold", 11.5)
            c.drawString(x + 0.28 * cm, ty, linea)
            ty -= 0.45 * cm
        c.setFillColor(TINTA3)
        for linea in envolver(c, detalle, "Helvetica", 9.5, caja - 0.5 * cm)[:2]:
            c.setFont("Helvetica", 9.5)
            c.drawString(x + 0.28 * cm, ty, linea)
            ty -= 0.38 * cm
        if i < len(pasos) - 1:
            flecha(c, x + caja + 0.1 * cm, y - alto / 2, hueco - 0.2 * cm)
    return y - alto - 0.5 * cm


def codigo(c, lineas, y, x0=MARGEN, ancho=UTIL, titulo=None, estado=None,
           resaltar=()):
    """Panel monoespaciado. `estado` es ('texto', color) y lleva siempre texto."""
    alto = 0.58 * cm * len(lineas) + 0.6 * cm
    if titulo or estado:
        if titulo:
            c.setFillColor(TINTA2)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x0, y, titulo)
        if estado:
            texto, color = estado
            c.setFillColor(color)
            c.circle(x0 + ancho - 0.2 * cm - c.stringWidth(texto, "Helvetica-Bold", 9)
                     - 0.35 * cm, y + 0.1 * cm, 0.13 * cm, stroke=0, fill=1)
            c.setFont("Helvetica-Bold", 9)
            c.drawRightString(x0 + ancho - 0.2 * cm, y, texto)
        y -= 0.52 * cm
    c.setFillColor(PAPEL)
    c.roundRect(x0, y - alto + 0.3 * cm, ancho, alto, 0.18 * cm, stroke=0, fill=1)
    ty = y - 0.2 * cm
    for i, linea in enumerate(lineas):
        c.setFillColor(MAL if i in resaltar else TINTA)
        c.setFont("Courier-Bold" if i in resaltar else "Courier", 10.5)
        c.drawString(x0 + 0.35 * cm, ty, linea)
        ty -= 0.58 * cm
    return y - alto + 0.1 * cm


def lista(c, items, y, x0=MARGEN, ancho=UTIL, tamano=13, color_punto=AZUL):
    for item in items:
        c.setFillColor(color_punto)
        c.circle(x0 + 0.1 * cm, y + 0.13 * cm, 0.08 * cm, stroke=0, fill=1)
        y = parrafo(c, item, x0 + 0.5 * cm, y, ancho - 0.5 * cm, tamano=tamano)
        y -= 0.18 * cm
    return y


def filas_decision(c, filas, y, x0=MARGEN, ancho=UTIL):
    """Dos columnas: la condicion del enunciado y la decision que forzo."""
    izq = ancho * 0.42
    for condicion, decision in filas:
        c.setStrokeColor(LINEA)
        c.setLineWidth(0.6)
        c.line(x0, y + 0.48 * cm, x0 + ancho, y + 0.48 * cm)
        c.setFillColor(TINTA)
        c.setFont("Helvetica-Bold", 11.5)
        for linea in envolver(c, condicion, "Helvetica-Bold", 11.5, izq - 0.4 * cm)[:2]:
            c.drawString(x0, y, linea)
            y -= 0.5 * cm
        yd = y + 0.5 * cm * len(envolver(c, condicion, "Helvetica-Bold", 11.5,
                                         izq - 0.4 * cm)[:2])
        fin = parrafo(c, decision, x0 + izq, yd, ancho - izq, tamano=11,
                      color=TINTA2, interlinea=0.48)
        y = min(y, fin) - 0.62 * cm
    return y


# --------------------------------------------------------------------------
# Las 12 laminas
# --------------------------------------------------------------------------

def portada(c):
    c.setFillColor(AZUL)
    c.rect(0, ALTO - 0.55 * cm, ANCHO, 0.55 * cm, stroke=0, fill=1)
    c.setFillColor(NARANJA)
    c.rect(0, ALTO - 0.55 * cm, ANCHO * 0.28, 0.55 * cm, stroke=0, fill=1)

    y = ALTO - 5.4 * cm
    c.setFillColor(TINTA3)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(MARGEN, y + 1.5 * cm, "PROYECTO 3 · DEEP LEARNING 2026")
    c.setFillColor(TINTA)
    c.setFont("Helvetica-Bold", 44)
    c.drawString(MARGEN, y - 0.6 * cm, "Text-to-SQL con LoRA")
    c.setFillColor(TINTA2)
    c.setFont("Helvetica", 16)
    c.drawString(MARGEN, y - 1.75 * cm,
                 "Fine-tuning de Qwen2.5-Coder-1.5B para generar MySQL 8.4.10")

    y = y - 3.6 * cm
    c.setFillColor(PAPEL)
    c.roundRect(MARGEN, y - 1.5 * cm, UTIL, 1.9 * cm, 0.2 * cm, stroke=0, fill=1)
    c.setFillColor(TINTA2)
    c.setFont("Courier", 12)
    c.drawString(MARGEN + 0.5 * cm, y - 0.05 * cm,
                 "esquema (SHOW CREATE TABLE)  +  pregunta en espanol")
    c.setFillColor(AZUL)
    c.setFont("Courier-Bold", 12)
    c.drawString(MARGEN + 0.5 * cm, y - 0.85 * cm,
                 "-->  SELECT ... una sola consulta, determinista")

    c.setFillColor(TINTA2)
    c.setFont("Helvetica", 13)
    c.drawString(MARGEN, MARGEN + 0.9 * cm, "Cindy Gualim  ·  Gadiel Ocana")
    c.setFillColor(TINTA3)
    c.setFont("Helvetica", 11)
    c.drawString(MARGEN, MARGEN + 0.3 * cm, "Universidad del Valle")


def el_problema(c):
    y = encabezado(c, "el problema", "Una pregunta en espanol, una consulta correcta")
    mitad = UTIL / 2 - 0.6 * cm
    y2 = parrafo(c, "El evaluador entrega el esquema tal como lo devuelve "
                    "SHOW CREATE TABLE, con sus COMMENT, y una pregunta que indica "
                    "que columnas devolver.", MARGEN, y, mitad, tamano=12.5)
    codigo(c, ['"Cuantas reservas tiene cada tipo', ' de habitacion? Devuelve el',
               ' nombre del tipo y la cantidad."'], y2 - 0.5 * cm, MARGEN, mitad)

    x2 = MARGEN + mitad + 1.2 * cm
    flecha(c, MARGEN + mitad + 0.25 * cm, y - 2.4 * cm, 0.8 * cm, AZUL)
    codigo(c, ["SELECT rt.name, COUNT(*)", "FROM bookings b",
               "JOIN rooms r ON b.room_id = r.id",
               "JOIN room_types rt ON r.type_id = rt.id",
               "GROUP BY rt.id, rt.name"], y, x2, mitad)

    yb = MARGEN + 3.4 * cm
    c.setFillColor(AZUL)
    c.rect(MARGEN, yb - 0.1 * cm, 0.09 * cm, 1.5 * cm, stroke=0, fill=1)
    parrafo(c, "Se mide por exactitud por ejecucion: se comparan los resultados de "
               "ejecutar las dos consultas, nunca su texto. Y sobre bases y preguntas "
               "que no conocemos.", MARGEN + 0.45 * cm, yb + 1.05 * cm, UTIL - 1 * cm,
            tamano=13, color=TINTA)


def las_reglas(c):
    y = encabezado(c, "restricciones", "Cada condicion del enunciado es una decision en el codigo")
    filas_decision(c, [
        ("ONLY_FULL_GROUP_BY activo",
         "Las 32 plantillas agrupan por la clave primaria ademas de la etiqueta. "
         "Es el error que mas consultas mata en MySQL 8.4 por defecto."),
        ("Una consulta que modifique la base: -10",
         "extraer_sql() corta en el primer punto y coma y rechaza todo lo que "
         "empiece por INSERT, UPDATE, DELETE o DDL. Se pierde la pregunta, no los puntos."),
        ("Generacion determinista",
         "do_sample=False, num_beams=1 y temperature/top_p/top_k anulados para que "
         "no queden los valores por defecto del modelo."),
        ("Particion por esquema, no por pregunta",
         "Las bases veterinaria y hotel no comparten ni un nombre de tabla con las "
         "12 de entrenamiento."),
        ("30 s por pregunta, 5 min de carga",
         "Carga perezosa con candado, una sola vez; la autocorreccion tiene tope "
         "duro de 3 llamadas, contado fuera del modelo."),
    ], y - 0.1 * cm)


def pipeline(c):
    y = encabezado(c, "datos", "Como se construyo el dataset")
    y = flujo(c, [
        ("12 esquemas propios", "6-7 tablas, espanol, ingles y abreviados"),
        ("Poblador generico", "lee information_schema, semilla 2026"),
        ("32 plantillas", "tres niveles, umbrales p25/p50/p75"),
        ("MySQL 8.4.10", "se ejecutan los 2,464, usuario de solo lectura"),
        ("2,320 pares", "entrenamiento + 71 de dev"),
    ], y, destacar=3)

    y -= 0.45 * cm
    y = lista(c, [
        "Los umbrales de los filtros salen de muestrear los datos reales, no son "
        "constantes inventadas: un filtro que no coincide con ningun dato produce "
        "un par que no ensena nada.",
        "El poblador es generico a proposito. Sirve igual para los esquemas de "
        "validacion, y evita que los datos de las dos particiones se parezcan por "
        "haberlos escrito con la misma mano.",
    ], y, tamano=12.5)


def el_dataset(c):
    y = encabezado(c, "dataset", "2,464 pares, todos ejecutados en el motor")
    y = tiles(c, [
        ("2,464", "GENERADOS", "32 plantillas x 12 bases"),
        ("97.0%", "VALIDOS", "2,391 pares"),
        ("73", "DESCARTADOS", "todos por resultado vacio"),
        ("0", "ERRORES DE SINTAXIS", "y 0 de ONLY_FULL_GROUP_BY"),
    ], y)

    y -= 0.3 * cm
    ybar = barras(c, [("facil (peso 1)", 894), ("media (peso 2)", 862),
                      ("dificil (peso 3)", 564)], y,
                  titulo="PARES DE ENTRENAMIENTO POR NIVEL")

    x2 = MARGEN + UTIL * 0.66
    c.setFillColor(PAPEL)
    c.roundRect(x2, ybar - 0.2 * cm, UTIL * 0.34, 3.5 * cm, 0.2 * cm, stroke=0, fill=1)
    c.setFillColor(NARANJA)
    c.rect(x2, ybar - 0.2 * cm, 0.09 * cm, 3.5 * cm, stroke=0, fill=1)
    parrafo(c, "Por que se descarta un resultado vacio: con cero filas la "
               "comparacion por ejecucion no distingue una consulta correcta de una "
               "rota. Cualquier error que tambien devuelva vacio acierta.",
            x2 + 0.5 * cm, ybar + 2.75 * cm, UTIL * 0.34 - 1 * cm, tamano=11.5)


def el_hallazgo(c):
    y = encabezado(c, "hallazgo", "Buscabamos preguntas repetidas y encontramos ambiguedad")
    mitad = UTIL / 2 - 0.6 * cm

    y2 = codigo(c, ["vuelos.origen  --> aeropuertos.iata",
                    "vuelos.destino --> aeropuertos.iata"], y, MARGEN, mitad,
                titulo="DOS CLAVES FORANEAS A LA MISMA TABLA")
    parrafo(c, '"Cuantos vuelos tiene cada aeropuerto?" no determina por cual de '
               "las dos se une. Lo mismo pasa con prestamos, que apunta a clientes "
               "y a sucursales: ambas tienen una columna nombre.",
            MARGEN, y2 - 0.45 * cm, mitad, tamano=12)

    x2 = MARGEN + mitad + 1.2 * cm
    c.setFillColor(TINTA2)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x2, y, "PREGUNTAS AMBIGUAS, TRAS CADA CORRECCION")
    yb = barras(c, [("inicial", 19), ("desambiguacion", 13), ("redaccion", 0)],
                y - 0.75 * cm, ancho=mitad, x0=x2)

    c.setFillColor(MAL)
    c.circle(x2 + 0.12 * cm, yb - 0.3 * cm, 0.13 * cm, stroke=0, fill=1)
    parrafo(c, "Lo grave no era el par descartado sino el que se quedaba: entrenaba "
               "al modelo a adivinar.", x2 + 0.5 * cm, yb - 0.4 * cm, mitad - 0.5 * cm,
            tamano=12.5, color=TINTA)


def validacion_propia(c):
    y = encabezado(c, "validacion", "Dos esquemas que el modelo nunca vio")
    caja = UTIL / 2 - 1.4 * cm
    alto = 3.3 * cm

    for i, (titulo, detalle, color) in enumerate([
        ("ENTRENAMIENTO · 12 esquemas",
         "biblioteca, ecommerce, clinica, universidad, hr, restaurante, aerolinea, "
         "gym, inmobiliaria, logistica, streaming, banco", AZUL),
        ("VALIDACION · 2 esquemas",
         "veterinaria (espanol) y hotel (ingles). 14 tablas que no aparecen en "
         "ninguna base de entrenamiento.", NARANJA),
    ]):
        x = MARGEN + i * (caja + 2.8 * cm)
        c.setFillColor(PAPEL)
        c.roundRect(x, y - alto, caja, alto, 0.22 * cm, stroke=0, fill=1)
        c.setFillColor(color)
        c.rect(x, y - alto, 0.09 * cm, alto, stroke=0, fill=1)
        c.setFillColor(TINTA)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x + 0.45 * cm, y - 0.7 * cm, titulo)
        parrafo(c, detalle, x + 0.45 * cm, y - 1.3 * cm, caja - 0.9 * cm, tamano=10.5)

    cx = MARGEN + caja + 1.4 * cm
    c.setFillColor(TINTA)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(cx, y - alto / 2 - 0.1 * cm, "n = 0")
    c.setFillColor(TINTA3)
    c.setFont("Helvetica", 8.5)
    c.drawCentredString(cx, y - alto / 2 - 0.65 * cm, "sin interseccion")

    y = tiles(c, [
        ("40", "PREGUNTAS", "escritas a mano, no generadas"),
        ("13/13/14", "POR NIVEL", "facil / media / dificil"),
        ("81", "PESO TOTAL", "pesos 1, 2 y 3"),
        ("5", "CON ORDEN EXIGIDO", "el resto compara como conjunto"),
    ], y - alto - 0.6 * cm)

    parrafo(c, "Escribirlas a mano encontro dos defectos del poblador que ninguna "
               "prueba automatica habria encontrado: perros con fecha de nacimiento "
               "de persona, y score de resena llegando a 100 cuando su COMMENT dice "
               "1 a 5.", MARGEN, y - 0.1 * cm, UTIL, tamano=12.5)


def configuraciones(c):
    y = encabezado(c, "entrenamiento", "Dos configuraciones, un solo factor distinto")
    caja = UTIL / 2 - 0.6 * cm

    for i, (nombre, valor, nota) in enumerate([
        ("CONFIGURACION A", "r = 8", "~9M parametros entrenables"),
        ("CONFIGURACION B", "r = 32", "~36M parametros entrenables"),
    ]):
        x = MARGEN + i * (caja + 1.2 * cm)
        c.setFillColor(PAPEL)
        c.roundRect(x, y - 2.5 * cm, caja, 2.5 * cm, 0.22 * cm, stroke=0, fill=1)
        c.setFillColor(AZUL if i == 0 else NARANJA)
        c.rect(x, y - 2.5 * cm, 0.09 * cm, 2.5 * cm, stroke=0, fill=1)
        c.setFillColor(TINTA3)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 0.5 * cm, y - 0.7 * cm, nombre)
        c.setFillColor(TINTA)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(x + 0.5 * cm, y - 1.6 * cm, valor)
        c.setFillColor(TINTA2)
        c.setFont("Helvetica", 11)
        c.drawString(x + 0.5 * cm, y - 2.15 * cm, nota)

    y -= 3.1 * cm
    y = codigo(c, ["alpha=32   dropout=0.05   lr=2e-4   2 epocas   lote efectivo 16",
                   "modulos: q_proj k_proj v_proj o_proj gate_proj up_proj down_proj"],
               y, titulo="FIJO EN AMBAS")

    y -= 0.5 * cm
    c.setFillColor(AZUL)
    c.rect(MARGEN, y - 1.55 * cm, 0.09 * cm, 2.1 * cm, stroke=0, fill=1)
    parrafo(c, "alpha se mantiene en 32 a proposito. Escalarlo con el rank cambiaria "
               "a la vez la capacidad del adapter y la magnitud de su contribucion, y "
               "la diferencia no se podria atribuir a ninguno de los dos.",
            MARGEN + 0.45 * cm, y + 0.4 * cm, UTIL - 1 * cm, tamano=12.5, color=TINTA)


def que_falla(c):
    y = encabezado(c, "baseline medido", "El modelo sin adapter ya parte de 0.580")
    mitad = UTIL / 2 - 0.6 * cm

    yb = barras(c, [("facil", 12), ("media", 20), ("dificil", 15)], y,
                titulo="PESO ACERTADO SOBRE EL DISPONIBLE  (12/13 · 20/26 · 15/42)",
                ancho=mitad)
    parrafo(c, "Acierta casi todo lo facil y se derrumba en lo dificil, que pesa 3. "
               "Ahi esta el margen, y tambien la dificultad: el umbral de +0.15 de "
               "mejora se mide contra una base alta.",
            MARGEN, yb - 0.35 * cm, mitad, tamano=12)

    x2 = MARGEN + mitad + 1.2 * cm
    y2 = codigo(c, ["SELECT T1.country, SUM(T2.total_amount)...",
                    "FROM bookings AS T1",
                    "JOIN payments AS T2 ON T1.id = T2.booking_id",
                    "GROUP BY T1.country"], y, x2, mitad,
                titulo="PREGUNTA 38 · GENERADO", estado=("tabla inexistente", MAL),
                resaltar={2})
    parrafo(c, "La base hotel no tiene ninguna tabla payments: el modelo la invento "
               "a partir de lo que sabe de otros esquemas, en vez de leer el que "
               "tiene delante. No es un error de razonamiento sino de anclaje, y es "
               "justo lo que 2,320 ejemplos pueden corregir.",
            x2, y2 - 0.45 * cm, mitad, tamano=12, color=TINTA)


def experimento(c):
    y = encabezado(c, "inferencia", "Tres variantes sobre el mismo adapter")
    y = flujo(c, [
        ("Directa", "el prompt del contrato, una sola generacion"),
        ("Few-shot", "tres ejemplos resueltos sobre un esquema inventado"),
        ("Autocorreccion", "ejecuta la consulta y la reescribe con el error"),
    ], y, alto=1.9 * cm)

    y -= 0.4 * cm
    y = codigo(c, ["generar  -->  ejecutar(sql)  -->  error del motor  -->  regenerar",
                   "tope de 3 llamadas, contado fuera del modelo"],
               y, titulo="EL CICLO DE AUTOCORRECCION")

    y -= 0.6 * cm
    c.setFillColor(MAL)
    c.circle(MARGEN + 0.12 * cm, y + 0.13 * cm, 0.13 * cm, stroke=0, fill=1)
    c.setFillColor(TINTA)
    c.setFont("Helvetica-Bold", 12.5)
    c.drawString(MARGEN + 0.5 * cm, y, "Su limite duro")
    y -= 0.55 * cm
    parrafo(c, "Solo puede arreglar lo que el motor reporta: Unknown column, Table "
               "doesn't exist. No hace nada por un resultado distinto, donde la "
               "consulta corre sin error y nada le indica al modelo que esta "
               "equivocada.", MARGEN + 0.5 * cm, y, UTIL - 0.5 * cm, tamano=12.5)


def analisis_errores(c):
    y = encabezado(c, "errores", "Donde se pierde el peso, medido en el baseline")
    mitad = UTIL / 2 - 0.6 * cm
    x2 = MARGEN + mitad + 1.2 * cm

    yb = barras(c, [("columna inexistente", 12), ("join", 8), ("agregacion", 8),
                    ("tabla inexistente", 3), ("sintaxis", 3)], y,
                titulo="PESO PERDIDO POR CATEGORIA  ·  34 DE 81", ancho=mitad)

    c.setFillColor(AZUL)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(x2, y, "15 DE LOS 34 PUNTOS SON ANCLAJE AL ESQUEMA")
    yd = parrafo(c, "Columna y tabla inexistente suman 15 del peso perdido: el 44%. "
                    "Son los unicos errores que el motor reporta de forma explicita, "
                    "asi que son los que el fine-tuning y la autocorreccion pueden "
                    "atacar. Los de agregacion y join exigen entender la pregunta.",
                 x2, y - 0.75 * cm, mitad, tamano=12)
    yd = parrafo(c, "13 preguntas falladas de 40, pero no cuestan lo mismo: fallar "
                    "una dificil equivale a fallar tres faciles.",
                 x2, yd - 0.3 * cm, mitad, tamano=12)

    # La fila de chips arranca debajo de la mas baja de las dos columnas.
    y = min(yb, yd) - 0.9 * cm
    for titulo, color, chips in [
        ("LO QUE EL MOTOR REPORTA", AZUL,
         ["sintaxis", "tabla inexistente", "columna inexistente"]),
        ("LO QUE HAY QUE INFERIR", NARANJA,
         ["join", "agregacion", "filtro", "resultado distinto"]),
    ]:
        c.setFillColor(color)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawString(MARGEN, y, titulo)
        cx = MARGEN + 4.9 * cm
        for chip in chips:
            ancho_chip = c.stringWidth(chip, "Helvetica", 10.5) + 0.85 * cm
            c.setFillColor(PAPEL)
            c.roundRect(cx, y - 0.2 * cm, ancho_chip, 0.68 * cm, 0.33 * cm,
                        stroke=0, fill=1)
            c.setFillColor(color)
            c.circle(cx + 0.33 * cm, y + 0.13 * cm, 0.1 * cm, stroke=0, fill=1)
            c.setFillColor(TINTA)
            c.setFont("Helvetica", 10.5)
            c.drawString(cx + 0.58 * cm, y + 0.02 * cm, chip)
            cx += ancho_chip + 0.25 * cm
        y -= 1.15 * cm


def prediccion(c):
    y = encabezado(c, "prediccion", "Que esperamos en la evaluacion oculta")

    c.setFillColor(PAPEL)
    c.roundRect(MARGEN, y - 4.3 * cm, UTIL * 0.46, 4.3 * cm, 0.25 * cm, stroke=0, fill=1)
    c.setFillColor(AZUL)
    c.rect(MARGEN, y - 4.3 * cm, 0.1 * cm, 4.3 * cm, stroke=0, fill=1)
    c.setFillColor(TINTA3)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(MARGEN + 0.6 * cm, y - 0.8 * cm, "EX PONDERADA ESPERADA")
    c.setFillColor(TINTA)
    c.setFont("Helvetica-Bold", 52)
    c.drawString(MARGEN + 0.55 * cm, y - 2.4 * cm, "0.55")

    # Franja de rango: 0.45 a 0.60 sobre un eje de 0 a 1.
    bx, bw = MARGEN + 0.6 * cm, UTIL * 0.46 - 1.2 * cm
    by = y - 3.3 * cm
    c.setFillColor(colors.HexColor("#e6e5e2"))
    c.roundRect(bx, by, bw, 0.3 * cm, 0.15 * cm, stroke=0, fill=1)
    c.setFillColor(AZUL)
    c.roundRect(bx + bw * 0.45, by, bw * 0.20, 0.3 * cm, 0.15 * cm, stroke=0, fill=1)
    c.setFillColor(TINTA)
    c.rect(bx + bw * 0.55 - 0.04 * cm, by - 0.12 * cm, 0.08 * cm, 0.54 * cm,
           stroke=0, fill=1)
    c.setFillColor(TINTA2)
    c.setFont("Helvetica", 9.5)
    c.drawString(bx, by - 0.6 * cm, "0.0")
    c.drawCentredString(bx + bw * 0.55, by - 0.6 * cm, "rango 0.45 - 0.65")
    c.drawRightString(bx + bw, by - 0.6 * cm, "1.0")

    x2 = MARGEN + UTIL * 0.5
    ancho2 = UTIL * 0.5
    c.setFillColor(TINTA3)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(x2, y - 0.8 * cm, "MEJORA SOBRE EL MODELO SIN ADAPTER")
    c.setFillColor(TINTA)
    c.setFont("Helvetica-Bold", 30)
    c.drawString(x2, y - 1.85 * cm, "+0.08 a +0.19")
    c.setFillColor(NARANJA)
    c.circle(x2 + 0.12 * cm, y - 2.45 * cm, 0.12 * cm, stroke=0, fill=1)
    c.setFillColor(TINTA2)
    c.setFont("Helvetica", 11)
    c.drawString(x2 + 0.45 * cm, y - 2.5 * cm,
                 "en riesgo: el umbral del enunciado es +0.15")

    lista(c, [
        "El baseline medido es alto, 0.580. La mejora se mide contra esa base, asi "
        "que el margen es estrecho por arriba.",
        "El techo optimista: si el adapter arreglara todo el anclaje al esquema, la "
        "EX subiria a 0.765 y la mejora seria +0.185.",
        "Descontamos 0.15 sobre la evaluacion oculta: nuestra validacion la "
        "escribimos nosotros, sobre esquemas que diseniamos nosotros.",
    ], y - 3.3 * cm, x2, ancho2, tamano=11.5)


LAMINAS = [portada, el_problema, las_reglas, pipeline, el_dataset, el_hallazgo,
           validacion_propia, configuraciones, que_falla, experimento,
           analisis_errores, prediccion]


def main():
    if len(LAMINAS) > 12:
        raise SystemExit("son %d diapositivas y el maximo es 12" % len(LAMINAS))

    destino = RAIZ / "presentacion.pdf"
    c = rl_canvas.Canvas(str(destino), pagesize=landscape(A4))
    for i, lamina in enumerate(LAMINAS, 1):
        c.setFillColor(SUPERFICIE)
        c.rect(0, 0, ANCHO, ALTO, stroke=0, fill=1)
        lamina(c)
        if i > 1:
            pie(c, i, len(LAMINAS))
        c.showPage()
    c.save()
    print("%s con %d diapositivas" % (destino, len(LAMINAS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

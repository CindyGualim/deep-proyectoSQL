"""Genera informe.pdf, el documento escrito del Proyecto 3.

Formato pedido: Times New Roman 11 para el cuerpo y 14 para los titulos, con
margenes de 2.54 cm. Las fuentes Times-Roman y Times-Bold que trae reportlab son
metricamente equivalentes a Times New Roman.

El anexo lleva el enlace al repositorio con el icono de GitHub
(assets/github.svg, de simple-icons, CC0).

    pip install reportlab svglib
    python scripts/generar_informe.py
"""

import pathlib
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)

RAIZ = pathlib.Path(__file__).resolve().parent.parent
REPO = "https://github.com/CindyGualim/deep-proyectoSQL"
MARGEN = 2.54 * cm

# Datos de la caratula. Si la seccion queda vacia, esa linea no se imprime.
CURSO = "Deep Learning"
SECCION = ""
CATEDRATICO = "Ing. Kevin Recinos"
TRABAJO = "Proyecto 3"
INTEGRANTES = ["Cindy Mishelle Gualim Perez", "Gadiel Oca&ntilde;a"]
FECHA = "25 de octubre de 2026"

TINTA = colors.HexColor("#111111")
TINTA2 = colors.HexColor("#444444")
LINEA = colors.HexColor("#999999")
SUAVE = colors.HexColor("#f2f4f6")

CUERPO = ParagraphStyle(
    "cuerpo", fontName="Times-Roman", fontSize=11, leading=15.4,
    alignment=TA_JUSTIFY, textColor=TINTA, spaceAfter=7,
)
TITULO1 = ParagraphStyle(
    "titulo1", fontName="Times-Bold", fontSize=14, leading=18,
    textColor=TINTA, spaceBefore=14, spaceAfter=7,
)
TITULO2 = ParagraphStyle(
    "titulo2", fontName="Times-Bold", fontSize=11.5, leading=15,
    textColor=TINTA, spaceBefore=9, spaceAfter=4,
)
PORTADA_TITULO = ParagraphStyle(
    "portada", fontName="Times-Bold", fontSize=20, leading=25,
    textColor=TINTA, spaceAfter=6,
)
PORTADA_SUB = ParagraphStyle(
    "portadasub", fontName="Times-Roman", fontSize=12.5, leading=17,
    textColor=TINTA2, spaceAfter=3,
)
CARATULA_UNIV = ParagraphStyle(
    "caratulauniv", fontName="Times-Bold", fontSize=12, leading=16,
    alignment=TA_CENTER, textColor=TINTA, spaceAfter=22,
)
CARATULA_LINEA = ParagraphStyle(
    "caratulalinea", fontName="Times-Roman", fontSize=11.5, leading=15,
    alignment=TA_CENTER, textColor=TINTA, spaceAfter=20,
)
CARATULA_PIE = ParagraphStyle(
    "caratulapie", fontName="Times-Bold", fontSize=11.5, leading=15,
    alignment=TA_CENTER, textColor=TINTA,
)
CELDA = ParagraphStyle(
    "celda", fontName="Times-Roman", fontSize=10, leading=13, textColor=TINTA,
)
CELDA_TIT = ParagraphStyle(
    "celdatit", fontName="Times-Bold", fontSize=10, leading=13, textColor=TINTA,
)
PIE_TABLA = ParagraphStyle(
    "pietabla", fontName="Times-Italic", fontSize=9.5, leading=12.5,
    textColor=TINTA2, spaceBefore=3, spaceAfter=9,
)
CODIGO = ParagraphStyle(
    "codigo", fontName="Courier", fontSize=9, leading=12, textColor=TINTA,
    spaceBefore=4, spaceAfter=8,
)


def p(texto, estilo=CUERPO):
    return Paragraph(texto, estilo)


def tabla(filas, anchos, pie=None):
    datos = [[Paragraph(c, CELDA_TIT if i == 0 else CELDA) for c in fila]
             for i, fila in enumerate(filas)]
    t = Table(datos, colWidths=anchos, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SUAVE),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, LINEA),
        ("LINEBELOW", (0, -1), (-1, -1), 0.6, LINEA),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    if pie:
        return [t, p(pie, PIE_TABLA)]
    return [t, Spacer(1, 9)]


def icono_github(alto=12):
    """Devuelve el icono como flowable, o None si no esta el archivo."""
    ruta = RAIZ / "assets" / "github.svg"
    if not ruta.is_file():
        return None
    try:
        from svglib.svglib import svg2rlg
    except ImportError:
        return None
    dibujo = svg2rlg(str(ruta))
    if dibujo is None:
        return None
    escala = alto / dibujo.height
    dibujo.width *= escala
    dibujo.height *= escala
    dibujo.scale(escala, escala)
    return dibujo


def numero_pagina(canvas, doc):
    canvas.saveState()
    canvas.setFont("Times-Roman", 9)
    canvas.setFillColor(TINTA2)
    if doc.page > 1:
        canvas.drawCentredString(A4[0] / 2, MARGEN - 1.1 * cm, str(doc.page))
        canvas.setFont("Times-Italic", 8.5)
        canvas.drawString(MARGEN, MARGEN - 1.1 * cm,
                          "Proyecto 3 - Text-to-SQL con LoRA")
    canvas.restoreState()


def contenido():
    f = []

    # ---------------- Caratula ----------------
    f.append(Spacer(1, 0.2 * cm))
    f.append(p("UNIVERSIDAD DEL VALLE DE GUATEMALA", CARATULA_UNIV))
    f.append(p(CURSO, CARATULA_LINEA))
    if SECCION:
        f.append(p("Secci&oacute;n &ndash; %s" % SECCION, CARATULA_LINEA))
    f.append(p(CATEDRATICO, CARATULA_LINEA))

    logo = RAIZ / "assets" / "uvg-logo.png"
    if logo.is_file():
        ancho = 4.3 * cm
        imagen = Image(str(logo), width=ancho, height=ancho * 1.48)
        imagen.hAlign = "CENTER"
        f.append(Spacer(1, 0.9 * cm))
        f.append(imagen)
        f.append(Spacer(1, 1.1 * cm))
    else:
        f.append(Spacer(1, 2.2 * cm))

    f.append(p(TRABAJO, CARATULA_LINEA))
    f.append(p("Text-to-SQL: fine-tuning de un LLM con LoRA", CARATULA_LINEA))
    f.append(Spacer(1, 0.8 * cm))
    for integrante in INTEGRANTES:
        f.append(p(integrante, CARATULA_LINEA))
    f.append(Spacer(1, 1.6 * cm))
    f.append(p("GUATEMALA, %s" % FECHA, CARATULA_PIE))
    f.append(PageBreak())

    # ---------------- 1 ----------------
    f.append(p("1. Objetivo y alcance", TITULO1))
    f.append(p(
        "El objetivo es ajustar con LoRA un modelo peque&ntilde;o para que, dado el "
        "esquema de una base de datos en el formato que devuelve "
        "<font face='Courier' size='10'>SHOW CREATE TABLE</font> y una pregunta en "
        "espa&ntilde;ol, genere una consulta MySQL correcta. El criterio de acierto "
        "es la exactitud por ejecuci&oacute;n: se comparan los resultados de ejecutar "
        "la consulta generada y la de referencia, nunca su texto."))
    f.append(p(
        "Este informe documenta el dataset, la validaci&oacute;n propia, el baseline "
        "medido, las dos configuraciones de LoRA, el experimento de inferencia, el "
        "an&aacute;lisis de errores y la predicci&oacute;n razonada del desempe&ntilde;o "
        "en la evaluaci&oacute;n oculta. Los n&uacute;meros que aparecen fueron medidos "
        "ejecutando el c&oacute;digo del repositorio, salvo donde se indica "
        "expl&iacute;citamente que un resultado est&aacute; pendiente."))

    # ---------------- 2 ----------------
    f.append(p("2. Construcci&oacute;n del dataset", TITULO1))
    f.append(p("2.1 Esquemas propios", TITULO2))
    f.append(p(
        "Se escribieron 12 esquemas de 6 a 7 tablas, con "
        "<font face='Courier' size='10'>COMMENT</font> en cada tabla y cada columna, "
        "porque es exactamente lo que el evaluador entrega al modelo. La mezcla es "
        "deliberada: cinco en espa&ntilde;ol, tres en ingl&eacute;s, dos con nombres "
        "abreviados (<font face='Courier' size='10'>pac</font>, "
        "<font face='Courier' size='10'>med</font>, "
        "<font face='Courier' size='10'>mbr</font>, "
        "<font face='Courier' size='10'>cls</font>) y dos mezclados, uno con clave "
        "primaria no num&eacute;rica y otro con tabla puente. El enunciado anuncia esas "
        "mismas condiciones para la evaluaci&oacute;n oculta."))
    f.append(p(
        "Los datos no se escribieron a mano: un poblador gen&eacute;rico lee "
        "<font face='Courier' size='10'>information_schema</font>, ordena las tablas "
        "topol&oacute;gicamente por sus claves for&aacute;neas y genera valores con "
        "semilla fija seg&uacute;n el tipo de cada columna y pistas de su nombre. "
        "Mantiene coherencia cronol&oacute;gica, respeta restricciones "
        "<font face='Courier' size='10'>UNIQUE</font> y acota cada valor al rango del "
        "tipo declarado. El resultado son 78 tablas y 9,525 filas reproducibles."))

    f.append(p("2.2 Generaci&oacute;n y validaci&oacute;n de los pares", TITULO2))
    f.append(p(
        "Se escribieron 32 plantillas param&eacute;tricas repartidas en los tres "
        "niveles de la evaluaci&oacute;n: 11 f&aacute;ciles de una sola tabla, 10 "
        "medias con <font face='Courier' size='10'>JOIN</font>, "
        "<font face='Courier' size='10'>GROUP BY</font> y "
        "<font face='Courier' size='10'>HAVING</font>, y 11 dif&iacute;ciles con "
        "subconsultas correlacionadas, <font face='Courier' size='10'>WITH</font>, "
        "funciones de ventana y fechas. Los umbrales de los filtros no son constantes "
        "inventadas: se muestrean 80 filas de cada tabla y se usan los cuantiles p25, "
        "p50 y p75, de modo que las consultas devuelvan resultados no vac&iacute;os."))
    f.append(p(
        "Los 2,464 pares generados se ejecutaron en MySQL 8.4.10 con un usuario de "
        "solo lectura, replicando la condici&oacute;n del evaluador."))
    f.extend(tabla([
        ["Resultado", "Pares", "Porcentaje"],
        ["Generados", "2,464", "100%"],
        ["V&aacute;lidos", "2,391", "97.0%"],
        ["Descartados por resultado vac&iacute;o", "73", "3.0%"],
        ["Descartados por error de sintaxis", "0", "0%"],
        ["Descartados por ambig&uuml;edad de la pregunta", "0", "0%"],
    ], [8.2 * cm, 3.2 * cm, 3.2 * cm],
        "Tabla 1. Validaci&oacute;n por ejecuci&oacute;n de los pares generados. "
        "El detalle por par est&aacute; en datos/descartes.csv."))
    f.append(p(
        "Se descartan los pares cuyo resultado es vac&iacute;o por una raz&oacute;n "
        "concreta: con cero filas, la comparaci&oacute;n por ejecuci&oacute;n no "
        "distingue una consulta correcta de una equivocada, porque cualquier error que "
        "tambi&eacute;n devuelva vac&iacute;o cuenta como acierto. Quedan 2,320 pares "
        "de entrenamiento (894 f&aacute;ciles, 862 medios, 564 dif&iacute;ciles) y 71 "
        "reservados para vigilar la p&eacute;rdida durante el entrenamiento."))

    f.append(p("2.3 Ambig&uuml;edad detectada y corregida", TITULO2))
    f.append(p(
        "La verificaci&oacute;n de preguntas duplicadas no encontr&oacute; "
        "repetici&oacute;n sino ambig&uuml;edad real. La tabla "
        "<font face='Courier' size='10'>vuelos</font> tiene dos claves for&aacute;neas "
        "a <font face='Courier' size='10'>aeropuertos</font> "
        "(<font face='Courier' size='10'>origen</font> y "
        "<font face='Courier' size='10'>destino</font>), y "
        "<font face='Courier' size='10'>prestamos</font> apunta a "
        "<font face='Courier' size='10'>clientes</font> y a "
        "<font face='Courier' size='10'>sucursales</font>, que adem&aacute;s tienen "
        "ambas una columna <font face='Courier' size='10'>nombre</font>. El problema "
        "no era el par descartado sino el que se conservaba: entrenaba al modelo a "
        "adivinar. Se a&ntilde;adi&oacute; desambiguaci&oacute;n autom&aacute;tica y se "
        "corrigieron cuatro redacciones que omit&iacute;an el nombre de la tabla. Las "
        "preguntas ambiguas pasaron de 19 a 13 y finalmente a 0."))

    # ---------------- 3 ----------------
    f.append(p("3. Validaci&oacute;n propia", TITULO1))
    f.append(p(
        "Se construyeron dos esquemas que no aparecen en el entrenamiento, "
        "<font face='Courier' size='10'>veterinaria</font> (espa&ntilde;ol) y "
        "<font face='Courier' size='10'>hotel</font> (ingl&eacute;s), y se escribieron "
        "a mano 40 preguntas con su consulta de referencia: 13 f&aacute;ciles, 13 "
        "medias y 14 dif&iacute;ciles, con peso total 81. Las preguntas est&aacute;n en "
        "espa&ntilde;ol tambi&eacute;n sobre el esquema en ingl&eacute;s. Cinco exigen "
        "un orden de filas expl&iacute;cito; el resto se compara como conjunto."))
    f.append(p(
        "La partici&oacute;n es por esquema, no por pregunta: la intersecci&oacute;n "
        "entre las bases de entrenamiento y las de validaci&oacute;n es vac&iacute;a, y "
        "no comparten ni un solo nombre de tabla. Las 40 consultas de referencia se "
        "verificaron ejecut&aacute;ndolas; todas corren y devuelven filas."))
    f.append(p(
        "Escribir las preguntas a mano revel&oacute; dos defectos del poblador que "
        "ninguna prueba autom&aacute;tica habr&iacute;a encontrado: las mascotas "
        "recib&iacute;an fechas de nacimiento de persona, y la calificaci&oacute;n de "
        "las rese&ntilde;as llegaba a 100 cuando su "
        "<font face='Courier' size='10'>COMMENT</font> indica un rango de 1 a 5."))

    # ---------------- 4 ----------------
    f.append(p("4. Baseline: el modelo sin adapter", TITULO1))
    f.append(p(
        "El baseline es el mismo <font face='Courier' size='10'>solucion.py</font> con "
        "<font face='Courier' size='10'>usar_adapter: false</font>, es decir, el modelo "
        "base con exactamente el mismo prompt. Se evalu&oacute; sobre las 40 preguntas "
        "de la validaci&oacute;n propia."))
    f.extend(tabla([
        ["Nivel", "Preguntas acertadas", "Peso acertado", "EX del nivel"],
        ["F&aacute;cil (peso 1)", "12 / 13", "12 / 13", "0.92"],
        ["Media (peso 2)", "10 / 13", "20 / 26", "0.77"],
        ["Dif&iacute;cil (peso 3)", "5 / 14", "15 / 42", "0.36"],
        ["<b>Total</b>", "<b>27 / 40</b>", "<b>47 / 81</b>", "<b>0.580</b>"],
    ], [4.2 * cm, 3.9 * cm, 3.3 * cm, 3.2 * cm],
        "Tabla 2. EX ponderada del modelo base sobre la validaci&oacute;n propia."))
    f.append(p(
        "El resultado es m&aacute;s alto de lo que anticip&aacute;bamos y tiene una "
        "consecuencia directa sobre la nota: el enunciado otorga 10 puntos si el adapter "
        "mejora la EX en al menos 0.15, y esa mejora se mide contra una base que ya est&aacute; "
        "en 0.580. El margen por arriba es estrecho."))
    f.append(p(
        "Ocho de las 40 consultas generadas ni siquiera ejecutan. El tiempo medido fue "
        "de 26.8 segundos por pregunta con un m&aacute;ximo de 76.1, pero esa "
        "medici&oacute;n se hizo en CPU; el contrato de 30 segundos debe verificarse en "
        "el entorno de evaluaci&oacute;n, una GPU T4, donde se espera un orden de "
        "magnitud menos."))

    # ---------------- 5 ----------------
    f.append(p("5. Configuraciones de LoRA", TITULO1))
    f.append(p(
        "Se definieron dos configuraciones que difieren en un solo factor, el rank. "
        "Todo lo dem&aacute;s se mantiene fijo: "
        "<font face='Courier' size='10'>alpha=32</font>, "
        "<font face='Courier' size='10'>dropout=0.05</font>, "
        "<font face='Courier' size='10'>lr=2e-4</font>, dos &eacute;pocas, lote efectivo "
        "16, planificador coseno, semilla 2026 y los mismos siete m&oacute;dulos "
        "objetivo. Mantener <font face='Courier' size='10'>alpha</font> constante es "
        "intencional: escalarlo con el rank cambiar&iacute;a a la vez la capacidad del "
        "adapter y la magnitud de su contribuci&oacute;n, y la diferencia no se "
        "podr&iacute;a atribuir a ninguno de los dos."))
    f.extend(tabla([
        ["", "Configuraci&oacute;n A", "Configuraci&oacute;n B"],
        ["Rank", "8", "32"],
        ["Par&aacute;metros entrenables", "pendiente", "pendiente"],
        ["Tiempo de entrenamiento", "pendiente", "pendiente"],
        ["P&eacute;rdida final (dev)", "pendiente", "pendiente"],
        ["EX en validaci&oacute;n propia", "pendiente", "pendiente"],
    ], [5.6 * cm, 4.5 * cm, 4.5 * cm],
        "Tabla 3. Las dos configuraciones. El entrenamiento requiere GPU y se ejecuta "
        "con notebooks/02_entrenamiento.ipynb en Google Colab."))
    f.append(p(
        "<b>Hip&oacute;tesis, escritas antes de entrenar.</b> La configuraci&oacute;n A, "
        "con unos 9 millones de par&aacute;metros entrenables, deber&iacute;a bastar "
        "para aprender el formato de salida y el anclaje al esquema, que es el error "
        "dominante del modelo base. La configuraci&oacute;n B, con cuatro veces esa "
        "capacidad, solo deber&iacute;a ganar en el nivel dif&iacute;cil, y con mayor "
        "riesgo de sobreajuste a las 32 plantillas. La se&ntilde;al a vigilar es la "
        "p&eacute;rdida de validaci&oacute;n: si A y B coinciden, la capacidad extra no "
        "se est&aacute; usando. Ante un empate se entrega A."))

    # ---------------- 6 ----------------
    f.append(p("6. Experimento de inferencia", TITULO1))
    f.append(p(
        "Se comparan tres variantes sobre el mismo adapter y el mismo criterio de EX, "
        "cambiando &uacute;nicamente c&oacute;mo se arma la inferencia: la directa, una "
        "con tres ejemplos resueltos en el prompt (few-shot) sobre un esquema inventado "
        "que no pertenece a ninguna partici&oacute;n, y una con autocorrecci&oacute;n."))
    f.append(p(
        "La autocorrecci&oacute;n usa la funci&oacute;n "
        "<font face='Courier' size='10'>ejecutar(sql)</font> que ofrece el evaluador. El "
        "ciclo ejecuta la consulta; si corre y devuelve filas, la entrega; si falla, "
        "vuelve a generar agregando al prompt la consulta anterior y el error del motor. "
        "Una consulta que se ejecuta pero devuelve cero filas se guarda como respaldo "
        "antes que entregar una rota. El contador de llamadas vive fuera del modelo, de "
        "modo que el tope de tres por pregunta se respeta siempre."))
    f.append(p(
        "<b>Hip&oacute;tesis.</b> La autocorrecci&oacute;n deber&iacute;a producir la "
        "mayor ganancia, concentrada en los errores de columna y tabla inexistente, que "
        "son los &uacute;nicos que el motor reporta de forma expl&iacute;cita y "
        "accionable. No esperamos ninguna mejora en los casos de resultado distinto: "
        "ah&iacute; la consulta corre sin error y el modelo no recibe se&ntilde;al alguna "
        "de que est&aacute; equivocada. Ese es el l&iacute;mite duro del m&eacute;todo. "
        "El few-shot deber&iacute;a aportar poco despu&eacute;s del ajuste fino; si "
        "aportara mucho, ser&iacute;a se&ntilde;al de que el adapter no aprendi&oacute; "
        "el formato."))

    # ---------------- 7 ----------------
    f.append(p("7. An&aacute;lisis de errores", TITULO1))
    f.append(p(
        "Los fallos se clasifican autom&aacute;ticamente en siete categor&iacute;as. Las "
        "de sintaxis, tabla y columna inexistente se deducen del c&oacute;digo de error "
        "de MySQL; las de join, agregaci&oacute;n y filtro se deducen comparando la forma "
        "de la consulta generada con la de referencia, es decir, el conjunto de tablas, "
        "la presencia de agregados y las condiciones."))
    f.extend(tabla([
        ["Categor&iacute;a", "Preguntas", "Peso perdido", "% del peso perdido"],
        ["Columna inexistente", "5", "12", "35%"],
        ["Join", "3", "8", "24%"],
        ["Agregaci&oacute;n", "3", "8", "24%"],
        ["Tabla inexistente", "1", "3", "9%"],
        ["Sintaxis", "1", "3", "9%"],
        ["<b>Total</b>", "<b>13</b>", "<b>34</b>", "<b>100%</b>"],
    ], [5.0 * cm, 2.6 * cm, 3.2 * cm, 3.8 * cm],
        "Tabla 4. Errores del baseline sobre la validaci&oacute;n propia. Se reporta el "
        "peso perdido porque es lo que mueve la m&eacute;trica: fallar una pregunta "
        "dif&iacute;cil cuesta lo mismo que fallar tres f&aacute;ciles."))
    f.append(p(
        "El 44% del peso perdido corresponde a anclaje al esquema: columna y tabla "
        "inexistente suman 15 de los 34 puntos. Un ejemplo representativo es la pregunta "
        "38, donde el modelo escribi&oacute; "
        "<font face='Courier' size='10'>JOIN payments</font> sobre la base "
        "<font face='Courier' size='10'>hotel</font>, que no tiene ninguna tabla con ese "
        "nombre: la invent&oacute; a partir de lo que sabe de otros esquemas en lugar de "
        "leer el que ten&iacute;a delante. No es un error de razonamiento sino de "
        "anclaje, y es precisamente lo que 2,320 ejemplos con el esquema en el prompt "
        "pueden corregir."))

    # ---------------- 8 ----------------
    f.append(p("8. Predicci&oacute;n justificada de la EX oculta", TITULO1))
    f.append(p(
        "<b>Predicci&oacute;n: EX entre 0.45 y 0.65, con 0.55 como valor m&aacute;s "
        "probable. Mejora sobre el modelo sin adapter de +0.08 a +0.19.</b>"))
    f.append(p(
        "El razonamiento parte del baseline medido, 0.580 sobre nuestra validaci&oacute;n. "
        "A ese n&uacute;mero le descontamos alrededor de 0.15 para la evaluaci&oacute;n "
        "oculta, porque nuestras preguntas las escribimos nosotros sobre esquemas que "
        "dise&ntilde;amos nosotros, y el docente no conoce nuestras convenciones de "
        "redacci&oacute;n."))
    f.append(p(
        "El techo optimista del adapter se puede calcular: si corrigiera todo el anclaje "
        "al esquema, recuperar&iacute;a los 15 puntos de peso de columna y tabla "
        "inexistente, lo que llevar&iacute;a la EX de 0.580 a 0.765 y dar&iacute;a una "
        "mejora de +0.185. Es un techo, no una expectativa: lo realista es recuperar "
        "entre la mitad y dos tercios de esos puntos, m&aacute;s algo de los errores de "
        "agregaci&oacute;n, donde el formato consistente del dataset deber&iacute;a "
        "ayudar con <font face='Courier' size='10'>ONLY_FULL_GROUP_BY</font>."))
    f.append(p(
        "La limitaci&oacute;n m&aacute;s seria que asumimos es que el dataset proviene de "
        "32 plantillas y no de lenguaje natural libre. El modelo ver&aacute; formas de "
        "preguntar que no aparecen en el entrenamiento. Lo mitigamos con dos "
        "par&aacute;frasis por plantilla y alternando el nombre literal de la columna con "
        "la etiqueta tomada de su <font face='Courier' size='10'>COMMENT</font>, pero no "
        "sustituye la variedad de preguntas escritas por personas distintas."))
    f.append(p(
        "De la <i>diferencia</i> entre las dos versiones estamos m&aacute;s seguros que "
        "del valor absoluto, porque se mide sobre las mismas preguntas y absorbe el "
        "factor de redacci&oacute;n. Aun as&iacute;, el umbral de +0.15 del enunciado "
        "queda dentro del rango pero no garantizado, y esa es la parte m&aacute;s "
        "expuesta de la entrega."))

    # ---------------- 9 ----------------
    f.append(p("9. Reproducibilidad", TITULO1))
    f.append(p(
        "Todo el pipeline es reproducible con semilla fija 2026: el poblador de datos, "
        "la generaci&oacute;n de pares, la partici&oacute;n interna y la generaci&oacute;n "
        "del modelo, que usa <font face='Courier' size='10'>do_sample=False</font> y un "
        "solo haz. Dos funciones cr&iacute;ticas tienen pruebas unitarias, porque de "
        "ellas depende todo lo que se reporta: la limpieza de la salida del modelo (11 "
        "casos) y el criterio de exactitud por ejecuci&oacute;n (20 casos)."))
    f.append(p("Secuencia completa:", CUERPO))
    f.append(p(
        "bash scripts/mysql_setup.sh docker<br/>"
        "python scripts/cargar_esquemas.py --dir datos/esquemas --poblar<br/>"
        "python scripts/generar_pares.py --limite 20<br/>"
        "python scripts/validar_pares.py<br/>"
        "python scripts/entrenar.py --etiqueta r8 --rank 8 --alpha 32<br/>"
        "python scripts/evaluar.py --etiqueta baseline --sin-adapter<br/>"
        "python scripts/analizar_errores.py", CODIGO))

    # ---------------- 10 ----------------
    f.append(p("10. Licencias y uso de IA", TITULO1))
    f.append(p(
        "El modelo base Qwen2.5-Coder-1.5B-Instruct se distribuye bajo licencia Apache "
        "2.0. El c&oacute;digo de este repositorio se publica bajo licencia MIT. El "
        "dataset es propio: los 12 esquemas, los datos y los 2,464 pares se generaron "
        "para este proyecto, por lo que no aplican las licencias de Spider ni de BIRD."))
    f.append(p(
        "Se utiliz&oacute; Claude (Anthropic) como asistente de programaci&oacute;n en la "
        "redacci&oacute;n del DDL, la implementaci&oacute;n de los scripts y la "
        "redacci&oacute;n de los documentos. Las decisiones de dise&ntilde;o "
        "documentadas en cada archivo fueron tomadas y revisadas por los integrantes. Las "
        "40 preguntas de validaci&oacute;n y sus consultas de referencia se escribieron a "
        "mano, no se generaron con un modelo, y cada una se verific&oacute; "
        "ejecut&aacute;ndola. Ninguna IA externa participa en la generaci&oacute;n de la "
        "consulta que se eval&uacute;a: el &uacute;nico modelo que interviene en "
        "<font face='Courier' size='10'>solucion.py</font> es el Qwen permitido por el "
        "enunciado, con su adapter."))

    # ---------------- Anexos ----------------
    f.append(p("Anexo A. Repositorio", TITULO1))
    f.append(p(
        "El c&oacute;digo, el dataset, los notebooks y los resultados est&aacute;n en el "
        "repositorio privado compartido con el docente:"))

    icono = icono_github(13)
    enlace = Paragraph(
        '<link href="%s"><font face="Times-Bold" size="11">%s</font></link>'
        % (REPO, REPO), CUERPO)
    if icono is not None:
        fila = Table([[icono, enlace]], colWidths=[0.75 * cm, 14.5 * cm], hAlign="LEFT")
        fila.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (0, 0), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        f.append(KeepTogether(fila))
    else:
        f.append(enlace)
    f.append(p(
        "El historial completo, con autor y fecha de cada cambio, est&aacute; en "
        "<font face='Courier' size='10'>historial_git.txt</font>, generado con "
        "<font face='Courier' size='10'>git log --all --date=iso --stat</font>. La "
        "bit&aacute;cora fechada est&aacute; en "
        "<font face='Courier' size='10'>BITACORA.md</font> y el reparto de tareas en "
        "<font face='Courier' size='10'>CONTRIBUCIONES.md</font>."))

    f.append(p("Anexo B. Entregables", TITULO1))
    f.extend(tabla([
        ["Archivo", "Contenido"],
        ["solucion.py", "Contrato de entrega: generar_sql(esquema, pregunta, ejecutar)"],
        ["config.json", "Modelo base, adapter, semilla"],
        ["requirements.txt", "Dependencias verificadas para Colab T4"],
        ["adapter/", "Adapter LoRA entrenado"],
        ["datos/entrenamiento.jsonl", "2,320 pares validados en MySQL 8.4.10"],
        ["datos/descartes.csv", "73 pares descartados con su motivo"],
        ["datos/validacion/", "2 esquemas y 40 preguntas propias"],
        ["notebooks/", "Datos, entrenamiento y evaluaci&oacute;n"],
        ["resultados/validacion_propia.csv", "Una fila por pregunta y por corrida"],
        ["resultados/analisis_errores.csv", "Fallos clasificados por categor&iacute;a"],
        ["presentacion.pdf", "12 diapositivas"],
    ], [5.4 * cm, 10.2 * cm]))

    return f


def main():
    destino = RAIZ / "informe.pdf"
    doc = BaseDocTemplate(
        str(destino), pagesize=A4,
        leftMargin=MARGEN, rightMargin=MARGEN,
        topMargin=MARGEN, bottomMargin=MARGEN,
        title="Proyecto 3 - Text-to-SQL con LoRA",
        author="Cindy Mishelle Gualim Perez, Gadiel Ocana",
    )
    marco = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates([PageTemplate(id="todo", frames=[marco],
                                       onPage=numero_pagina)])
    doc.build(contenido())
    print("%s generado" % destino)
    return 0


if __name__ == "__main__":
    sys.exit(main())

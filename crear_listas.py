from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import os
import sys

from utils import obtener_ruta, obtener_ruta_recurso


# Registrar la fuente Montserrat (✅ ahora como recurso empaquetado)
pdfmetrics.registerFont(TTFont("Montserrat", obtener_ruta_recurso("fuentes/Montserrat-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Montserrat-Bold", obtener_ruta_recurso("fuentes/Montserrat-Bold.ttf")))
pdfmetrics.registerFont(TTFont("Montserrat-ExtraBold", obtener_ruta_recurso("fuentes/Montserrat-ExtraBold.ttf")))

def creacion_de_listas(tabla1="", tabla2="", tabla3="", nombre=""):
    tabla3_sorted = sorted(
        tabla3,
        key=lambda alumno: (
            alumno[1].split()[0],
            alumno[1].split()[1] if len(alumno[1].split()) > 1 else ""
        )
    )

    # Asegurar extensión correcta (evita .pdf.pdf)
    pdf_file = nombre if str(nombre).lower().endswith(".pdf") else f"{nombre}.pdf"

    # ✅ Guardar junto al exe (o junto al proyecto en dev) si te pasan solo un nombre
    if not os.path.isabs(pdf_file):
        pdf_file = obtener_ruta(pdf_file)

    c = canvas.Canvas(pdf_file, pagesize=landscape(letter))

    # --- Tabla superior (data_0) ---
    num_rows_0 = 4
    num_cols_0 = 1
    col_widths_0 = [170]
    row_heights_0 = [13] * 4
    data_0 = [["" for _ in range(num_cols_0)] for _ in range(num_rows_0)]
    data_0[0][0] = "LISTA DE GRUPO"
    data_0[1][0] = f"CICLO ESCOLAR {tabla1['ciclo_escolar']}/{tabla1['periodo']}"
    data_0[2][0] = "LICENCIATURA EN DISEÑO"
    data_0[3][0] = f"{tabla1['semestre']} SEMESTRE"
    table_0 = Table(data_0, colWidths=col_widths_0, rowHeights=row_heights_0)
    style_0 = TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, -1), "Montserrat-ExtraBold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("LINEABOVE", (0, 0), (-1, -1), 0, colors.white),
        ("LINEBELOW", (0, 0), (-1, -1), 0, colors.white),
        ("LINEBEFORE", (0, 0), (-1, -1), 0, colors.white),
        ("LINEAFTER", (0, 0), (-1, -1), 0, colors.white),
    ])
    table_0.setStyle(style_0)
    table_0.wrapOn(c, 0, 0)
    table_0.drawOn(c, 303, 526)

    # --- Imágenes ---
    # Imagen de "cultura" (✅ como recurso empaquetado)
    imagen_path_0 = obtener_ruta_recurso("imagenes/cultura_inba.png")
    x_pos_0 = 42
    y_pos_0 = 548
    ancho_0 = 683
    alto_0 = 117
    escala_0 = 0.31
    c.drawImage(imagen_path_0, x_pos_0, y_pos_0, width=ancho_0 * escala_0, height=alto_0 * escala_0, preserveAspectRatio=True, mask='auto')

    # Imagen del logo "edinba" (✅ como recurso empaquetado)
    imagen_path = obtener_ruta_recurso("imagenes/edinba_logo.jpg")
    x_pos = 574
    y_pos = 556
    ancho = 162
    alto = 38
    escala = 0.71
    c.drawImage(imagen_path, x_pos, y_pos, width=ancho * escala, height=alto * escala, preserveAspectRatio=True, mask='auto')

    # --- Tabla central (data_1) ---
    num_rows = 5
    num_cols = 5
    col_widths = [110, 96, 242, 71, 128]
    row_heights = [13] * 5
    data_1 = [["" for _ in range(num_cols)] for _ in range(num_rows)]
    data_1[2][0] = f"ASIGNATURA {tabla2['tipo']}"
    data_1[0][1] = "ASIGNATURA"
    data_1[1][1] = "CURSO"
    data_1[2][1] = "NODO"
    data_1[3][1] = "DOCENTE"
    data_1[4][1] = "COORDINADOR(A)"
    data_1[0][2] = f"{tabla2['asignatura']}"

    temporal = tabla2['curso']
    limite = 44
    if len(temporal) <= limite:
        texto_limitado = temporal
    else:
        texto_limitado = " ".join(temporal[:limite].rsplit(" ", 1)[0].split())

    data_1[1][2] = texto_limitado
    data_1[2][2] = "Profesionalizante"
    data_1[3][2] = f"{tabla2['docente'].title()}"
    data_1[4][2] = f"{tabla2['coordinador(a)'].title()}"
    data_1[0][3] = "DURACIÓN"
    data_1[1][3] = "HORARIO"
    data_1[2][3] = "SALÓN"
    data_1[0][4] = "Semestral"
    data_1[1][4] = f"{tabla2['horario']}"
    data_1[2][4] = f"{tabla2['salon']}"
    table_1 = Table(data_1, colWidths=col_widths, rowHeights=row_heights)
    style_1 = TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.8, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, -1), "Montserrat"),
        ("ALIGN", (0, 0), (1, -1), "RIGHT"),
        ("ALIGN", (2, 0), (2, -1), "LEFT"),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("ALIGN", (4, 0), (4, -1), "LEFT"),
        ("LINEABOVE", (0, 0), (0, -1), 0, colors.white),
        ("LINEBELOW", (0, 0), (0, -1), 0, colors.white),
        ("LINEBEFORE", (0, 0), (0, -1), 0, colors.white),
        ("FONTNAME", (0, 0), (0, -1), "Montserrat-ExtraBold"),
        ("RIGHTPADDING", (0, 0), (0, -1), 11),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("FONTSIZE", (0, 0), (0, -1), 11),
        ("RIGHTPADDING", (1, 0), (1, -1), 2),
        ("LEFTPADDING", (2, 0), (2, -1), 11),
        ("RIGHTPADDING", (3, 0), (3, -1), 3),
        ("LEFTPADDING", (4, 0), (4, -1), 3),
    ])
    table_1.setStyle(style_1)
    table_1.wrapOn(c, 0, 0)
    table_1.drawOn(c, 41, 447)

    # --- Tabla grande (data_2) ---
    num_rows_2 = 27
    num_cols_2 = 23
    col_widths_2 = [22.5] + [190] + [18] * 18 + [24.5] + [35] + [50]
    row_heights_2 = [12.5] + [19.5] + [10.5] * 25
    data = [["" for _ in range(num_cols_2)] for _ in range(num_rows_2)]
    start_number = 1
    for i in range(2, num_rows_2):
        data[i][0] = start_number
        start_number += 1

    # Usar la lista ordenada para colocar los nombres en la tabla
    for i, alumno in enumerate(tabla3_sorted):
        data[i + 2][1] = alumno[1].title()

    data[1][0] = "NO."
    data[1][1] = "NOMBRE"
    data[0][2] = "ASISTENCIA"
    data[0][20] = "CALIFICACIÓN"
    data[1][20] = "No."
    data[1][21] = "Letra"
    data[1][22] = "% Asist"
    table_2 = Table(data, colWidths=col_widths_2, rowHeights=row_heights_2)
    style_2 = TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.8, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, -1), "Montserrat"),
        ("FONTNAME", (0, 1), (0, 1), "Montserrat-Bold"),
        ("FONTNAME", (1, 1), (1, 1), "Montserrat-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("FONTSIZE", (0, 2), (1, 26), 7.5),
        ("BOTTOMPADDING", (0, 2), (0, -1), 0),
        ("ALIGN", (1, 2), (1, -1), "LEFT"),
        ("LEFTPADDING", (1, 2), (1, -1), 2),
        ("BOTTOMPADDING", (1, 2), (1, -1), 0),
        ("SPAN", (2, 0), (19, 1)),
        ("VALIGN", (2, 0), (19, 1), "TOP"),
        ("TOPPADDING", (2, 0), (19, 1), 0),
        ("SPAN", (20, 0), (22, 0)),
        ("VALIGN", (20, 1), (22, 1), "BOTTOM"),
        ("ALIGN", (20, 1), (22, 1), "LEFT"),
        ("LEFTPADDING", (20, 1), (22, 1), 2),
        ("BOTTOMPADDING", (20, 1), (22, 1), 1),
        ("FONTNAME", (20, 0), (22, 1), "Montserrat-Bold"),
        ("FONTNAME", (2, 0), (22, 1), "Montserrat-Bold"),
        ("LINEABOVE", (0, 0), (0, 0), 0, colors.white),
        ("LINEBEFORE", (0, 0), (0, 0), 0, colors.white),
        ("LINEABOVE", (1, 0), (1, 0), 0, colors.white),
        ("LINEBEFORE", (1, 0), (1, 0), 0, colors.white),
    ])
    table_2.setStyle(style_2)
    table_2.wrapOn(c, 0, 0)
    table_2.drawOn(c, 42, 140)

    # --- Línea y texto final ---
    x1, y1 = 540, 110
    x2, y2 = 690, 110
    c.setLineWidth(1.5)
    c.line(x1, y1, x2, y2)
    texto_x = x1 + 30
    texto_y = y1 - 10
    c.setFont("Montserrat", 9.5)
    c.drawString(texto_x, texto_y, "Firma del docente")

    # --- Segunda página: Correos de alumnos ---
    emails = []
    for alumno in tabla3_sorted:
        matricula, nombre_completo = alumno  # Cada alumno es una tupla (matricula, nombre_completo)
        partes = nombre_completo.split()
        # Se asume que el formato es "APELLIDO_PATERNO APELLIDO_MATERNO NOMBRES..."
        if len(partes) >= 3:
            ap_paterno = partes[0]
            ap_materno = partes[1]
            # Solo se toma el primer nombre (en caso de tener varios)
            primer_nombre = partes[2].split()[0]
        else:
            primer_nombre = partes[-1] if partes else ""
            ap_paterno = ""
            ap_materno = ""
        matricula_prefix = matricula[:2].lower() if matricula else ""
        correo = f"dis.{primer_nombre.lower()}{ap_paterno.lower()}{ap_materno.lower()}.{matricula_prefix}@inba.edu.mx"
        emails.append(correo)

    # Crear la segunda página
    c.showPage()
    c.setFont("Montserrat", 10)
    # Coordenadas de inicio para el texto
    x_inicial = 50
    y_inicial = 540
    linea_espaciado = 12  # Espacio entre líneas
    # Dibujar la línea de título
    c.drawString(x_inicial, y_inicial, "Estos son los correos de los/las estudiantes:")
    # Dejar una línea en blanco (se reduce el valor de y dos veces)
    y_inicial -= linea_espaciado * 2
    # Dibujar cada correo en una línea nueva
    for correo in emails:
        c.drawString(x_inicial, y_inicial, correo + ",")
        y_inicial -= linea_espaciado

    # Guardar el PDF
    c.save()
    print(f"Archivo PDF generado: {pdf_file}")

# Bloque de prueba dummy
if __name__ == "__main__":
    """
    # Datos dummy para tabla1, tabla2 y tabla3 (tabla3: lista de tuplas con matrícula y nombre completo)
    tabla1 = {
        "ciclo_escolar": "2024-2025",
        "periodo": "1",
        "semestre": "PRIMER",
    }
    tabla2 = {
        "tipo": "A",
        "asignatura": "Optativa Técnicas - Tecnológicas",
        "curso": "AutoCAD Avanzado",
        "docente": "Rafael Rivas",
        "coordinador(a)": "Andrea Citlalpiltzin Martínez",
        "horario": "Martes 11:30 a 14:30 hrs",
        "salon": "Laboratorio 2"
    }
    tabla3 = [
        ("AB1234", "ABARCA COLIN DAFNE MICHELLE"),
        ("CD5678", "CAMACHO ROSAS DAVID EZEQUIEL"),
        ("EF9012", "YAROD YESCAS CUPICH")
    ]
    creacion_de_listas(tabla1, tabla2, tabla3, "dummy_lista_optativas")
    """

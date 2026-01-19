#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path
from dotenv import load_dotenv

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QStyleFactory
)
from PySide6.QtGui import (
    QIcon, QFontDatabase, QFont, QPalette, QColor
)
from PySide6.QtCore import Qt, QTimer

from base_datos import Database
from utils import obtener_ruta, obtener_ruta_bd
from tabs.tab_inscripciones import TabInscripciones


def load_font(rel_path: str):
    font_path = Path(__file__).parent / rel_path
    if not font_path.exists():
        print(f"[WARN] No se encontró la fuente: {font_path}")
        return None
    fid = QFontDatabase.addApplicationFont(str(font_path))
    if fid == -1:
        print(f"[ERR] Falló addApplicationFont para {font_path}")
        return None
    families = QFontDatabase.applicationFontFamilies(fid)
    return families[0] if families else None


def create_tables(db: Database):
    queries = [
        """CREATE TABLE IF NOT EXISTS estudiantes (
                matricula TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                apellido_paterno TEXT NOT NULL,
                apellido_materno TEXT NOT NULL,
                semestre TEXT NOT NULL,
                estado TEXT NOT NULL
            )""",
        """CREATE TABLE IF NOT EXISTS docentes (
                rfc TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                apellido_paterno TEXT NOT NULL,
                apellido_materno TEXT NOT NULL
            )""",
        """CREATE TABLE IF NOT EXISTS optativas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT CHECK(tipo IN ('A','B')) NOT NULL,
                nombre TEXT NOT NULL,
                rfc_docente TEXT NOT NULL,
                rfc_segundo_docente TEXT,
                semestres TEXT,
                cupo INTEGER,
                dia TEXT,
                inicio TEXT,
                fin TEXT,
                salon TEXT,
                ciclo TEXT,
                FOREIGN KEY(rfc_docente) REFERENCES docentes(rfc),
                FOREIGN KEY(rfc_segundo_docente) REFERENCES docentes(rfc)
            )""",
        """CREATE TABLE IF NOT EXISTS inscripciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matricula TEXT NOT NULL,
                optativa_id INTEGER NOT NULL,
                FOREIGN KEY(optativa_id) REFERENCES optativas(id)
            )"""
    ]
    for q in queries:
        db.run_query(q)

    pragma = db.run_query("PRAGMA table_info(optativas)", fetch="all") or []
    cols = [c[1] for c in pragma]
    if "rfc_segundo_docente" not in cols:
        try:
            db.run_query("ALTER TABLE optativas ADD COLUMN rfc_segundo_docente TEXT")
        except Exception:
            pass

    # ✅ Tabla de estado (contador de cambios)
    db.run_query("""
        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value INTEGER NOT NULL
        )
    """)
    db.run_query("""
        INSERT OR IGNORE INTO app_state(key, value)
        VALUES ('optativas_version', 0)
    """)

    # ✅ Triggers: cualquier cambio en optativas incrementa versión
    db.run_query("""
        CREATE TRIGGER IF NOT EXISTS trg_optativas_version_ins
        AFTER INSERT ON optativas
        BEGIN
            UPDATE app_state SET value = value + 1 WHERE key='optativas_version';
        END;
    """)
    db.run_query("""
        CREATE TRIGGER IF NOT EXISTS trg_optativas_version_upd
        AFTER UPDATE ON optativas
        BEGIN
            UPDATE app_state SET value = value + 1 WHERE key='optativas_version';
        END;
    """)
    db.run_query("""
        CREATE TRIGGER IF NOT EXISTS trg_optativas_version_del
        AFTER DELETE ON optativas
        BEGIN
            UPDATE app_state SET value = value + 1 WHERE key='optativas_version';
        END;
    """)


def limpiar_optativas_vacias(db: Database):
    try:
        db.run_query("DELETE FROM optativas WHERE nombre IS NULL OR TRIM(nombre) = ''")
    except Exception as e:
        print(f"[WARN] Limpieza de optativas vacías falló: {e}")


def migrar_estados_estudiantes(db: Database):
    try:
        filas = db.run_query(
            "SELECT matricula, UPPER(TRIM(estado)) FROM estudiantes",
            fetch="all"
        ) or []

        for mat, est in filas:
            nuevo = est
            if est == "ACTIVO":
                nuevo = "REGULAR"
            elif est == "IRREGULAR":
                nuevo = "RECURSAMIENTO"
            elif est in (
                "BAJA TEMPORAL", "BAJA DEFINITIVA",
                "RECURSAMIENTO", "RECURSAMIENTO PARALELO",
                "MOVILIDAD PARCIAL", "MOVILIDAD", "REGULAR"
            ):
                nuevo = est
            else:
                m = (est or "").replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
                if m in (
                    "BAJA TEMPORAL", "BAJA DEFINITIVA",
                    "RECURSAMIENTO", "RECURSAMIENTO PARALELO",
                    "MOVILIDAD PARCIAL", "MOVILIDAD", "REGULAR"
                ):
                    nuevo = m

            if nuevo != est:
                db.run_query("UPDATE estudiantes SET estado=? WHERE matricula=?", (nuevo, mat))
    except Exception as e:
        print(f"[WARN] Migración de estados falló: {e}")


class VentanaInscripciones(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        self.setWindowTitle("EDINBA - Inscripciones (Alumnos)")
        self.setFixedSize(1300, 710)
        self.setWindowIcon(QIcon(obtener_ruta("edinba_logo.ico")))

        # Crear la pestaña tal como está (SIN editar tab_inscripciones.py)
        self.tab_ins = TabInscripciones(self.db)

        # Hacer que el área visible no cambie por plataforma (evita recortes distintos en mac)
        self.tab_ins.widget.setFixedSize(1300, 710)

        # Inyectar label + reacomodar geometrías desde AQUÍ
        self._personalizar_ui_alumnos()

        self.setCentralWidget(self.tab_ins.widget)

        # ─────────────────────────────────────────────────────────────
        # ✅ “Live refresh” multi-app: detectar cambios de optativas (cupo, etc.)
        # ─────────────────────────────────────────────────────────────
        self._last_optativas_version = self._get_optativas_version()

        self._timer_db = QTimer(self)
        self._timer_db.setInterval(400)  # ms (ajusta 250-500 si quieres más/menos “instantáneo”)
        self._timer_db.timeout.connect(self._watch_optativas_changes)
        self._timer_db.start()

    def _on_siguiente_clicked(self):
        """
        Limpia los 3 campos de búsqueda al presionar 'Siguiente'.
        """
        if hasattr(self.tab_ins, "line_search_estudiante_tab3"):
            self.tab_ins.line_search_estudiante_tab3.clear()
        if hasattr(self.tab_ins, "line_search_optativa_a"):
            self.tab_ins.line_search_optativa_a.clear()
        if hasattr(self.tab_ins, "line_search_optativa_b"):
            self.tab_ins.line_search_optativa_b.clear()

    def _personalizar_ui_alumnos(self):
        """
        Personaliza textos/estilos del modo alumnos SIN tocar tabs/tab_inscripciones.py
        (Paso 2 y 3 en 2 renglones: opción A)
        """

        # Buscadores: compactos y borde suave
        search_style = """
            QLineEdit {
                border: 1px solid rgba(12, 28, 140, 110);
                border-radius: 7px;
                min-height: 28px;
                font: bold 13px "Noto Sans";
                color: rgb(12,28,140);
                padding: 0 10px;
                background-color: white;
            }
            QLineEdit::placeholder {
                color: rgba(96, 102, 140, 170);
                font: bold 13px "Noto Sans";
            }
            QLineEdit:focus {
                border: 1px solid rgba(12, 28, 140, 180);
            }
        """

        # Estilo azul para botones (Inscribir A/B y Siguiente)
        btn_style_azul = """
            QPushButton {
                border: 1.5px solid #0c1c8c;
                border-radius: 12px;
                font: bold 14px "Noto Sans";
                color: white;
                background-color: rgb(12,28,140);
                min-height: 34px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #4054a1;
            }
            QPushButton:pressed {
                background-color: #0a0f3e;
            }
        """

        # ✅ SOLO PARA QUE EN mac SE VEA EL TEXTO "Ya cursó Optativa" SIN CAMBIAR TODO
        chk_style = """
            QCheckBox {
                color: rgb(12,28,140);
                font: bold 13px "Noto Sans";
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """

        font_paso = QFont("Noto Sans", 14, QFont.Weight.Bold)

        # ===== 1) Paso 1 =====
        self.lbl_paso_1 = QLabel("1.- Búscate y Selecciona tu nombre", self.tab_ins.widget)
        self.lbl_paso_1.setGeometry(10, 40, 390, 30)
        self.lbl_paso_1.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.lbl_paso_1.setFont(font_paso)
        self.lbl_paso_1.setStyleSheet("color: rgb(12, 28, 140);")

        # ===== 2) Buscadores =====
        if hasattr(self.tab_ins, "line_search_estudiante_tab3"):
            self.tab_ins.line_search_estudiante_tab3.setPlaceholderText("Escribe tu nombre")
            self.tab_ins.line_search_estudiante_tab3.setGeometry(10, 80, 390, 28)
            self.tab_ins.line_search_estudiante_tab3.setStyleSheet(search_style)

        if hasattr(self.tab_ins, "line_search_optativa_a"):
            self.tab_ins.line_search_optativa_a.setPlaceholderText("Escribe el nombre de tu Asignatura A")
            self.tab_ins.line_search_optativa_a.setGeometry(430, 82, 410, 28)
            self.tab_ins.line_search_optativa_a.setStyleSheet(search_style)

        if hasattr(self.tab_ins, "line_search_optativa_b"):
            self.tab_ins.line_search_optativa_b.setPlaceholderText("Escribe el nombre de tu Asignatura B")
            self.tab_ins.line_search_optativa_b.setGeometry(860, 82, 410, 28)
            self.tab_ins.line_search_optativa_b.setStyleSheet(search_style)

        # Gap referencia (buscador nombre -> tabla estudiantes)
        gap_ref = 16

        # Tabla estudiantes
        y_table_est = 124

        # Tablas A/B (misma separación desde buscador A/B)
        y_tab_opt = 126

        # 4.- y tabla inscritas: mismo gap_ref
        y_lbl4 = 494
        y_ins_table = y_lbl4 + 22 + gap_ref

        # ===== 3) Tabla estudiantes =====
        if hasattr(self.tab_ins, "table_estudiantes_tab3"):
            self.tab_ins.table_estudiantes_tab3.setGeometry(10, y_table_est, 400, 355)

        # ===== 4) Paso 2 y Paso 3 (dos renglones) =====
        self.lbl_paso_2 = QLabel("2.- Busca, Selecciona, e Inscribe\ntu Asignatura A", self.tab_ins.widget)
        self.lbl_paso_2.setGeometry(430, 18, 600, 50)
        self.lbl_paso_2.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_paso_2.setFont(font_paso)
        self.lbl_paso_2.setStyleSheet("color: rgb(12, 28, 140);")

        self.lbl_paso_3 = QLabel("3.- Busca, Selecciona, e Inscribe\ntu Asignatura B", self.tab_ins.widget)
        self.lbl_paso_3.setGeometry(860, 18, 600, 50)
        self.lbl_paso_3.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_paso_3.setFont(font_paso)
        self.lbl_paso_3.setStyleSheet("color: rgb(12, 28, 140);")

        # ===== 5) Ocultar labels "Asignaturas A" y "Asignaturas B" + renombrar "Inscritas" =====
        for lab in self.tab_ins.widget.findChildren(QLabel):
            txt = (lab.text() or "").strip()

            if txt == "Asignaturas A" or txt == "Asignaturas B":
                lab.hide()

            elif txt == "Inscritas":
                lab.setText("4.- Revisa tus Asignaturas inscritas")
                lab.setGeometry(10, y_lbl4, 520, 30)
                lab.setFont(font_paso)
                lab.setStyleSheet("color: rgb(12, 28, 140);")

        # ===== 6) Botones Inscribir A/B estilo azul =====
        if hasattr(self.tab_ins, "btn_inscribir_a"):
            self.tab_ins.btn_inscribir_a.setStyleSheet(btn_style_azul)

        if hasattr(self.tab_ins, "btn_inscribir_b"):
            self.tab_ins.btn_inscribir_b.setStyleSheet(btn_style_azul)

        # ===== 7) Tablas A/B + botones + checkboxes =====
        if hasattr(self.tab_ins, "optativas_listado_a_tab3"):
            geo_a = self.tab_ins.optativas_listado_a_tab3.geometry()
            self.tab_ins.optativas_listado_a_tab3.setGeometry(geo_a.x(), y_tab_opt, geo_a.width(), geo_a.height())
            y_btn_opt = y_tab_opt + geo_a.height() + 10
        else:
            y_btn_opt = 430

        if hasattr(self.tab_ins, "optativas_listado_b_tab3"):
            geo_b = self.tab_ins.optativas_listado_b_tab3.geometry()
            self.tab_ins.optativas_listado_b_tab3.setGeometry(geo_b.x(), y_tab_opt, geo_b.width(), geo_b.height())

        if hasattr(self.tab_ins, "btn_inscribir_a"):
            self.tab_ins.btn_inscribir_a.setGeometry(430, y_btn_opt, 130, 34)

        if hasattr(self.tab_ins, "btn_inscribir_b"):
            self.tab_ins.btn_inscribir_b.setGeometry(860, y_btn_opt, 130, 34)

        if hasattr(self.tab_ins, "chk_ya_curso_a"):
            self.tab_ins.chk_ya_curso_a.setGeometry(690, y_btn_opt, 200, 25)
            self.tab_ins.chk_ya_curso_a.setStyleSheet(chk_style)

        if hasattr(self.tab_ins, "chk_ya_curso_b"):
            self.tab_ins.chk_ya_curso_b.setGeometry(1120, y_btn_opt, 200, 25)
            self.tab_ins.chk_ya_curso_b.setStyleSheet(chk_style)

        # ===== 8) Tabla inscritas + botón Quitar debajo =====
        if hasattr(self.tab_ins, "table_inscritas_tab3"):
            self.tab_ins.table_inscritas_tab3.setGeometry(10, y_ins_table, 820, 110)

        if hasattr(self.tab_ins, "btn_quitar_inscrita") and hasattr(self.tab_ins, "table_inscritas_tab3"):
            geo = self.tab_ins.table_inscritas_tab3.geometry()
            x_btn = geo.x()
            y_btn = geo.y() + geo.height() + 10
            self.tab_ins.btn_quitar_inscrita.setGeometry(x_btn, y_btn, 160, 34)

        # ===== 9) Paso 5 arriba del botón Siguiente + botón Siguiente =====
        if hasattr(self.tab_ins, "table_inscritas_tab3"):
            geo = self.tab_ins.table_inscritas_tab3.geometry()
            x_next = geo.x() + geo.width() + 20
            y_next = geo.y() + int((geo.height() - 34) / 2)

            # Label Paso 5 (como lo dejaste)
            self.lbl_paso_5 = QLabel("5.- Presiona Siguiente", self.tab_ins.widget)
            self.lbl_paso_5.setGeometry(x_next, y_lbl4 + 32, 420, 30)
            self.lbl_paso_5.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.lbl_paso_5.setFont(font_paso)
            self.lbl_paso_5.setStyleSheet("color: rgb(12, 28, 140);")

            self.btn_siguiente = QPushButton("Siguiente", self.tab_ins.widget)
            self.btn_siguiente.setGeometry(x_next, y_next, 160, 34)
            self.btn_siguiente.setStyleSheet(btn_style_azul)
            self.btn_siguiente.clicked.connect(self._on_siguiente_clicked)

        # ===== 10) Elevar labels =====
        self.lbl_paso_1.raise_()
        self.lbl_paso_2.raise_()
        self.lbl_paso_3.raise_()
        if hasattr(self, "lbl_paso_5"):
            self.lbl_paso_5.raise_()

    def _get_optativas_version(self) -> int:
        row = self.db.run_query(
            "SELECT value FROM app_state WHERE key='optativas_version'",
            fetch="one"
        )
        try:
            return int(row[0]) if row else 0
        except Exception:
            return 0

    def _watch_optativas_changes(self):
        v = self._get_optativas_version()
        if v == self._last_optativas_version:
            return

        self._last_optativas_version = v

        # ✅ Refresca solo lo que depende del cupo (sin mover la selección de alumno)
        try:
            self.tab_ins.cargar_optativas_a_tab3()
            self.tab_ins.cargar_optativas_b_tab3()
            self.tab_ins._control_optativas_a_b_habilitadas()
        except Exception as e:
            print(f"[WARN] Refresh optativas falló: {e}")

if __name__ == "__main__":
    load_dotenv()

    app = QApplication(sys.argv)

    # --- Forzar estilo consistente (mac/Windows/Linux) ---
    app.setStyle(QStyleFactory.create("Fusion"))

    # --- Paleta base para evitar variaciones de fondo/controles en mac ---
    pal = app.palette()
    pal.setColor(QPalette.Window, QColor("white"))
    pal.setColor(QPalette.Base, QColor("white"))
    pal.setColor(QPalette.AlternateBase, QColor("#e8eaf4"))
    pal.setColor(QPalette.Button, QColor("white"))
    pal.setColor(QPalette.Text, QColor("black"))
    pal.setColor(QPalette.ButtonText, QColor("black"))
    pal.setColor(QPalette.Highlight, QColor(12, 28, 140))
    pal.setColor(QPalette.HighlightedText, QColor("white"))
    app.setPalette(pal)

    # --- DPI: ayuda a reducir diferencias en mac retina ---
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Cargar fuente embebida
    noto_family = load_font("fuentes/NotoSans-VariableFont.ttf")
    if noto_family:
        app.setFont(QFont(noto_family, 12))

    # Mantener tu estilo global mínimo (como te gusta)
    app.setStyleSheet("""
        QTableWidget, QTableWidget QTableView, QTableWidget::item {
            color: black;
        }
    """)

    ruta_bd = obtener_ruta_bd()
    db = Database(ruta_bd)

    # Igual que tu MainWindow original (pasos críticos)
    create_tables(db)
    limpiar_optativas_vacias(db)
    migrar_estados_estudiantes(db)

    w = VentanaInscripciones(db)
    w.show()
    sys.exit(app.exec())

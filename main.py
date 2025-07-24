#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from dotenv import load_dotenv

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTabWidget, QMessageBox, QDialog, QLineEdit, QPushButton
)
from PyQt6.QtGui import QIcon, QAction, QFontDatabase, QFont
from PyQt6.QtCore import QSettings, Qt

from base_datos import Database
from crear_listas import creacion_de_listas
from utils import obtener_ruta, obtener_ruta_bd, SEMESTRE_MAPA

from tabs.tab_estudiantes import TabEstudiantes
from tabs.tab_docentes import TabDocentes
from tabs.tab_optativas import TabOptativas
from tabs.tab_inscripciones import TabInscripciones
from tabs.tab_listas import TabListas


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()

        # — Mismo título e ícono que el MainWindow —
        self.setWindowTitle("EDINBA: Estudiantes & Docentes - Optativas - Listas")
        self.setWindowIcon(QIcon(obtener_ruta("edinba_logo.ico")))

        # — Mismo tamaño que el programa principal —
        self.setFixedSize(1366, 768)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

        # — Estilos razonables —
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLineEdit {
                border: 1.5px solid #0c1c8c;
                border-radius: 5px;
                min-height: 32px;
                font: bold 14px "Noto Sans";
                color: rgb(12,28,140);
                padding: 0 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #4054a1;
            }
            QLineEdit::placeholder {
                color: rgb(96,102,140);
            }
            QPushButton {
                border: 1.5px solid #0c1c8c;
                border-radius: 12px;
                font: bold 14px "Noto Sans";
                color: white;
                background-color: rgb(12,28,140);
                min-height: 36px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #4054a1;
            }
            QPushButton:pressed {
                background-color: #0a0f3e;
            }
        """)

        # — Layout centrado —
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Campo Usuario
        self.user_edit = QLineEdit(self)
        self.user_edit.setPlaceholderText("Usuario")
        self.user_edit.setFixedWidth(300)
        layout.addWidget(self.user_edit)

        # Campo Contraseña
        self.pass_edit = QLineEdit(self)
        self.pass_edit.setPlaceholderText("Contraseña")
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_edit.setFixedWidth(300)
        layout.addWidget(self.pass_edit)

        # Botón Ingresar
        self.login_btn = QPushButton("Ingresar", self)
        self.login_btn.setFixedWidth(300)
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)

        self.role = None  # "admin" u "optativas"

    def handle_login(self):
        user = self.user_edit.text().strip().lower()
        pwd = self.pass_edit.text()

        u_admin = os.getenv("USUARIO_ADMIN", "").lower()
        p_admin = os.getenv("CONTRASENA_ADMIN", "")
        u_opt = os.getenv("USUARIO_OPTATIVAS", "").lower()
        p_opt = os.getenv("CONTRASENA_OPTATIVAS", "")

        if user == u_admin and pwd == p_admin:
            self.role = "admin"
            self.accept()
        elif user == u_opt and pwd == p_opt:
            self.role = "optativas"
            self.accept()
        else:
            # Mensaje de error con texto centrado
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.NoIcon)
            msg.setWindowTitle("Error de login")
            msg.setTextFormat(Qt.TextFormat.RichText)
            msg.setText("<div align='center'>Usuario o contraseña incorrectos</div>")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()


class MainWindow(QMainWindow):
    def __init__(self, db: Database, settings: QSettings, role: str):
        super().__init__()
        self.role = role

        # Título y tamaño
        self.setWindowTitle("EDINBA: Estudiantes & Docentes - Optativas - Listas")
        self.setFixedSize(1366, 768)

        # — Centrar la ventana en la pantalla al iniciar —
        cp = self.screen().availableGeometry().center()
        qr = self.frameGeometry()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        # — Deshabilitar el botón de maximizar —
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

        # Ícono
        self.setWindowIcon(QIcon(obtener_ruta("edinba_logo.ico")))

        # DB y Settings
        self.db = db
        self.create_tables()
        self.settings = settings

        # UI principal
        central = QWidget()
        lay = QVBoxLayout(central)
        self.tabWidget = QTabWidget()
        lay.addWidget(self.tabWidget)
        self.setCentralWidget(central)

        # Pestañas (pasan is_admin solo a quienes cargan CSV)
        self.tab_est = TabEstudiantes(self.db, is_admin=(self.role == "admin"))
        self.tabWidget.addTab(self.tab_est.widget, "ESTUDIANTES")

        self.tab_doc = TabDocentes(self.db, is_admin=(self.role == "admin"))
        self.tabWidget.addTab(self.tab_doc.widget, "DOCENTES")

        self.tab_opt = TabOptativas(self.db, is_admin=(self.role == "admin"))
        self.tabWidget.addTab(self.tab_opt.widget, "OPTATIVAS")

        self.tab_ins = TabInscripciones(self.db)
        self.tabWidget.addTab(self.tab_ins.widget, "INSCRIPCIONES")

        self.tab_lis = TabListas(self.db, self.settings)
        self.tabWidget.addTab(self.tab_lis.widget, "LISTAS")

        # Carga inicial de datos
        self.tab_est.cargar_estudiantes()
        self.tab_doc.cargar_profesores_tab1()
        self.tab_opt.cargar_optativas()
        self.tab_ins.cargar_estudiantes_tab3()

        # — No se ocultan pestañas, solo botones en las tabs —
        # (Eliminado bloque que quitaba pestañas para optativas)

        # Menú Créditos
        action_creditos = QAction("Créditos", self)
        action_creditos.triggered.connect(self.mostrar_creditos)
        self.menuBar().addAction(action_creditos)

    def mostrar_creditos(self):
        QMessageBox.information(
            self,
            "Créditos y Licencia",
            "Desarrollador: Yarod Yescas Cupich\n"
            "Diseñadora de la Interfaz: Karen\n"
            "Asesor del proyecto: David Perrusquía González\n\n"
            "Esta aplicación utiliza la biblioteca Qt a través de PyQt6.\n"
            "Qt está licenciada bajo LGPLv3.\n"
            "Las bibliotecas Qt usadas están enlazadas dinámicamente y pueden ser reemplazadas.\n"
            "Puede consultar los términos completos de la licencia en:\n"
            "https://www.gnu.org/licenses/lgpl-3.0.html"
        )

    def create_tables(self):
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
            self.db.run_query(q)
        pragma = self.db.run_query("PRAGMA table_info(optativas)", fetch="all")
        cols = [c[1] for c in pragma]
        if "rfc_segundo_docente" not in cols:
            try:
                self.db.run_query(
                    "ALTER TABLE optativas ADD COLUMN rfc_segundo_docente TEXT"
                )
            except Exception:
                pass


if __name__ == "__main__":
    load_dotenv()  # requiere python-dotenv y un .env en la raíz
    app = QApplication(sys.argv)

    # ─────────────────────────────────────────────────────────────
    #  Cargar fuente Noto Sans (o la que tengas) embebida
    # ─────────────────────────────────────────────────────────────
    from pathlib import Path
    from PyQt6.QtGui import QFontDatabase, QFont

    def load_font(rel_path: str) -> str | None:
        """Registra una fuente y devuelve el nombre de familia que Qt reconoce."""
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

    # Ajusta la ruta a donde realmente pusiste tu .ttf
    noto_family = load_font("fuentes/NotoSans-VariableFont.ttf")

    if noto_family:
        # Forzar la fuente por defecto de toda la app (tamaño a gusto)
        app.setFont(QFont(noto_family, 12))
    else:
        print("[INFO] Usando la fuente del sistema porque no se pudo registrar Noto Sans.")

    # 🔽 Forzar texto negro en tablas (tu código original)
    app.setStyleSheet("""
        QTableWidget, QTableWidget QTableView, QTableWidget::item {
            color: black;
        }
    """)

    # ─────────────────────────────────────────────────────────────
    #  Login y arranque normal
    # ─────────────────────────────────────────────────────────────
    login = LoginDialog()
    if login.exec() == QDialog.DialogCode.Accepted:
        ruta_bd = obtener_ruta_bd()
        db = Database(ruta_bd)
        settings = QSettings("EDINBA", "EstudiantesDocentesOptativas")
        w = MainWindow(db, settings, login.role)
        w.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)

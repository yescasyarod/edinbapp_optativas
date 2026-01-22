#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pathlib import Path

# ── Qt ──────────────────────────────────────────────────────────
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTabWidget, QMessageBox, QDialog, QLineEdit, QPushButton,
    QLabel
)
from PySide6.QtGui import QIcon, QAction, QFontDatabase, QFont
from PySide6.QtCore import QSettings, Qt

# ── Tu código ───────────────────────────────────────────────────
from base_datos import Database
from crear_listas import creacion_de_listas
from utils import obtener_ruta, obtener_ruta_bd, obtener_ruta_recurso, cargar_env, SEMESTRE_MAPA

from tabs.tab_estudiantes import TabEstudiantes
from tabs.tab_docentes import TabDocentes
from tabs.tab_optativas import TabOptativas
from tabs.tab_inscripciones import TabInscripciones
from tabs.tab_listas import TabListas
from tabs.tab_estadisticas import TabEstadisticas


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()

        # — Mismo título e ícono que el MainWindow —
        self.setWindowTitle("EDINBA: Estudiantes & Docentes - Optativas - Listas")
        self.setWindowIcon(QIcon(obtener_ruta_recurso("edinba_logo.ico")))

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

        # Ícono (✅ ahora empaquetado)
        self.setWindowIcon(QIcon(obtener_ruta_recurso("edinba_logo.ico")))

        # DB y Settings
        self.db = db
        self.create_tables()
        self._limpiar_optativas_vacias()
        self._migrar_estados_estudiantes()
        self.settings = settings

        # UI principal
        central = QWidget()
        lay = QVBoxLayout(central)
        # UI principal
        central = QWidget()
        lay = QVBoxLayout(central)
        self.tabWidget = QTabWidget()
        lay.addWidget(self.tabWidget)
        self.setCentralWidget(central)

        # — Estilo de las pestañas —
        self.tabWidget.setStyleSheet("""
            /* estilo general de cada pestaña */
            QTabBar::tab {
                font: bold 12px "Noto Sans";
                color: rgb(12,28,140);
                background: transparent;
                padding: 8px 16px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            /* pestaña seleccionada */
            QTabBar::tab:selected {
                background-color: rgb(12,28,140);
                color: white;
            }

        """)

        # Pestañas (pasan is_admin solo a quienes cargan CSV)
        self.tab_est = TabEstudiantes(self.db, is_admin=(self.role == "admin"))
        self.tabWidget.addTab(self.tab_est.widget, "ESTUDIANTES")

        self.tab_doc = TabDocentes(self.db, is_admin=(self.role == "admin"))
        self.tabWidget.addTab(self.tab_doc.widget, "DOCENTES")

        self.tab_opt = TabOptativas(self.db, is_admin=(self.role == "admin"))
        self.tabWidget.addTab(self.tab_opt.widget, "ASIGNATURAS")


        self.tab_ins = TabInscripciones(self.db)
        self.tabWidget.addTab(self.tab_ins.widget, "INSCRIPCIONES")
        # Cuando cambien las optativas, recarga al instante las listas A y B en Inscripciones
        self.tab_opt.optativas_changed.connect(self.tab_ins.cargar_optativas_a_tab3)
        self.tab_opt.optativas_changed.connect(self.tab_ins.cargar_optativas_b_tab3)


        self.tab_lis = TabListas(self.db, self.settings)
        self.tabWidget.addTab(self.tab_lis.widget, "LISTAS")

        # Estadísticas de inscripciones
        self.tab_estad = TabEstadisticas(self.db)
        self.tab_opt.optativas_changed.connect(self.tab_estad.cargar_estadisticas)
        self.tabWidget.addTab(self.tab_estad.widget, "ESTADÍSTICAS")

        # Carga inicial de datos
        self.tab_est.cargar_estudiantes()
        self.tab_doc.cargar_profesores_tab1()
        self.tab_opt.cargar_optativas()
        self.tab_ins.cargar_estudiantes_tab3()
        self.tab_ins.inscripciones_changed.connect(self.tab_estad.cargar_estadisticas)

        # Menú Créditos
        action_creditos = QAction("Créditos", self)
        action_creditos.triggered.connect(self.mostrar_creditos)
        self.menuBar().addAction(action_creditos)
        # --- Menú Exportar ---
        menu_exportar = self.menuBar().addMenu("Exportar")

        act_exp_est = QAction("Estudiantes", self)
        act_exp_doc = QAction("Docentes", self)
        act_exp_opt = QAction("Asignaturas", self)
        act_exp_ins = QAction("Inscripciones", self)

        act_exp_est.triggered.connect(self.exportar_estudiantes_csv)
        act_exp_doc.triggered.connect(self.exportar_docentes_csv)
        act_exp_opt.triggered.connect(self.exportar_optativas_csv)
        act_exp_ins.triggered.connect(self.exportar_inscripciones_csv)

        menu_exportar.addAction(act_exp_est)
        menu_exportar.addAction(act_exp_doc)
        menu_exportar.addAction(act_exp_opt)
        menu_exportar.addAction(act_exp_ins)

    def mostrar_creditos(self):
        # 1) Creamos el QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle("Créditos y Licencia")
        msg.setIcon(QMessageBox.NoIcon)
        
        # 2) Le decimos que el texto es HTML
        msg.setTextFormat(Qt.RichText)
        
        # 3) Permitimos interacción con el texto (clic en links)
        msg.setTextInteractionFlags(Qt.TextBrowserInteraction)
        
        # 4) Definimos el HTML con los <a href="...">
        html = (
            'Desarrollador: '
            '<a href="https://www.instagram.com/yarod.yescas.cupich/" '
            'style="text-decoration:none; color:#0000ff;">'
            'Yarod Yescas Cupich</a><br>'
            'Diseñadora de la Interfaz: Karen Ramírez Gordillo<br>'
            'Asesor del proyecto: David Perrusquía González<br><br>'
            'Esta aplicación utiliza la biblioteca Qt a través de PySide6.<br>'
            'Qt está licenciada bajo LGPLv3.<br>'
            'Las bibliotecas Qt usadas están enlazadas dinámicamente y pueden ser reemplazadas.<br>'
            'Consulte los términos completos en:<br>'
            '<a href="https://www.gnu.org/licenses/lgpl-3.0.html">'
            'https://www.gnu.org/licenses/lgpl-3.0.html</a>'
        )
        msg.setText(html)
        
        # 5) Para que el link realmente abra el navegador,
        #    tenemos que activar openExternalLinks en la etiqueta interna
        label = msg.findChild(QLabel)
        if label:
            label.setOpenExternalLinks(True)
        
        # 6) Botón OK y mostrar
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

    def _csv_base_path(self):
        from utils import obtener_directorio_base
        base = obtener_directorio_base()
        path = os.path.join(base, "CSV")
        os.makedirs(path, exist_ok=True)
        return path

    def exportar_estudiantes_csv(self):
        path = os.path.join(self._csv_base_path(), "estudiantes.csv")
        rows = self.db.run_query(
            "SELECT matricula,nombre,apellido_paterno,apellido_materno,semestre,estado "
            "FROM estudiantes ORDER BY nombre,apellido_paterno,apellido_materno", fetch="all"
        ) or []
        import csv
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["matricula","nombre","apellido_paterno","apellido_materno","semestre","estado"])
            w.writerows(rows)
        QMessageBox.information(self, "Exportar", f"Estudiantes exportados en:\n{path}")

    def exportar_docentes_csv(self):
        path = os.path.join(self._csv_base_path(), "docentes.csv")
        rows = self.db.run_query(
            "SELECT rfc,nombre,apellido_paterno,apellido_materno FROM docentes "
            "ORDER BY nombre,apellido_paterno,apellido_materno", fetch="all"
        ) or []
        import csv
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["rfc","nombre","apellido_paterno","apellido_materno"])
            w.writerows(rows)
        QMessageBox.information(self, "Exportar", f"Docentes exportados en:\n{path}")

    def exportar_optativas_csv(self):
        path = os.path.join(self._csv_base_path(), "asignaturas.csv")

        # Sólo filas con nombre no vacío
        rows = self.db.run_query(
            """
            SELECT
                UPPER(TRIM(tipo)) AS tipo,
                nombre,
                rfc_docente,
                COALESCE(rfc_segundo_docente, '') AS rfc_segundo_docente,
                COALESCE(semestres, '') AS semestres,
                COALESCE(cupo, 0) AS cupo,
                COALESCE(dia, '') AS dia,
                COALESCE(inicio, '') AS inicio,
                COALESCE(fin, '') AS fin,
                COALESCE(salon, '') AS salon,
                COALESCE(ciclo, '') AS ciclo
            FROM optativas
            WHERE nombre IS NOT NULL AND TRIM(nombre) <> ''
            ORDER BY
                CASE UPPER(TRIM(tipo)) WHEN 'A' THEN 0 ELSE 1 END,
                nombre COLLATE NOCASE,
                dia COLLATE NOCASE,
                inicio
            """,
            fetch="all"
        ) or []

        import csv
        # UTF-8 con BOM para Excel
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["tipo","nombre","rfc_docente","rfc_segundo_docente","semestres",
                        "cupo","dia","inicio","fin","salon","ciclo"])
            w.writerows(rows)

        QMessageBox.information(self, "Exportar", f"Optativas exportadas en:\n{path}")

    def exportar_inscripciones_csv(self):
        path = os.path.join(self._csv_base_path(), "inscripciones.csv")
        # Matrícula, Nombre Completo, Tipo de Optativa, Semestre, Materia, Correo
        rows = self.db.run_query(
            """SELECT e.matricula, e.nombre, e.apellido_paterno, e.apellido_materno,
                    e.semestre, o.tipo, o.nombre
            FROM inscripciones i
            JOIN estudiantes e ON e.matricula=i.matricula
            JOIN optativas o ON o.id=i.optativa_id
            ORDER BY e.nombre,e.apellido_paterno,e.apellido_materno,o.tipo,o.nombre""",
            fetch="all"
        ) or []

        def correo_from(matricula, nombre, ap, am):
            # Regla igual que en crear_listas: dis.{primerNombre}{apPat}{apMat}.{matricula[:2]}
            primer_nombre = (nombre.split()[0] if nombre else "").lower()
            ap_p = (ap or "").lower()
            ap_m = (am or "").lower()
            pref = (matricula or "")[:2].lower()
            return f"dis.{primer_nombre}{ap_p}{ap_m}.{pref}@inba.edu.mx"

        import csv
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Matricula","Nombre Completo","Tipo de Optativa","Semestre","Materia","Correo"])
            for m,n,ap,am,sem,tipo,nommat in rows:
                nombre_comp = f"{n} {ap} {am}".strip()
                w.writerow([m, nombre_comp, tipo, sem, nommat, correo_from(m,n,ap,am)])

        QMessageBox.information(self, "Exportar", f"Inscripciones exportadas en:\n{path}")

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

        # 1) Tablas principales
        for q in queries:
            self.db.run_query(q)

        # 2) Migración rfc_segundo_docente si hace falta
        pragma = self.db.run_query("PRAGMA table_info(optativas)", fetch="all") or []
        cols = [c[1] for c in pragma]
        if "rfc_segundo_docente" not in cols:
            try:
                self.db.run_query("ALTER TABLE optativas ADD COLUMN rfc_segundo_docente TEXT")
            except Exception:
                pass

        # 3) ✅ Tabla de estado para “versionado” (cambios en optativas)
        self.db.run_query("""
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value INTEGER NOT NULL
            )
        """)
        self.db.run_query("""
            INSERT OR IGNORE INTO app_state(key, value)
            VALUES ('optativas_version', 0)
        """)

        # 4) ✅ Triggers: cualquier INSERT/UPDATE/DELETE en optativas incrementa versión
        self.db.run_query("""
            CREATE TRIGGER IF NOT EXISTS trg_optativas_version_ins
            AFTER INSERT ON optativas
            BEGIN
                UPDATE app_state SET value = value + 1 WHERE key='optativas_version';
            END;
        """)
        self.db.run_query("""
            CREATE TRIGGER IF NOT EXISTS trg_optativas_version_upd
            AFTER UPDATE ON optativas
            BEGIN
                UPDATE app_state SET value = value + 1 WHERE key='optativas_version';
            END;
        """)
        self.db.run_query("""
            CREATE TRIGGER IF NOT EXISTS trg_optativas_version_del
            AFTER DELETE ON optativas
            BEGIN
                UPDATE app_state SET value = value + 1 WHERE key='optativas_version';
            END;
        """)

    def _migrar_estados_estudiantes(self):
        """
        Migra estados antiguos a los nuevos para que Inscripciones no quede vacía.
        ACTIVO -> REGULAR
        IRREGULAR -> RECURSAMIENTO
        (los demás se normalizan a mayúsculas)
        """
        try:
            filas = self.db.run_query(
                "SELECT matricula, UPPER(TRIM(estado)) FROM estudiantes", fetch="all"
            ) or []
            for mat, est in filas:
                nuevo = est
                if est == "ACTIVO":
                    nuevo = "REGULAR"
                elif est == "IRREGULAR":
                    nuevo = "RECURSAMIENTO"
                # Normaliza variantes comunes
                elif est in ("BAJA TEMPORAL", "BAJA DEFINITIVA",
                            "RECURSAMIENTO", "RECURSAMIENTO PARALELO",
                            "MOVILIDAD PARCIAL", "MOVILIDAD", "REGULAR"):
                    nuevo = est  # ya ok
                else:
                    # si viene en formato "Baja Temporal", etc., normaliza a mayúsculas exactas
                    m = est.replace("Á","A").replace("É","E").replace("Í","I").replace("Ó","O").replace("Ú","U")
                    if m in ("BAJA TEMPORAL","BAJA DEFINITIVA","RECURSAMIENTO","RECURSAMIENTO PARALELO",
                            "MOVILIDAD PARCIAL","MOVILIDAD","REGULAR"):
                        nuevo = m
                if nuevo != est:
                    self.db.run_query(
                        "UPDATE estudiantes SET estado=? WHERE matricula=?",
                        (nuevo, mat)
                    )
        except Exception as e:
            print(f"[WARN] Migración de estados falló: {e}")
    
    def _limpiar_optativas_vacias(self):
        try:
            self.db.run_query(
                "DELETE FROM optativas WHERE nombre IS NULL OR TRIM(nombre) = ''"
            )
        except Exception as e:
            print(f"[WARN] Limpieza de optativas vacías falló: {e}")



def load_font(rel_path: str):
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


if __name__ == "__main__":
    cargar_env()  # requiere python-dotenv y un .env en la raíz
    app = QApplication(sys.argv)

    # ─────────────────────────────────────────────────────────────
    #  Cargar fuente embebida
    # ─────────────────────────────────────────────────────────────
    noto_family = load_font("fuentes/NotoSans-VariableFont.ttf")
    if noto_family:
        app.setFont(QFont(noto_family, 12))

    app.setStyleSheet("""
        QTableWidget, QTableWidget QTableView, QTableWidget::item {
            color: black;
        }
    """)

    # ─────────────────────────────────────────────────────────────
    #  ¿SALTAR LOGIN? Pon SKIP_LOGIN=true en tu .env si quieres
    # ─────────────────────────────────────────────────────────────
    skip_login = os.getenv("SKIP_LOGIN", "false").lower() == "true"
    default_role = os.getenv("DEFAULT_ROLE", "admin")  # o "optativas"

    if skip_login:
        # Directamente al programa, sin pedir credenciales
        ruta_bd = obtener_ruta_bd()
        db = Database(ruta_bd)
        settings = QSettings("EDINBA", "EstudiantesDocentesOptativas")
        w = MainWindow(db, settings, default_role)
        w.show()
        sys.exit(app.exec())

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
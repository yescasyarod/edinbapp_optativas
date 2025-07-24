# proyecto/tabs/tab_listas.py

import os, shutil
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox
)
from utils import obtener_directorio_base, SEMESTRE_MAPA
from crear_listas import creacion_de_listas


class TabListas:
    def __init__(self, db, settings):
        self.db = db
        self.settings = settings
        self.widget = QWidget()
        self._setup_ui()

    def _setup_ui(self):
        main = QVBoxLayout(self.widget)

        main.addStretch()
        cont = QWidget()
        lay = QVBoxLayout(cont)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(20)

        lbl = QLabel("Coordinador(a):")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lbl)

        self.line_coordinador = QLineEdit()
        self.line_coordinador.setText(self.settings.value("coordinador", ""))
        self.line_coordinador.editingFinished.connect(self.save_coordinador)
        self.line_coordinador.setFixedWidth(250)
        lay.addWidget(self.line_coordinador, alignment=Qt.AlignmentFlag.AlignCenter)

        lbl2 = QLabel("Ciclo/Periodo:")
        lbl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lbl2)

        self.combo_ciclo_listas = QComboBox()
        from datetime import datetime
        año_actual = datetime.now().year
        items = [
            f"{año_actual - 1}-{año_actual}/2",
            f"{año_actual}-{año_actual + 1}/1"
        ]
        self.combo_ciclo_listas.addItems(items)
        self.combo_ciclo_listas.setFixedWidth(250)
        lay.addWidget(self.combo_ciclo_listas, alignment=Qt.AlignmentFlag.AlignCenter)

        self.btn_generar_listas = QPushButton("Generar listas")
        self.btn_generar_listas.setFixedWidth(250)
        self.btn_generar_listas.clicked.connect(self.generar_listas)
        lay.addWidget(self.btn_generar_listas, alignment=Qt.AlignmentFlag.AlignCenter)

        main.addWidget(cont)
        main.addStretch()

    def save_coordinador(self):
        self.settings.setValue("coordinador", self.line_coordinador.text())

    def generar_listas(self):
        r = QMessageBox.question(
            self.widget, "Advertencia",
            "Se borrará todo el contenido de la carpeta 'listas' antes de generar nuevas. ¿Desea continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if r != QMessageBox.StandardButton.Yes:
            return

        base = obtener_directorio_base()
        listas_path = os.path.join(base, "listas")
        if os.path.exists(listas_path):
            shutil.rmtree(listas_path)
        os.makedirs(listas_path)

        ciclo_full = self.combo_ciclo_listas.currentText()
        parte_ciclo, parte_periodo = ciclo_full.split("/", 1)
        coord = self.line_coordinador.text().strip() or "SIN COORDINADOR"

        query = """
            SELECT DISTINCT o.id,o.tipo,o.nombre,o.dia,o.inicio,o.fin,o.salon,
                            o.rfc_docente,o.rfc_segundo_docente
            FROM inscripciones i
            JOIN optativas o ON i.optativa_id=o.id
            ORDER BY o.nombre
        """
        ops = self.db.run_query(query, fetch="all")
        docs = self.db.run_query(
            "SELECT rfc,nombre||' '||apellido_paterno||' '||apellido_materno FROM docentes",
            fetch="all"
        )
        doc_map = {r: nom for r, nom in docs}

        for (opt_id, tipo, nombre_opt, dia, hi, hf, salon, r1, r2) in ops:
            if r2:
                d1 = doc_map.get(r1, "Docente Sin Nombre")
                d2 = doc_map.get(r2, "Docente Sin Nombre")
                docente_str = f"{self._proc_doc(d1)} - {self._proc_doc(d2)}"
            else:
                docente_str = self._proc_doc(doc_map.get(r1, "Docente Sin Nombre"))

            alumnos = self.db.run_query(
                """SELECT e.matricula,e.nombre,e.apellido_paterno,e.apellido_materno,e.semestre
                   FROM inscripciones i
                   JOIN estudiantes e ON i.matricula=e.matricula
                   WHERE i.optativa_id=? AND e.estado='Activo'
                   ORDER BY e.nombre,e.apellido_paterno,e.apellido_materno""",
                (opt_id,), fetch="all"
            )
            sem_groups = {}
            for mat, nom, ap, am, sem in alumnos:
                sem_groups.setdefault(sem, []).append((mat, f"{ap} {am} {nom}".strip().upper()))

            for sem, lista in sem_groups.items():
                tipo_sub = ("Optativas_A" if tipo == "A" else "Optativas_B")
                sem_num = sem.replace("°", "")
                carpeta = os.path.join(listas_path, tipo_sub, nombre_opt, f"semestre_{sem_num}")
                os.makedirs(carpeta, exist_ok=True)
                tabla = {
                    "ciclo_escolar": parte_ciclo,
                    "periodo": parte_periodo,
                    "semestre": SEMESTRE_MAPA.get(sem, "DESCONOCIDO")
                }
                asign_text = ("Optativa Técnico - Tecnológica" if tipo == "A"
                              else "Optativa Humanístico - Estética")
                horario = f"{dia} {hi} a {hf} hrs"
                datos = {
                    "tipo": tipo, "asignatura": asign_text, "curso": nombre_opt,
                    "docente": docente_str, "coordinador(a)": coord,
                    "horario": horario, "salon": salon
                }
                pdf_name = f"OP_{tipo}_{nombre_opt}_{sem}.pdf"
                out = os.path.join(carpeta, pdf_name)
                try:
                    creacion_de_listas(tabla, datos, lista, out)
                except Exception as e:
                    print(f"Error en {out}: {e}")

        QMessageBox.information(self.widget, "Listas", "¡Listas generadas exitosamente!")

    def _proc_doc(self, nombre):
        parts = nombre.split()
        if len(parts) >= 3:
            return f"{parts[0]} {parts[-2]}"
        if len(parts) == 2:
            return nombre
        return nombre

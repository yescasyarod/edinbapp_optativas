# proyecto/tabs/tab_optativas.py

import csv
from datetime import datetime

from PySide6.QtCore import Qt, QTime, Signal, QObject
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QTabWidget, QGridLayout,
    QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QCheckBox, QSpinBox, QTimeEdit, QFileDialog, QMessageBox, QComboBox
)
from PySide6.QtGui import QFont, QPalette, QColor
from utils import obtener_ruta


class TabOptativas(QObject):
    optativas_changed = Signal()
    def __init__(self, db, is_admin=True):
        super().__init__() 
        self.db = db
        self.is_admin = is_admin

        self.editando_optativa = False
        self.editando_optativa_id = None
        self.editando_optativa_tipo = None
        self.editando_optativa_fila = -1

        self.semestre_checkboxes = []

        self._setup_ui()
        self._connect_signals()

        if not self.is_admin:
            self.btn_cargar_optativas_a.hide()
            self.btn_cargar_optativas_b.hide()

        self.cargar_optativas()
        self.cargar_docentes_optativas()

    # ─────────────────────────── UI ───────────────────────────
    def _setup_ui(self):
        # Contenedor único
        self.widget = QWidget()
        self.widget.setGeometry(0, 0, 1366, 768)

        # ——— Tabs A/B ———
        from PySide6.QtWidgets import QAbstractItemView
        from PySide6.QtGui import QPalette, QColor

        self.tabs = QTabWidget(self.widget)
        self.tabs.setGeometry(10, 10, 1360, 760)

        # ====== TAB A ======
        tab_a = QWidget(self.tabs)
        self.tabs.addTab(tab_a, "Asignaturas A")

        self.btn_cargar_optativas_a = QPushButton("Cargar Asignaturas A (csv)", tab_a)
        self.btn_cargar_optativas_a.setGeometry(575, 360, 200, 30)

        self.buscar_optativa_a = QLineEdit(tab_a)
        self.buscar_optativa_a.setPlaceholderText("BUSCAR ASIGNATURA A")
        self.buscar_optativa_a.setGeometry(470, 10, 300, 30)

        lbl_a = QLabel("Asignaturas A", tab_a)
        lbl_a.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lbl_a.setGeometry(20, 10, 260, 30)
        lbl_a.setFont(QFont("Noto Sans", 20, QFont.Weight.Bold))
        lbl_a.setStyleSheet("color: rgb(12, 28, 140);")

        # Tabla A
        self.optativas_listado_a = QTableWidget(tab_a)
        self.optativas_listado_a.setGeometry(10, 50, 760, 300)
        self.optativas_listado_a.setColumnCount(12)
        self.optativas_listado_a.setHorizontalHeaderLabels([
            "Optativa", "Docente", "Semestres", "Cupo",
            "Día", "Inicio", "Fin", "Salón",
            "ID (oculto)", "RFC Docente (oculto)",
            "RFC Segundo Docente (oculto)", "Ciclo (oculto)"
        ])
        for col in range(8, 12):
            self.optativas_listado_a.setColumnHidden(col, True)
        self.optativas_listado_a.setAlternatingRowColors(True)
        self.optativas_listado_a.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.optativas_listado_a.horizontalHeader().setStretchLastSection(True)
        self.optativas_listado_a.setStyleSheet(
            "background-color: #d9dced; alternate-background-color: #e8eaf4;"
        )
        self.optativas_listado_a.horizontalHeader().setStyleSheet(
            "background-color: #bfc4e0; font-weight: bold; color: #0c1c8c;"
        )

        # Selección fila completa, única, con fondo blanco y texto azul
        self.optativas_listado_a.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.optativas_listado_a.setSelectionMode(QAbstractItemView.SingleSelection)
        pal_a = self.optativas_listado_a.palette()
        pal_a.setColor(QPalette.Highlight, QColor("white"))
        pal_a.setColor(QPalette.HighlightedText, QColor(12, 28, 140))
        self.optativas_listado_a.setPalette(pal_a)

        self.editar_optativa_a = QPushButton("Editar A", tab_a)
        self.editar_optativa_a.setGeometry(10, 360, 100, 30)
        self.quitar_optativa_a = QPushButton("Quitar A", tab_a)
        self.quitar_optativa_a.setGeometry(120, 360, 100, 30)

        # ====== TAB B ======
        tab_b = QWidget(self.tabs)
        self.tabs.addTab(tab_b, "Asignaturas B")

        self.btn_cargar_optativas_b = QPushButton("Cargar Asignaturas B (csv)", tab_b)
        self.btn_cargar_optativas_b.setGeometry(575, 360, 200, 30)

        self.buscar_optativa_b = QLineEdit(tab_b)
        self.buscar_optativa_b.setPlaceholderText("BUSCAR ASIGNATURA B")
        self.buscar_optativa_b.setGeometry(470, 10, 300, 30)

        lbl_b = QLabel("Asignaturas B", tab_b)
        lbl_b.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lbl_b.setGeometry(20, 10, 260, 30)
        lbl_b.setFont(QFont("Noto Sans", 20, QFont.Weight.Bold))
        lbl_b.setStyleSheet("color: rgb(12, 28, 140);")

        # Tabla B
        self.optativas_listado_b = QTableWidget(tab_b)
        self.optativas_listado_b.setGeometry(10, 50, 760, 300)
        self.optativas_listado_b.setColumnCount(12)
        self.optativas_listado_b.setHorizontalHeaderLabels([
            "Optativa", "Docente", "Semestres", "Cupo",
            "Día", "Inicio", "Fin", "Salón",
            "ID (oculto)", "RFC Docente (oculto)",
            "RFC Segundo Docente (oculto)", "Ciclo (oculto)"
        ])
        for col in range(8, 12):
            self.optativas_listado_b.setColumnHidden(col, True)
        self.optativas_listado_b.setAlternatingRowColors(True)
        self.optativas_listado_b.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.optativas_listado_b.horizontalHeader().setStretchLastSection(True)
        self.optativas_listado_b.setStyleSheet(
            "background-color: #d9dced; alternate-background-color: #e8eaf4;"
        )
        self.optativas_listado_b.horizontalHeader().setStyleSheet(
            "background-color: #bfc4e0; font-weight: bold; color: #0c1c8c;"
        )

        # Selección para B
        self.optativas_listado_b.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.optativas_listado_b.setSelectionMode(QAbstractItemView.SingleSelection)
        pal_b = self.optativas_listado_b.palette()
        pal_b.setColor(QPalette.Highlight, QColor("white"))
        pal_b.setColor(QPalette.HighlightedText, QColor(12, 28, 140))
        self.optativas_listado_b.setPalette(pal_b)

        self.editar_optativa_b = QPushButton("Editar B", tab_b)
        self.editar_optativa_b.setGeometry(10, 360, 100, 30)
        self.quitar_optativa_b = QPushButton("Quitar B", tab_b)
        self.quitar_optativa_b.setGeometry(120, 360, 100, 30)

        # ——— Panel derecho ———
        x0 = 800
        y = 10

        lbl_ciclo = QLabel("Ciclo escolar", self.widget)
        lbl_ciclo.setGeometry(35, 580, 120, 20)
        self.combo_ciclo_escolar = QComboBox(self.widget)
        self._populate_ciclos()
        self.combo_ciclo_escolar.setGeometry(30, 600, 150, 30)

        y += 80
        lbl_nom = QLabel("AGREGAR OPTATIVA", self.widget)
        lbl_nom.setGeometry(35, 480, 180, 20)
        lbl_nom.setFont(QFont("Noto Sans", 12, QFont.Weight.Bold))
        lbl_nom.setStyleSheet("color: rgb(12,28,140);")
        self.nombre_optativa = QLineEdit(self.widget)
        self.nombre_optativa.setGeometry(30, 510, 250, 30)
        self.nombre_optativa.setPlaceholderText("NOMBRE DE LA OPTATIVA")

        y += 80
        lbl_sems = QLabel("Semestres", self.widget)
        lbl_sems.setGeometry(330, 480, 100, 20)
        sems = ["1°","2°","3°","4°","5°","6°","7°"]
        for i, s in enumerate(sems):
            cb = QCheckBox(s, self.widget)
            self.semestre_checkboxes.append(cb)
            cb.setGeometry(330 + (i % 4) * 20, 480 + 25 + (i // 4) * 30, 50, 25)

        y += 120
        lbl_cupo = QLabel("Cupo", self.widget)
        lbl_cupo.setGeometry(330, 580, 50, 20)
        self.cupo = QSpinBox(self.widget)
        self.cupo.setGeometry(330, 600, 80, 30)

        y += 80
        lbl_dia = QLabel("Día", self.widget)
        lbl_dia.setGeometry(470, 480, 40, 20)
        self.combo_dia = QComboBox(self.widget)
        self.combo_dia.addItems(["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado"])
        self.combo_dia.setGeometry(470, 500, 130, 30)

        y += 80
        lbl_ini = QLabel("Horario Inicio", self.widget)
        lbl_ini.setGeometry(640, 480, 100, 20)
        self.fecha_inicio = QTimeEdit(QTime(12,0), self.widget)
        self.fecha_inicio.setGeometry(640, 500, 100, 30)

        y += 80
        lbl_fin = QLabel("Horario Fin", self.widget)
        lbl_fin.setGeometry(680, 580, 100, 20)
        self.fecha_final = QTimeEdit(QTime(14,0), self.widget)
        self.fecha_final.setGeometry(680, 600, 100, 30)

        y += 80
        lbl_salon = QLabel("Salón", self.widget)
        lbl_salon.setGeometry(470, 580, 35, 20)
        self.salones = QComboBox(self.widget)
        self.salones.addItems([
            "102","103","104","109","110","201","202","206","209/lab tintes",
            "301","304","306","401","402","Artesanías","Auditorio","Biblioteca",
            "Laboratorio 1","Laboratorio 2","Laboratorio 4","Laboratorio de Fotografía",
            "Taller de Cerámica","Taller de Maderas","Taller de Serigrafía",
            "Taller de Tejido plano","UP1","UP4","UP5","UP6","UP7","UP8","UP8/Taller de Serigrafía"
        ])
        self.salones.setGeometry(470, 600, 170, 30)

        y += 80
        self.agregar_optativa = QPushButton("Agregar", self.widget)
        self.agregar_optativa.setGeometry(810, 600, 100, 30)

        # ——— Listado de docentes ———
        y = 10
        self.buscar_docente = QLineEdit(self.widget)
        self.buscar_docente.setGeometry(800, 45, 240, 30)
        self.buscar_docente.setPlaceholderText("BUSCAR DOCENTE")

        y += 80
        self.listado_docentes = QTableWidget(self.widget)
        self.listado_docentes.setGeometry(800, 85, 240, 300)
        self.listado_docentes.setColumnCount(2)
        self.listado_docentes.setHorizontalHeaderLabels(["RFC", "Docente"])
        self.listado_docentes.setAlternatingRowColors(True)
        self.listado_docentes.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.listado_docentes.horizontalHeader().setStretchLastSection(True)
        self.listado_docentes.setStyleSheet(
            "background-color: #d9dced; alternate-background-color: #e8eaf4; color: rgb(12,28,140);"
        )
        self.listado_docentes.horizontalHeader().setStyleSheet(
            "background-color: #bfc4e0; font-weight: bold; color: #0c1c8c;"
        )

        # Selección en listado_docentes
        self.listado_docentes.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.listado_docentes.setSelectionMode(QAbstractItemView.SingleSelection)
        pal_d1 = self.listado_docentes.palette()
        pal_d1.setColor(QPalette.Highlight, QColor("white"))
        pal_d1.setColor(QPalette.HighlightedText, QColor(12, 28, 140))
        self.listado_docentes.setPalette(pal_d1)

        y += 200
        self.check_segundo_docente = QCheckBox("Agregar segundo docente", self.widget)
        self.check_segundo_docente.setGeometry(800, 400, 200, 25)

        y += 40
        self.listado_segundo_docentes = QTableWidget(self.widget)
        self.listado_segundo_docentes.setGeometry(1050, 85, 240, 300)
        self.listado_segundo_docentes.setColumnCount(2)
        self.listado_segundo_docentes.setHorizontalHeaderLabels(["RFC", "Docente"])
        self.listado_segundo_docentes.setAlternatingRowColors(True)
        self.listado_segundo_docentes.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.listado_segundo_docentes.horizontalHeader().setStretchLastSection(True)
        self.listado_segundo_docentes.setStyleSheet(
            "background-color: #d9dced; alternate-background-color: #e8eaf4; color: rgb(12,28,140);"
        )
        self.listado_segundo_docentes.horizontalHeader().setStyleSheet(
            "background-color: #bfc4e0; font-weight: bold; color: #0c1c8c;"
        )
        self.listado_segundo_docentes.hide()

        # Selección en listado_segundo_docentes
        self.listado_segundo_docentes.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.listado_segundo_docentes.setSelectionMode(QAbstractItemView.SingleSelection)
        pal_d2 = self.listado_segundo_docentes.palette()
        pal_d2.setColor(QPalette.Highlight, QColor("white"))
        pal_d2.setColor(QPalette.HighlightedText, QColor(12, 28, 140))
        self.listado_segundo_docentes.setPalette(pal_d2)

        # Ajuste inicial de paridad
        self._aplicar_paridad_semestres()



    def _bloquear_docentes_y_semestres(self, bloquear: bool):
        # Bloquear tablas de docentes
        self.listado_docentes.setDisabled(bloquear)
        self.listado_segundo_docentes.setDisabled(bloquear)
        self.check_segundo_docente.setDisabled(bloquear)
        self.buscar_docente.setDisabled(bloquear)
        # Bloquear checkboxes de semestres
        for cb in self.semestre_checkboxes:
            cb.setDisabled(bloquear)
        # Visualmente: cambia el estilo para que se note desactivado
        style = (
            "background-color: #e0e0e0; color: #a0a0a0;"
            if bloquear else
            "background-color: #d9dced; alternate-background-color: #e8eaf4; color: rgb(12,28,140);"
        )
        self.listado_docentes.setStyleSheet(style)
        self.listado_segundo_docentes.setStyleSheet(style)
    # ─────────────────────────── Señales ───────────────────────────
    def _connect_signals(self):
        # CSV
        self.btn_cargar_optativas_a.clicked.connect(self.cargar_optativas_a_csv)
        self.btn_cargar_optativas_b.clicked.connect(self.cargar_optativas_b_csv)
        self.buscar_optativa_a.textChanged.connect(self.filtrar_optativas_a)
        self.buscar_optativa_b.textChanged.connect(self.filtrar_optativas_b)

        # Edit / Quitar
        self.editar_optativa_a.clicked.connect(self.edit_optativa_a)
        self.quitar_optativa_a.clicked.connect(self.optativa_a_quitada)
        self.editar_optativa_b.clicked.connect(self.edit_optativa_b)
        self.quitar_optativa_b.clicked.connect(self.optativa_b_quitada)

        # Agregar / Actualizar
        self.agregar_optativa.clicked.connect(self.optativa_agregada)

        # Filtrado docentes
        self.buscar_docente.textChanged.connect(self.filtrar_docentes_optativas)

        # Mostrar/ocultar segundo docente
        self.check_segundo_docente.toggled.connect(self._toggle_segundo_docente)

        # Limpiar al cambiar pestaña
        self.tabs.currentChanged.connect(lambda _: self.limpiar_campos_optativas())

        # Cambiar ciclo escolar ⇒ ajustar paridad semestres
        self.combo_ciclo_escolar.currentIndexChanged.connect(self._aplicar_paridad_semestres)

    # ─────────────────────────── Helpers ───────────────────────────
    def _populate_ciclos(self):
        """Genera dos opciones dinámicas: (año-1)-(año)/2 y (año)-(año+1)/1"""
        y = datetime.now().year
        ciclo2 = f"{y-1}-{y}/2"
        ciclo1 = f"{y}-{y+1}/1"
        self.combo_ciclo_escolar.addItems([ciclo2, ciclo1])
        idx = self.combo_ciclo_escolar.findText(ciclo1)
        if idx >= 0:
            self.combo_ciclo_escolar.setCurrentIndex(idx)

    def filtrar_optativas_a(self, texto: str):
        self._filtrar_optativas(self.optativas_listado_a, texto)

    def filtrar_optativas_b(self, texto: str):
        self._filtrar_optativas(self.optativas_listado_b, texto)

    def _filtrar_optativas(self, table: QTableWidget, texto: str):
        texto = texto.lower().strip()
        for row in range(table.rowCount()):
            item = table.item(row, 0)  # columna “Optativa”
            match = texto in item.text().lower() if item else False
            table.setRowHidden(row, not match)
            
    def _aplicar_paridad_semestres(self):
        """Muestra sólo semestres pares si el ciclo termina en '/2', impares si '/1'."""
        texto = self.combo_ciclo_escolar.currentText()
        es_par = texto.endswith("/2")
        for cb in self.semestre_checkboxes:
            numero = int(cb.text().replace("°", ""))
            mostrar = (numero % 2 == 0) if es_par else (numero % 2 == 1)
            cb.setVisible(mostrar)
            # Solo desmarcar si NO estamos editando y bloqueando campos
            if not (self.editando_optativa and cb.isEnabled() is False):
                if not mostrar:
                    cb.setChecked(False)

    def _toggle_segundo_docente(self, checked: bool):
        self.listado_segundo_docentes.setVisible(checked)
        if not checked:
            self.listado_segundo_docentes.clearSelection()
            for i in range(self.listado_segundo_docentes.rowCount()):
                self.listado_segundo_docentes.setRowHidden(i, False)

    # ─────────────────────────── Datos ───────────────────────────
    def cargar_optativas(self):
        self.optativas_listado_a.setRowCount(0)
        self.optativas_listado_b.setRowCount(0)
        query = """
            SELECT o.id, o.tipo, o.nombre,
                   d1.nombre, d1.apellido_paterno, d1.apellido_materno,
                   d2.nombre, d2.apellido_paterno, d2.apellido_materno,
                   o.semestres, o.cupo, o.dia, o.inicio, o.fin,
                   o.salon, o.rfc_docente, o.rfc_segundo_docente, o.ciclo
            FROM optativas o
            JOIN docentes d1 ON o.rfc_docente = d1.rfc
            LEFT JOIN docentes d2 ON o.rfc_segundo_docente = d2.rfc
            ORDER BY o.nombre
        """
        rows = self.db.run_query(query, fetch="all") or []
        for (opt_id, tipo, nom_opt,
             d1n, d1p, d1m,
             d2n, d2p, d2m,
             sems, cupo, dia, inicio, fin,
             salon, rfc_doc, rfc_seg, ciclo) in rows:

            docente_comp = f"{d1n} {d1p} {d1m}" + (f" & {d2n} {d2p} {d2m}" if d2n else "")
            table = self.optativas_listado_a if tipo == "A" else self.optativas_listado_b
            f_row = table.rowCount()
            table.insertRow(f_row)
            table.setItem(f_row, 0, QTableWidgetItem(nom_opt))
            table.setItem(f_row, 1, QTableWidgetItem(docente_comp))
            table.setItem(f_row, 2, QTableWidgetItem(sems or ""))
            table.setItem(f_row, 3, QTableWidgetItem(str(cupo)))
            table.setItem(f_row, 4, QTableWidgetItem(dia))
            table.setItem(f_row, 5, QTableWidgetItem(inicio))
            table.setItem(f_row, 6, QTableWidgetItem(fin))
            table.setItem(f_row, 7, QTableWidgetItem(salon))
            table.setItem(f_row, 8, QTableWidgetItem(str(opt_id)))
            table.setItem(f_row, 9, QTableWidgetItem(rfc_doc))
            table.setItem(f_row, 10, QTableWidgetItem(rfc_seg or ""))
            table.setItem(f_row, 11, QTableWidgetItem(ciclo))

    def cargar_docentes_optativas(self):
        self.listado_docentes.setRowCount(0)
        rows = self.db.run_query(
            "SELECT rfc, nombre, apellido_paterno, apellido_materno FROM docentes "
            "ORDER BY nombre, apellido_paterno, apellido_materno",
            fetch="all"
        ) or []
        for i, (rfc, nom, ap, am) in enumerate(rows):
            self.listado_docentes.insertRow(i)
            self.listado_docentes.setItem(i, 0, QTableWidgetItem(rfc))
            self.listado_docentes.setItem(i, 1, QTableWidgetItem(f"{nom} {ap} {am}"))
        self.cargar_docentes_segundo_optativas()

    def cargar_docentes_segundo_optativas(self):
        self.listado_segundo_docentes.setRowCount(0)
        rows = self.db.run_query(
            "SELECT rfc, nombre, apellido_paterno, apellido_materno FROM docentes "
            "ORDER BY nombre, apellido_paterno, apellido_materno",
            fetch="all"
        ) or []
        for i, (rfc, nom, ap, am) in enumerate(rows):
            self.listado_segundo_docentes.insertRow(i)
            self.listado_segundo_docentes.setItem(i, 0, QTableWidgetItem(rfc))
            self.listado_segundo_docentes.setItem(i, 1, QTableWidgetItem(f"{nom} {ap} {am}"))

    # ─────────────────────────── CRUD ───────────────────────────
    def optativa_agregada(self):
        tipo = "A" if self.tabs.currentIndex() == 0 else "B"
        nombre = self.nombre_optativa.text().strip()
        if not nombre:
            return

        ciclo = self.combo_ciclo_escolar.currentText().strip()

        row_docente = self.listado_docentes.currentRow()
        if row_docente < 0:
            return
        rfc_doc = self.listado_docentes.item(row_docente, 0).text()

        rfc_segundo_doc = ""
        if self.check_segundo_docente.isChecked():
            row2 = self.listado_segundo_docentes.currentRow()
            if row2 >= 0:
                rfc_segundo_doc = self.listado_segundo_docentes.item(row2, 0).text()

        cupo_valor = self.cupo.value()
        dia = self.combo_dia.currentText()
        inicio = self.fecha_inicio.time().toString("HH:mm")
        fin = self.fecha_final.time().toString("HH:mm")
        salon = self.salones.currentText().strip()

        sem_checked = [cb.text() for cb in self.semestre_checkboxes if cb.isChecked()]
        semestres_str = ",".join(sem_checked)

        if self.editando_optativa and self.editando_optativa_tipo == tipo:
            count_ins = self.db.run_query(
                "SELECT COUNT(*) FROM inscripciones WHERE optativa_id=?",
                (self.editando_optativa_id,), fetch="one"
            )[0]
            if cupo_valor < count_ins:
                QMessageBox.warning(
                    self.widget, "Advertencia",
                    "El cupo no puede ser menor que el número de inscripciones existentes."
                )
                return
            self.db.run_query(
                """UPDATE optativas
                   SET tipo=?, nombre=?, rfc_docente=?, rfc_segundo_docente=?, semestres=?, cupo=?, dia=?, inicio=?, fin=?, salon=?, ciclo=?
                   WHERE id=?""",
                (tipo, nombre, rfc_doc, rfc_segundo_doc, semestres_str,
                 cupo_valor, dia, inicio, fin, salon, ciclo, self.editando_optativa_id)
            )
        else:
            self.db.run_query(
                """INSERT INTO optativas(tipo, nombre, rfc_docente, rfc_segundo_docente,
                                        semestres, cupo, dia, inicio, fin, salon, ciclo)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (tipo, nombre, rfc_doc, rfc_segundo_doc, semestres_str,
                 cupo_valor, dia, inicio, fin, salon, ciclo)
            )

        self.limpiar_campos_optativas()
        self.cargar_optativas()
        self.optativas_changed.emit()

    def limpiar_campos_optativas(self):
        self.combo_dia.setCurrentIndex(0)
        self.nombre_optativa.clear()
        for cb in self.semestre_checkboxes:
            cb.setChecked(False)
        self.cupo.setValue(0)
        self.fecha_inicio.setTime(QTime(12, 0))
        self.fecha_final.setTime(QTime(14, 0))
        self.salones.setCurrentIndex(0)
        self.check_segundo_docente.setChecked(False)

        self.editando_optativa = False
        self.editando_optativa_id = None
        self.editando_optativa_tipo = None
        self.agregar_optativa.setText("Agregar")

        self._aplicar_paridad_semestres()
        self._bloquear_docentes_y_semestres(False)

    def optativa_a_quitada(self):
        fila = self.optativas_listado_a.currentRow()
        if fila < 0:
            return
        opt_id = int(self.optativas_listado_a.item(fila, 8).text())
        reply = QMessageBox.question(
            self.widget, "Advertencia",
            "¿Está seguro de quitar la optativa A seleccionada?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.run_query("DELETE FROM optativas WHERE id=?", (opt_id,))
            self.optativas_listado_a.removeRow(fila)
            self.optativas_changed.emit()

    def optativa_b_quitada(self):
        fila = self.optativas_listado_b.currentRow()
        if fila < 0:
            return
        opt_id = int(self.optativas_listado_b.item(fila, 8).text())
        reply = QMessageBox.question(
            self.widget, "Advertencia",
            "¿Está seguro de quitar la optativa B seleccionada?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.run_query("DELETE FROM optativas WHERE id=?", (opt_id,))
            self.optativas_listado_b.removeRow(fila)
            self.optativas_changed.emit()

    def edit_optativa_a(self):
        fila = self.optativas_listado_a.currentRow()
        if fila < 0:
            return
        self._edit_optativa(self.optativas_listado_a, fila, "A")

    def edit_optativa_b(self):
        fila = self.optativas_listado_b.currentRow()
        if fila < 0:
            return
        self._edit_optativa(self.optativas_listado_b, fila, "B")

    def _edit_optativa(self, table, fila, tipo):
        self.editando_optativa = True
        # Bloquear docentes y semestres (inicialmente)
        self._bloquear_docentes_y_semestres(True)
        # REHABILITAR sólo los checkboxes de semestres para permitir edición
        for cb in self.semestre_checkboxes:
            cb.setDisabled(False)

        self.editando_optativa_tipo = tipo
        self.editando_optativa_id = int(table.item(fila, 8).text())
        self.agregar_optativa.setText("Aceptar")

        # Día
        dia = table.item(fila, 4).text()
        idx = self.combo_dia.findText(dia)
        if idx >= 0:
            self.combo_dia.setCurrentIndex(idx)

        # Nombre / Ciclo
        self.nombre_optativa.setText(table.item(fila, 0).text())
        ciclo = table.item(fila, 11).text()
        idxc = self.combo_ciclo_escolar.findText(ciclo)
        if idxc >= 0:
            self.combo_ciclo_escolar.setCurrentIndex(idxc)
        self._aplicar_paridad_semestres()

        # Semestres
        sems = [s.strip() for s in table.item(fila, 2).text().split(",")]
        for cb in self.semestre_checkboxes:
            cb.setChecked(cb.text() in sems and cb.isVisible())

        # Cupo
        self.cupo.setValue(int(table.item(fila, 3).text()))

        # Horario
        hi = table.item(fila, 5).text().split(":")
        hf = table.item(fila, 6).text().split(":")
        if len(hi) == 2:
            self.fecha_inicio.setTime(QTime(int(hi[0]), int(hi[1])))
        if len(hf) == 2:
            self.fecha_final.setTime(QTime(int(hf[0]), int(hf[1])))

        # Salón
        self.salones.setCurrentText(table.item(fila, 7).text())

        # Docentes
        rfc1 = table.item(fila, 9).text()
        for i in range(self.listado_docentes.rowCount()):
            if self.listado_docentes.item(i, 0).text() == rfc1:
                self.listado_docentes.selectRow(i)
                break

        rfc2 = table.item(fila, 10).text()
        if rfc2:
            self.check_segundo_docente.setChecked(True)
            self.listado_segundo_docentes.show()
            for i in range(self.listado_segundo_docentes.rowCount()):
                if self.listado_segundo_docentes.item(i, 0).text() == rfc2:
                    self.listado_segundo_docentes.selectRow(i)
                    break
        else:
            self.check_segundo_docente.setChecked(False)


    # ─────────────────────────── Util ───────────────────────────
    def filtrar_docentes_optativas(self, texto):
        texto = texto.lower().strip()
        for tbl in (self.listado_docentes, self.listado_segundo_docentes):
            for i in range(tbl.rowCount()):
                rfc = tbl.item(i, 0).text().lower()
                nom = tbl.item(i, 1).text().lower()
                ocultar = bool(texto) and texto not in rfc and texto not in nom
                tbl.setRowHidden(i, ocultar)

    # ───────────────────────── CSV ─────────────────────────
    def cargar_optativas_a_csv(self):
        fn, _ = QFileDialog.getOpenFileName(
            self.widget, "Selecciona CSV de Optativas A",
            obtener_ruta("datos"), "CSV Files (*.csv)"
        )
        if not fn:
            return
        self.db.run_query("DELETE FROM optativas WHERE tipo='A'")
        self._leer_csv_e_insertar(fn)
        self.cargar_optativas()
        self.optativas_changed.emit()

    def cargar_optativas_b_csv(self):
        fn, _ = QFileDialog.getOpenFileName(
            self.widget, "Selecciona CSV de Optativas B",
            obtener_ruta("datos"), "CSV Files (*.csv)"
        )
        if not fn:
            return
        self.db.run_query("DELETE FROM optativas WHERE tipo='B'")
        self._leer_csv_e_insertar(fn)
        self.cargar_optativas()
        self.optativas_changed.emit()

    def _leer_csv_e_insertar(self, fn):
        import csv

        with open(fn, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Normalizar valores base
                tipo = (row.get("tipo", "") or "").strip().upper()
                nombre = (row.get("nombre", "") or "").strip()

                # 1) Validaciones mínimas: descartar filas vacías
                if tipo not in ("A", "B"):
                    continue
                if not nombre:
                    continue  # No insertamos "A,,,,,0,,,,," y similares

                rfc_docente = (row.get("rfc_docente", "") or "").strip()
                rfc_seg = (row.get("rfc_segundo_docente", "") or "").strip() or None
                semestres = (row.get("semestres", "") or "").strip()

                # cupo entero (default 0)
                cupo_raw = (row.get("cupo", "") or "").strip()
                try:
                    cupo = int(cupo_raw) if cupo_raw else 0
                except ValueError:
                    cupo = 0

                dia = (row.get("dia", "") or "").strip()
                inicio = (row.get("inicio", "") or "").strip()
                fin = (row.get("fin", "") or "").strip()
                salon = (row.get("salon", "") or "").strip()
                ciclo = (row.get("ciclo", "") or "").strip()

                # 2) Insert seguro
                self.db.run_query(
                    "INSERT INTO optativas (tipo,nombre,rfc_docente,rfc_segundo_docente,semestres,cupo,dia,inicio,fin,salon,ciclo) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (tipo, nombre, rfc_docente, rfc_seg, semestres, cupo, dia, inicio, fin, salon, ciclo)
                )

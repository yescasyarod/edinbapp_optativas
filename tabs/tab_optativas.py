# proyecto/tabs/tab_optativas.py

import csv
from datetime import datetime

from PySide6.QtCore import Qt, QTime
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QTabWidget, QGridLayout,
    QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QCheckBox, QSpinBox, QTimeEdit, QFileDialog, QMessageBox, QComboBox
)
from utils import obtener_ruta


class TabOptativas:
    def __init__(self, db, is_admin=True):
        self.db = db
        self.is_admin = is_admin

        self.editando_optativa = False
        self.editando_optativa_id = None
        self.editando_optativa_tipo = None
        self.editando_optativa_fila = -1

        # referencias a widgets que usamos después
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
        self.widget = QWidget()
        main_layout = QHBoxLayout(self.widget)

        # ----- Tabs A/B -----
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, stretch=4)

        # ====== TAB A ======
        tab_a = QWidget()
        la = QVBoxLayout(tab_a)

        self.btn_cargar_optativas_a = QPushButton("Cargar Optativas A (csv)")
        la.addWidget(self.btn_cargar_optativas_a)
        la.addWidget(QLabel("Optativas A", alignment=Qt.AlignmentFlag.AlignCenter))

        self.optativas_listado_a = QTableWidget()
        self.optativas_listado_a.setColumnCount(12)
        self.optativas_listado_a.setHorizontalHeaderLabels([
            "Optativa", "Docente", "Semestres", "Cupo", "Día", "Inicio", "Fin", "Salón",
            "ID (oculto)", "RFC Docente (oculto)", "RFC Segundo Docente (oculto)", "Ciclo (oculto)"
        ])
        for col in range(8, 12):
            self.optativas_listado_a.setColumnHidden(col, True)
        self.optativas_listado_a.setAlternatingRowColors(True)
        self.optativas_listado_a.setStyleSheet(
            "background-color: #d9dced; alternate-background-color: #e8eaf4;"
        )
        self.optativas_listado_a.horizontalHeader().setStyleSheet(
            "background-color: #bfc4e0; font-weight: bold; color: #0c1c8c;"
        )
        la.addWidget(self.optativas_listado_a)

        btns_a = QHBoxLayout()
        self.editar_optativa_a = QPushButton("Editar A")
        self.quitar_optativa_a = QPushButton("Quitar A")
        btns_a.addWidget(self.editar_optativa_a)
        btns_a.addWidget(self.quitar_optativa_a)
        la.addLayout(btns_a)

        self.tabs.addTab(tab_a, "Optativas A")

        # ====== TAB B ======
        tab_b = QWidget()
        lb = QVBoxLayout(tab_b)

        self.btn_cargar_optativas_b = QPushButton("Cargar Optativas B (csv)")
        lb.addWidget(self.btn_cargar_optativas_b)
        lb.addWidget(QLabel("Optativas B", alignment=Qt.AlignmentFlag.AlignCenter))

        self.optativas_listado_b = QTableWidget()
        self.optativas_listado_b.setColumnCount(12)
        self.optativas_listado_b.setHorizontalHeaderLabels([
            "Optativa", "Docente", "Semestres", "Cupo", "Día", "Inicio", "Fin", "Salón",
            "ID (oculto)", "RFC Docente (oculto)", "RFC Segundo Docente (oculto)", "Ciclo (oculto)"
        ])
        for col in range(8, 12):
            self.optativas_listado_b.setColumnHidden(col, True)
        self.optativas_listado_b.setAlternatingRowColors(True)
        self.optativas_listado_b.setStyleSheet(
            "background-color: #d9dced; alternate-background-color: #e8eaf4;"
        )
        self.optativas_listado_b.horizontalHeader().setStyleSheet(
            "background-color: #bfc4e0; font-weight: bold; color: #0c1c8c;"
        )
        lb.addWidget(self.optativas_listado_b)

        btns_b = QHBoxLayout()
        self.editar_optativa_b = QPushButton("Editar B")
        self.quitar_optativa_b = QPushButton("Quitar B")
        btns_b.addWidget(self.editar_optativa_b)
        btns_b.addWidget(self.quitar_optativa_b)
        lb.addLayout(btns_b)

        self.tabs.addTab(tab_b, "Optativas B")

        # ----- Panel derecho -----
        derecha = QWidget()
        gd = QGridLayout(derecha)

        # Col izquierda (vertical, col=0)
        row = 0

        gd.addWidget(QLabel("Ciclo escolar"), row, 0)
        row += 1
        self.combo_ciclo_escolar = QComboBox()
        self._populate_ciclos()
        gd.addWidget(self.combo_ciclo_escolar, row, 0)

        row += 1
        gd.addWidget(QLabel("Optativa"), row, 0)
        row += 1
        self.nombre_optativa = QLineEdit()
        gd.addWidget(self.nombre_optativa, row, 0)

        row += 1
        gd.addWidget(QLabel("Semestres"), row, 0)
        row += 1
        sems_widget = QWidget()
        sg = QGridLayout(sems_widget)
        semestres = ["1°", "2°", "3°", "4°", "5°", "6°", "7°"]
        for i, s in enumerate(semestres):
            cb = QCheckBox(s)
            self.semestre_checkboxes.append(cb)
            sg.addWidget(cb, i // 4, i % 4)
        sems_widget.setLayout(sg)
        gd.addWidget(sems_widget, row, 0)

        row += 1
        gd.addWidget(QLabel("Cupo"), row, 0)
        row += 1
        self.cupo = QSpinBox()
        gd.addWidget(self.cupo, row, 0)

        # Día
        row += 1
        gd.addWidget(QLabel("Día"), row, 0)
        row += 1
        self.combo_dia = QComboBox()
        self.combo_dia.addItems(["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"])
        gd.addWidget(self.combo_dia, row, 0)

        # Horario
        row += 1
        gd.addWidget(QLabel("Horario Inicio"), row, 0)
        row += 1
        self.fecha_inicio = QTimeEdit(QTime(12, 0))
        gd.addWidget(self.fecha_inicio, row, 0)

        row += 1
        gd.addWidget(QLabel("Horario Fin"), row, 0)
        row += 1
        self.fecha_final = QTimeEdit(QTime(14, 0))
        gd.addWidget(self.fecha_final, row, 0)

        # Salón
        row += 1
        gd.addWidget(QLabel("Salón"), row, 0)
        row += 1
        self.salones = QLineEdit()
        gd.addWidget(self.salones, row, 0)

        # Botón agregar/actualizar
        row += 1
        self.agregar_optativa = QPushButton("Agregar")
        gd.addWidget(self.agregar_optativa, row, 0)

        # Bloque Docentes (col=2)
        col_doc = 2
        rdoc = 0
        gd.addWidget(QLabel("Buscar docente"), rdoc, col_doc)
        rdoc += 1
        self.buscar_docente = QLineEdit()
        gd.addWidget(self.buscar_docente, rdoc, col_doc)

        rdoc += 1
        gd.addWidget(QLabel("Docentes"), rdoc, col_doc)
        rdoc += 1
        self.listado_docentes = QTableWidget()
        self.listado_docentes.setColumnCount(2)
        self.listado_docentes.setHorizontalHeaderLabels(["RFC", "Docente"])
        self.listado_docentes.horizontalHeader().setStretchLastSection(True)
        self.listado_docentes.setAlternatingRowColors(True)
        self.listado_docentes.setStyleSheet(
            "background-color: #d9dced; alternate-background-color: #e8eaf4;"
        )
        self.listado_docentes.horizontalHeader().setStyleSheet(
            "background-color: #bfc4e0; font-weight: bold; color: #0c1c8c;"
        )
        gd.addWidget(self.listado_docentes, rdoc, col_doc, 6, 1)

        rdoc += 6
        self.check_segundo_docente = QCheckBox("Agregar segundo docente")
        gd.addWidget(self.check_segundo_docente, rdoc, col_doc)

        rdoc += 1
        self.listado_segundo_docentes = QTableWidget()
        self.listado_segundo_docentes.setColumnCount(2)
        self.listado_segundo_docentes.setHorizontalHeaderLabels(["RFC", "Docente"])
        self.listado_segundo_docentes.horizontalHeader().setStretchLastSection(True)
        self.listado_segundo_docentes.setAlternatingRowColors(True)
        self.listado_segundo_docentes.setStyleSheet(
            "background-color: #d9dced; alternate-background-color: #e8eaf4;"
        )
        self.listado_segundo_docentes.horizontalHeader().setStyleSheet(
            "background-color: #bfc4e0; font-weight: bold; color: #0c1c8c;"
        )
        self.listado_segundo_docentes.hide()
        gd.addWidget(self.listado_segundo_docentes, rdoc, col_doc, 4, 1)

        main_layout.addWidget(derecha, stretch=2)

        # Inicializa visibilidad de semestres según ciclo
        self._aplicar_paridad_semestres()

    def _connect_signals(self):
        # CSV
        self.btn_cargar_optativas_a.clicked.connect(self.cargar_optativas_a_csv)
        self.btn_cargar_optativas_b.clicked.connect(self.cargar_optativas_b_csv)

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
        # Por defecto selecciona el que tenga /1 (actual-inicio)
        idx = self.combo_ciclo_escolar.findText(ciclo1)
        if idx >= 0:
            self.combo_ciclo_escolar.setCurrentIndex(idx)

    def _aplicar_paridad_semestres(self):
        """Muestra sólo semestres pares si el ciclo termina en '/2', impares si '/1'."""
        texto = self.combo_ciclo_escolar.currentText()
        es_par = texto.endswith("/2")
        for cb in self.semestre_checkboxes:
            numero = int(cb.text().replace("°", ""))
            mostrar = (numero % 2 == 0) if es_par else (numero % 2 == 1)
            cb.setVisible(mostrar)
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
        salon = self.salones.text().strip()

        sem_checked = [cb.text() for cb in self.semestre_checkboxes if cb.isChecked()]
        semestres_str = ", ".join(sem_checked)

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

    def limpiar_campos_optativas(self):
        # No cambies el ciclo automáticamente
        self.combo_dia.setCurrentIndex(0)
        self.nombre_optativa.clear()
        for cb in self.semestre_checkboxes:
            cb.setChecked(False)
        self.cupo.setValue(0)
        self.fecha_inicio.setTime(QTime(12, 0))
        self.fecha_final.setTime(QTime(14, 0))
        self.salones.clear()
        self.check_segundo_docente.setChecked(False)

        self.editando_optativa = False
        self.editando_optativa_id = None
        self.editando_optativa_tipo = None
        self.agregar_optativa.setText("Agregar")

        # Vuelve a aplicar paridad
        self._aplicar_paridad_semestres()

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
        # Ajustar paridad
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
        self.salones.setText(table.item(fila, 7).text())

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

    def _leer_csv_e_insertar(self, fn):
        with open(fn, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                vals = (
                    row["tipo"].strip(), row["nombre"].strip(),
                    row["rfc_docente"].strip(), row["rfc_segundo_docente"].strip(),
                    row["semestres"].strip(),
                    int(row["cupo"]) if row["cupo"] else 0,
                    row.get("dia", "").strip(), row.get("inicio", "").strip(), row.get("fin", "").strip(),
                    row.get("salon", "").strip(), row.get("ciclo", "").strip()
                )
                self.db.run_query(
                    "INSERT INTO optativas(tipo,nombre,rfc_docente,rfc_segundo_docente,semestres,"
                    "cupo,dia,inicio,fin,salon,ciclo) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    vals
                )

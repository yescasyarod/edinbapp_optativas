# proyecto/tabs/tab_inscripciones.py

from PyQt6.QtCore import Qt, QTime
from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QComboBox, QLineEdit, QLabel,
    QTableWidget, QPushButton, QCheckBox, QHeaderView,
    QMessageBox, QTableWidgetItem
)

class TabInscripciones:
    def __init__(self, db):
        self.db = db
        self.widget = QWidget()
        self.ya_curso = {}  # almacena tuplas (yaA, yaB) por matrícula
        self._last_tab3_student_row = -1

        self._setup_ui()
        self._connect_signals()

        # Inicializar tablas al estilo original:
        self.cargar_estudiantes_tab3()
        if self.table_estudiantes_tab3.rowCount() > 0:
            self.table_estudiantes_tab3.selectRow(0)


    def _setup_ui(self):
        grid = QGridLayout(self.widget)

        # Controles de filtro
        self.combo_inscritos_tab3 = QComboBox()
        self.combo_inscritos_tab3.addItems(["No inscritos", "Inscritos"])
        grid.addWidget(self.combo_inscritos_tab3, 0, 0)

        self.combo_semestre_tab3 = QComboBox()
        self.combo_semestre_tab3.addItems(["Todos", "1°", "2°", "3°", "4°", "5°", "6°", "7°"])
        grid.addWidget(self.combo_semestre_tab3, 1, 0)

        self.line_search_estudiante_tab3 = QLineEdit()
        self.line_search_estudiante_tab3.setPlaceholderText("Buscar estudiante")
        grid.addWidget(self.line_search_estudiante_tab3, 2, 0)

        # Tabla Estudiantes
        grid.addWidget(QLabel("Estudiantes"), 3, 0)
        self.table_estudiantes_tab3 = QTableWidget()
        self.table_estudiantes_tab3.setColumnCount(4)
        self.table_estudiantes_tab3.setHorizontalHeaderLabels(
            ["Matrícula", "Nombre", "Semestre", "Condición"]
        )
        self.table_estudiantes_tab3.setAlternatingRowColors(True)
        hdr = self.table_estudiantes_tab3.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_estudiantes_tab3.setStyleSheet(
            "background-color: #d9dced; alternate-background-color: #e8eaf4;"
        )
        self.table_estudiantes_tab3.horizontalHeader().setStyleSheet(
            "background-color: #bfc4e0; font-weight: bold; color: #0c1c8c;"
        )
        grid.addWidget(self.table_estudiantes_tab3, 4, 0, 11, 1)

        # Checkboxes Ya cursó
        self.chk_ya_curso_a = QCheckBox("Ya cursó Optativa A")
        grid.addWidget(self.chk_ya_curso_a, 0, 1)
        self.chk_ya_curso_b = QCheckBox("Ya cursó Optativa B")
        grid.addWidget(self.chk_ya_curso_b, 0, 2)

        # Optativas A
        self.line_search_optativa_a = QLineEdit()
        self.line_search_optativa_a.setPlaceholderText("Buscar optativa A")
        grid.addWidget(self.line_search_optativa_a, 1, 1)
        grid.addWidget(QLabel("Optativas A"), 2, 1)
        self.optativas_listado_a_tab3 = QTableWidget()
        self.optativas_listado_a_tab3.setColumnCount(8)
        self.optativas_listado_a_tab3.setHorizontalHeaderLabels(
            ["Optativa", "Docente", "Semestres", "Cupo", "Día", "Inicio", "Fin", "Salón"]
        )
        self.optativas_listado_a_tab3.setAlternatingRowColors(True)
        self.optativas_listado_a_tab3.setStyleSheet(
            "background-color: #d9dced; alternate-background-color: #e8eaf4;"
        )
        self.optativas_listado_a_tab3.horizontalHeader().setStyleSheet(
            "background-color: #bfc4e0; font-weight: bold; color: #0c1c8c;"
        )
        grid.addWidget(self.optativas_listado_a_tab3, 3, 1, 6, 1)
        self.btn_inscribir_a = QPushButton("Inscribir A")
        grid.addWidget(self.btn_inscribir_a, 9, 1)

        # Optativas B
        self.line_search_optativa_b = QLineEdit()
        self.line_search_optativa_b.setPlaceholderText("Buscar optativa B")
        grid.addWidget(self.line_search_optativa_b, 1, 2)
        grid.addWidget(QLabel("Optativas B"), 2, 2)
        self.optativas_listado_b_tab3 = QTableWidget()
        self.optativas_listado_b_tab3.setColumnCount(8)
        self.optativas_listado_b_tab3.setHorizontalHeaderLabels(
            ["Optativa", "Docente", "Semestres", "Cupo", "Día", "Inicio", "Fin", "Salón"]
        )
        self.optativas_listado_b_tab3.setAlternatingRowColors(True)
        self.optativas_listado_b_tab3.setStyleSheet(
            "background-color: #d9dced; alternate-background-color: #e8eaf4;"
        )
        self.optativas_listado_b_tab3.horizontalHeader().setStyleSheet(
            "background-color: #bfc4e0; font-weight: bold; color: #0c1c8c;"
        )
        grid.addWidget(self.optativas_listado_b_tab3, 3, 2, 6, 1)
        self.btn_inscribir_b = QPushButton("Inscribir B")
        grid.addWidget(self.btn_inscribir_b, 9, 2)

        # Tabla Inscritas
        grid.addWidget(QLabel("Inscritas"), 10, 1, 1, 2)
        self.table_inscritas_tab3 = QTableWidget()
        self.table_inscritas_tab3.setColumnCount(5)
        self.table_inscritas_tab3.setHorizontalHeaderLabels(
            ["Matrícula", "Optativa", "Día", "Horario", "Docente"]
        )
        self.table_inscritas_tab3.setAlternatingRowColors(True)
        self.table_inscritas_tab3.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table_inscritas_tab3.setStyleSheet(
            "background-color: #d9dced; alternate-background-color: #e8eaf4;"
        )
        self.table_inscritas_tab3.horizontalHeader().setStyleSheet(
            "background-color: #bfc4e0; font-weight: bold; color: #0c1c8c;"
        )
        grid.addWidget(self.table_inscritas_tab3, 11, 1, 3, 2)
        self.btn_quitar_inscrita = QPushButton("Quitar Inscrita")
        grid.addWidget(self.btn_quitar_inscrita, 14, 1, 1, 2)

    def _connect_signals(self):
        self.combo_inscritos_tab3.currentIndexChanged.connect(self.cargar_estudiantes_tab3)
        self.combo_semestre_tab3.currentTextChanged.connect(self.cargar_estudiantes_tab3)
        self.line_search_estudiante_tab3.textChanged.connect(self.cargar_estudiantes_tab3)
        self.line_search_optativa_a.textChanged.connect(self.filtrar_optativas_a_tab3)
        self.line_search_optativa_b.textChanged.connect(self.filtrar_optativas_b_tab3)
        self.chk_ya_curso_a.stateChanged.connect(self._on_checkbox_ya_curso_changed)
        self.chk_ya_curso_b.stateChanged.connect(self._on_checkbox_ya_curso_changed)
        self.table_estudiantes_tab3.itemSelectionChanged.connect(self._on_estudiante_tab3_changed)
        self.btn_inscribir_a.clicked.connect(self.inscribir_optativa_a)
        self.btn_inscribir_b.clicked.connect(self.inscribir_optativa_b)
        self.btn_quitar_inscrita.clicked.connect(self.quitar_inscrita)

    def cargar_estudiantes_tab3(self):
        self.table_estudiantes_tab3.setRowCount(0)
        all_students = self.db.run_query(
            "SELECT matricula, nombre, apellido_paterno, apellido_materno, semestre, estado FROM estudiantes WHERE estado='Activo' ORDER BY nombre, apellido_paterno, apellido_materno",
            fetch="all"
        )
        # map matrícula -> tipos inscritos
        tipos_map = {}
        for mat, *_ in all_students:
            rows = self.db.run_query(
                "SELECT o.tipo FROM inscripciones i JOIN optativas o ON i.optativa_id=o.id WHERE i.matricula=?",
                (mat,), fetch="all"
            )
            tipos_map[mat] = {r[0] for r in rows} if rows else set()

        row_idx = 0
        modo = self.combo_inscritos_tab3.currentText()
        sem_sel = self.combo_semestre_tab3.currentText()
        texto = self.line_search_estudiante_tab3.text().lower().strip()

        for mat, nom, ap, am, sem, est in all_students:
            if sem == "8°":
                continue
            nombre_comp = f"{nom} {ap} {am}"
            if sem_sel != "Todos" and sem != sem_sel:
                continue
            if texto and texto not in nombre_comp.lower():
                continue

            tipos = tipos_map.get(mat, set())
            yaA, yaB = self.ya_curso.get(mat, (False, False))
            llevaA = ("A" in tipos) or yaA
            llevaB = ("B" in tipos) or yaB

            if modo == "Inscritos" and not (llevaA and llevaB):
                continue
            if modo == "No inscritos" and (llevaA and llevaB):
                continue

            self.table_estudiantes_tab3.insertRow(row_idx)
            self.table_estudiantes_tab3.setItem(row_idx, 0, QTableWidgetItem(mat))
            self.table_estudiantes_tab3.setItem(row_idx, 1, QTableWidgetItem(nombre_comp))
            self.table_estudiantes_tab3.setItem(row_idx, 2, QTableWidgetItem(sem))
            self.table_estudiantes_tab3.setItem(row_idx, 3, QTableWidgetItem(est))
            row_idx += 1

        # recarga inscritas para la fila seleccionada
        self._reload_inscritas_tab3()

    def filtrar_optativas_a_tab3(self):
        texto = self.line_search_optativa_a.text().lower().strip()
        for i in range(self.optativas_listado_a_tab3.rowCount()):
            name = self.optativas_listado_a_tab3.item(i, 0).text().lower()
            self.optativas_listado_a_tab3.setRowHidden(i, texto and texto not in name)

    def filtrar_optativas_b_tab3(self):
        texto = self.line_search_optativa_b.text().lower().strip()
        for i in range(self.optativas_listado_b_tab3.rowCount()):
            name = self.optativas_listado_b_tab3.item(i, 0).text().lower()
            self.optativas_listado_b_tab3.setRowHidden(i, texto and texto not in name)

    def _reload_inscritas_tab3(self):
        self.table_inscritas_tab3.setRowCount(0)
        row = self.table_estudiantes_tab3.currentRow()
        if row < 0:
            return
        mat = self.table_estudiantes_tab3.item(row, 0).text()
        rows = self.db.run_query(
            """SELECT o.nombre, o.dia, o.inicio, o.fin,
                      d1.nombre, d1.apellido_paterno, d1.apellido_materno,
                      d2.nombre, d2.apellido_paterno, d2.apellido_materno
               FROM inscripciones i
               JOIN optativas o ON i.optativa_id=o.id
               JOIN docentes d1 ON o.rfc_docente=d1.rfc
               LEFT JOIN docentes d2 ON o.rfc_segundo_docente=d2.rfc
               WHERE i.matricula=?
               ORDER BY o.nombre""",
            (mat,), fetch="all"
        )
        for i, (opt, dia, hi, hf, d1n, d1p, d1m, d2n, d2p, d2m) in enumerate(rows):
            if d2n:
                docente = f"{d1n} {d1p} {d1m} & {d2n} {d2p} {d2m}"
            else:
                docente = f"{d1n} {d1p} {d1m}"
            self.table_inscritas_tab3.insertRow(i)
            self.table_inscritas_tab3.setItem(i, 0, QTableWidgetItem(mat))
            self.table_inscritas_tab3.setItem(i, 1, QTableWidgetItem(opt))
            self.table_inscritas_tab3.setItem(i, 2, QTableWidgetItem(dia))
            self.table_inscritas_tab3.setItem(i, 3, QTableWidgetItem(f"{hi}-{hf}"))
            self.table_inscritas_tab3.setItem(i, 4, QTableWidgetItem(docente))

    def _on_estudiante_tab3_changed(self):
        old = self._last_tab3_student_row
        if old >= 0:
            mat_old = self.table_estudiantes_tab3.item(old, 0).text()
            self.ya_curso[mat_old] = (
                self.chk_ya_curso_a.isChecked(),
                self.chk_ya_curso_b.isChecked()
            )
        new = self.table_estudiantes_tab3.currentRow()
        self._last_tab3_student_row = new

        # 1) recarga la lista de inscritas
        self._reload_inscritas_tab3()
        # 2) vuelve a poblar los listados de optativas disponibles
        self.cargar_optativas_a_tab3()
        self.cargar_optativas_b_tab3()
        # 3) aplica habilitado/deshabilitado por solapamientos
        self._control_optativas_a_b_habilitadas()

    def _on_checkbox_ya_curso_changed(self):
        row = self.table_estudiantes_tab3.currentRow()
        if row < 0:
            return
        mat = self.table_estudiantes_tab3.item(row, 0).text()
        self.ya_curso[mat] = (
            self.chk_ya_curso_a.isChecked(),
            self.chk_ya_curso_b.isChecked()
        )
        # recargar estudiante para forzar filtro
        self.cargar_estudiantes_tab3()
        # volver a seleccionar la misma fila
        for i in range(self.table_estudiantes_tab3.rowCount()):
            if self.table_estudiantes_tab3.item(i, 0).text() == mat:
                self.table_estudiantes_tab3.selectRow(i)
                break

    def _control_optativas_a_b_habilitadas(self):
        row = self.table_estudiantes_tab3.currentRow()
        if row < 0:
            return
        mat = self.table_estudiantes_tab3.item(row, 0).text()
        # inscripciones A/B actuales para chequear solapamientos
        insA = self.db.run_query(
            "SELECT o.dia, o.inicio, o.fin FROM inscripciones i JOIN optativas o ON i.optativa_id=o.id WHERE i.matricula=? AND o.tipo='A'",
            (mat,), fetch="all"
        )
        insB = self.db.run_query(
            "SELECT o.dia, o.inicio, o.fin FROM inscripciones i JOIN optativas o ON i.optativa_id=o.id WHERE i.matricula=? AND o.tipo='B'",
            (mat,), fetch="all"
        )
        # para cada listado, deshabilitar filas en conflicto
        for table, other_ins in (
            (self.optativas_listado_a_tab3, insB),
            (self.optativas_listado_b_tab3, insA)
        ):
            for i in range(table.rowCount()):
                day = table.item(i, 4).text()
                hi = table.item(i, 5).text()
                hf = table.item(i, 6).text()
                conflict = any(
                    d2 == day and self.times_overlap(hi, hf, hi2, hf2)
                    for d2, hi2, hf2 in other_ins
                )
                for col in range(table.columnCount()):
                    item = table.item(i, col)
                    if item:
                        flags = item.flags()
                        if conflict:
                            item.setFlags(flags & ~Qt.ItemFlag.ItemIsEnabled)
                        else:
                            item.setFlags(flags | Qt.ItemFlag.ItemIsEnabled)

    def cargar_optativas_a_tab3(self):
        self.optativas_listado_a_tab3.setRowCount(0)
        row = self.table_estudiantes_tab3.currentRow()
        if row < 0:
            return
        sem_alumno = self.table_estudiantes_tab3.item(row, 2).text()
        res = self.db.run_query(
            """SELECT o.id, o.nombre,
                      d1.nombre, d1.apellido_paterno, d1.apellido_materno,
                      d2.nombre, d2.apellido_paterno, d2.apellido_materno,
                      o.semestres, o.cupo, o.dia, o.inicio, o.fin, o.salon
               FROM optativas o
               JOIN docentes d1 ON o.rfc_docente=d1.rfc
               LEFT JOIN docentes d2 ON o.rfc_segundo_docente=d2.rfc
               WHERE o.tipo='A'
               ORDER BY o.nombre""",
            fetch="all"
        )
        filas = []
        for (opt_id, nombre, d1n, d1p, d1m, d2n, d2p, d2m, sems, cupo, dia, hi, hf, sal) in res:
            if sem_alumno not in (sems or ""):
                continue
            count = self.db.run_query(
                "SELECT COUNT(*) FROM inscripciones WHERE optativa_id=?", (opt_id,), fetch="one"
            )[0]
            if count < cupo:
                docente = f"{d1n} {d1p} {d1m}" + (f" & {d2n} {d2p} {d2m}" if d2n else "")
                filas.append((opt_id, nombre, docente, sems, cupo, count, dia, hi, hf, sal))
        for i, (_, nombre, docente, sems, cupo, count, dia, hi, hf, sal) in enumerate(filas):
            disp = cupo - count
            self.optativas_listado_a_tab3.insertRow(i)
            self.optativas_listado_a_tab3.setItem(i, 0, QTableWidgetItem(nombre))
            self.optativas_listado_a_tab3.setItem(i, 1, QTableWidgetItem(docente))
            self.optativas_listado_a_tab3.setItem(i, 2, QTableWidgetItem(sems))
            self.optativas_listado_a_tab3.setItem(i, 3, QTableWidgetItem(str(disp)))
            self.optativas_listado_a_tab3.setItem(i, 4, QTableWidgetItem(dia))
            self.optativas_listado_a_tab3.setItem(i, 5, QTableWidgetItem(hi))
            self.optativas_listado_a_tab3.setItem(i, 6, QTableWidgetItem(hf))
            self.optativas_listado_a_tab3.setItem(i, 7, QTableWidgetItem(sal))

    def cargar_optativas_b_tab3(self):
        self.optativas_listado_b_tab3.setRowCount(0)
        row = self.table_estudiantes_tab3.currentRow()
        if row < 0:
            return
        sem_alumno = self.table_estudiantes_tab3.item(row, 2).text()
        res = self.db.run_query(
            """SELECT o.id, o.nombre,
                      d1.nombre, d1.apellido_paterno, d1.apellido_materno,
                      d2.nombre, d2.apellido_paterno, d2.apellido_materno,
                      o.semestres, o.cupo, o.dia, o.inicio, o.fin, o.salon
               FROM optativas o
               JOIN docentes d1 ON o.rfc_docente=d1.rfc
               LEFT JOIN docentes d2 ON o.rfc_segundo_docente=d2.rfc
               WHERE o.tipo='B'
               ORDER BY o.nombre""",
            fetch="all"
        )
        filas = []
        for (opt_id, nombre, d1n, d1p, d1m, d2n, d2p, d2m, sems, cupo, dia, hi, hf, sal) in res:
            if sem_alumno not in (sems or ""):
                continue
            count = self.db.run_query(
                "SELECT COUNT(*) FROM inscripciones WHERE optativa_id=?", (opt_id,), fetch="one"
            )[0]
            if count < cupo:
                docente = f"{d1n} {d1p} {d1m}" + (f" & {d2n} {d2p} {d2m}" if d2n else "")
                filas.append((opt_id, nombre, docente, sems, cupo, count, dia, hi, hf, sal))
        for i, (_, nombre, docente, sems, cupo, count, dia, hi, hf, sal) in enumerate(filas):
            disp = cupo - count
            self.optativas_listado_b_tab3.insertRow(i)
            self.optativas_listado_b_tab3.setItem(i, 0, QTableWidgetItem(nombre))
            self.optativas_listado_b_tab3.setItem(i, 1, QTableWidgetItem(docente))
            self.optativas_listado_b_tab3.setItem(i, 2, QTableWidgetItem(sems))
            self.optativas_listado_b_tab3.setItem(i, 3, QTableWidgetItem(str(disp)))
            self.optativas_listado_b_tab3.setItem(i, 4, QTableWidgetItem(dia))
            self.optativas_listado_b_tab3.setItem(i, 5, QTableWidgetItem(hi))
            self.optativas_listado_b_tab3.setItem(i, 6, QTableWidgetItem(hf))
            self.optativas_listado_b_tab3.setItem(i, 7, QTableWidgetItem(sal))

    def inscribir_optativa_a(self):
        est = self.table_estudiantes_tab3.currentRow()
        opt = self.optativas_listado_a_tab3.currentRow()
        if est < 0 or opt < 0:
            return
        mat = self.table_estudiantes_tab3.item(est, 0).text()
        nombre = self.optativas_listado_a_tab3.item(opt, 0).text()
        dia = self.optativas_listado_a_tab3.item(opt, 4).text()
        hi = self.optativas_listado_a_tab3.item(opt, 5).text()
        hf = self.optativas_listado_a_tab3.item(opt, 6).text()

        res = self.db.run_query(
            "SELECT id, cupo FROM optativas WHERE tipo='A' AND nombre=? AND dia=? AND inicio=? AND fin=?",
            (nombre, dia, hi, hf),
            fetch="one"
        )
        if not res:
            return
        oid, cupo = res
        count = self.db.run_query(
            "SELECT COUNT(*) FROM inscripciones WHERE optativa_id=?", (oid,), fetch="one"
        )[0]
        if count >= cupo:
            QMessageBox.warning(self.widget, "Advertencia", f"La optativa '{nombre}' ya alcanzó su cupo.")
            return

        # comprobar solapamiento con B
        others = self.db.run_query(
            "SELECT o.dia, o.inicio, o.fin, o.nombre FROM inscripciones i "
            "JOIN optativas o ON i.optativa_id=o.id "
            "WHERE i.matricula=? AND o.tipo='B'",
            (mat,), fetch="all"
        )
        for d2, hi2, hf2, n2 in others:
            if d2 == dia and self.times_overlap(hi, hf, hi2, hf2):
                QMessageBox.warning(self.widget, "Advertencia", f"Se superpone con '{n2}'.")
                return

        self.db.run_query("INSERT INTO inscripciones(matricula, optativa_id) VALUES(?, ?)", (mat, oid))
        self._reload_inscritas_tab3()
        self.cargar_optativas_a_tab3()
        self._control_optativas_a_b_habilitadas()

    def inscribir_optativa_b(self):
        est = self.table_estudiantes_tab3.currentRow()
        opt = self.optativas_listado_b_tab3.currentRow()
        if est < 0 or opt < 0:
            return
        mat = self.table_estudiantes_tab3.item(est, 0).text()
        nombre = self.optativas_listado_b_tab3.item(opt, 0).text()
        dia = self.optativas_listado_b_tab3.item(opt, 4).text()
        hi = self.optativas_listado_b_tab3.item(opt, 5).text()
        hf = self.optativas_listado_b_tab3.item(opt, 6).text()

        res = self.db.run_query(
            "SELECT id, cupo FROM optativas WHERE tipo='B' AND nombre=? AND dia=? AND inicio=? AND fin=?",
            (nombre, dia, hi, hf),
            fetch="one"
        )
        if not res:
            return
        oid, cupo = res
        count = self.db.run_query(
            "SELECT COUNT(*) FROM inscripciones WHERE optativa_id=?", (oid,), fetch="one"
        )[0]
        if count >= cupo:
            QMessageBox.warning(self.widget, "Advertencia", f"La optativa '{nombre}' ya alcanzó su cupo.")
            return

        # comprobar solapamiento con A
        others = self.db.run_query(
            "SELECT o.dia, o.inicio, o.fin, o.nombre FROM inscripciones i "
            "JOIN optativas o ON i.optativa_id=o.id "
            "WHERE i.matricula=? AND o.tipo='A'",
            (mat,), fetch="all"
        )
        for d2, hi2, hf2, n2 in others:
            if d2 == dia and self.times_overlap(hi, hf, hi2, hf2):
                QMessageBox.warning(self.widget, "Advertencia", f"Se superpone con '{n2}'.")
                return

        self.db.run_query("INSERT INTO inscripciones(matricula, optativa_id) VALUES(?, ?)", (mat, oid))
        self._reload_inscritas_tab3()
        self.cargar_optativas_b_tab3()
        self._control_optativas_a_b_habilitadas()

    def quitar_inscrita(self):
        fila = self.table_inscritas_tab3.currentRow()
        if fila < 0:
            return
        mat = self.table_inscritas_tab3.item(fila, 0).text()
        nombre = self.table_inscritas_tab3.item(fila, 1).text()
        dia = self.table_inscritas_tab3.item(fila, 2).text()
        horario = self.table_inscritas_tab3.item(fila, 3).text().split("-")
        if len(horario) != 2:
            return
        hi, hf = horario

        res = self.db.run_query(
            "SELECT id FROM optativas WHERE nombre=? AND dia=? AND inicio=? AND fin=?",
            (nombre, dia, hi, hf),
            fetch="one"
        )
        if not res:
            return
        oid = res[0]

        self.db.run_query(
            "DELETE FROM inscripciones WHERE matricula=? AND optativa_id=?", (mat, oid)
        )
        self.table_inscritas_tab3.removeRow(fila)
        self.cargar_optativas_a_tab3()
        self.cargar_optativas_b_tab3()
        self._control_optativas_a_b_habilitadas()

    def times_overlap(self, start1, end1, start2, end2):
        t1_start = QTime.fromString(start1, "HH:mm")
        t1_end = QTime.fromString(end1, "HH:mm")
        t2_start = QTime.fromString(start2, "HH:mm")
        t2_end = QTime.fromString(end2, "HH:mm")
        return t1_start < t2_end and t2_start < t1_end

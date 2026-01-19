# proyecto/tabs/tab_inscripciones.py

from PySide6.QtCore import Qt, QTime, Signal, QObject
from PySide6.QtWidgets import (
    QWidget, QComboBox, QLineEdit, QLabel,
    QTableWidget, QPushButton, QCheckBox, QHeaderView,
    QMessageBox, QTableWidgetItem
)
from PySide6.QtGui import QFont


class TabInscripciones(QObject):
    inscripciones_changed = Signal()

    def __init__(self, db):
        super().__init__()
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
            self.table_estudiantes_tab3.setCurrentCell(0, 0)
            self._on_estudiante_tab3_changed()

    # ---------------------------
    #   UI helpers (mac/win)
    # ---------------------------
    def _apply_table_theme(self, table: QTableWidget):
        """
        Tema QSS consistente (evita depender de palette(), que en macOS se comporta distinto).
        """
        table.setStyleSheet("""
            QTableWidget {
                background-color: #d9dced;
                alternate-background-color: #e8eaf4;
                gridline-color: #bfc4e0;

                /* fallback selection (algunos estilos la usan) */
                selection-background-color: white;
                selection-color: rgb(12,28,140);
            }

            /* Selección cuando está activo */
            QTableWidget::item:selected:active {
                background: white;
                color: rgb(12,28,140);
            }

            /* Selección cuando NO está activo (macOS suele cambiarlo) */
            QTableWidget::item:selected:!active {
                background: white;
                color: rgb(12,28,140);
            }

            /* QTableWidget sin “halo”/outline */
            QTableWidget:focus {
                outline: none;
            }

            QHeaderView::section {
                background-color: #bfc4e0;
                font-weight: 700;
                color: #0c1c8c;
                padding: 6px;
                border: 0px;
                border-bottom: 1px solid #aab0d4;
            }

            QTableCornerButton::section {
                background-color: #bfc4e0;
                border: 0px;
            }
        """)

        # Métricas consistentes (mac suele verse diferente si no fijas alturas)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setDefaultSectionSize(26)  # alto de fila
        table.horizontalHeader().setFixedHeight(32)       # alto header
        table.verticalHeader().setVisible(False)          # look más parecido a Windows (opcional)
        table.setWordWrap(False)
        table.setTextElideMode(Qt.TextElideMode.ElideRight)

        # Selección por filas
        from PySide6.QtWidgets import QAbstractItemView
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)

    def _setup_ui(self):
        # widget contenedor principal
        self.widget.setFixedSize(1360, 760)  # tamaño total de la pestaña

        # Un pequeño QSS general para quitar outlines de foco en mac
        self.widget.setStyleSheet("""
            QLineEdit:focus, QComboBox:focus, QPushButton:focus, QCheckBox:focus {
                outline: none;
            }
        """)

        # — Controles de filtro —
        self.combo_inscritos_tab3 = QComboBox(self.widget)
        self.combo_inscritos_tab3.setGeometry(10, 10, 180, 25)
        self.combo_inscritos_tab3.addItems(["No inscritos", "Parcial", "Inscritos"])

        self.combo_semestre_tab3 = QComboBox(self.widget)
        self.combo_semestre_tab3.setGeometry(200, 10, 200, 25)
        self.combo_semestre_tab3.addItems(["Todos", "1°", "2°", "3°", "4°", "5°", "6°", "7°"])

        self.line_search_estudiante_tab3 = QLineEdit(self.widget)
        self.line_search_estudiante_tab3.setPlaceholderText("Buscar estudiante")
        self.line_search_estudiante_tab3.setGeometry(10, 45, 390, 25)

        # — Tabla Estudiantes —
        self.table_estudiantes_tab3 = QTableWidget(self.widget)
        self.table_estudiantes_tab3.setGeometry(10, 105, 400, 390)

        # eran 3 columnas, pero luego escribías 4 (estado)
        self.table_estudiantes_tab3.setColumnCount(4)
        self.table_estudiantes_tab3.setHorizontalHeaderLabels(
            ["Matrícula", "Nombre", "Semestre", "Estado"]
        )

        hdr = self.table_estudiantes_tab3.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table_estudiantes_tab3.setColumnWidth(1, 200)
        # Ocultar columna "Estado" (col = 3)
        self.table_estudiantes_tab3.setColumnHidden(3, True)

        # (Opcional) ya que no se verá, puedes hacer que "Nombre" estire
        hdr = self.table_estudiantes_tab3.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self._apply_table_theme(self.table_estudiantes_tab3)

        # — Checkboxes Ya cursó —
        self.chk_ya_curso_a = QCheckBox("Ya cursó Optativa A", self.widget)
        self.chk_ya_curso_a.setGeometry(715, 415, 160, 25)

        self.chk_ya_curso_b = QCheckBox("Ya cursó Optativa B", self.widget)
        self.chk_ya_curso_b.setGeometry(1145, 415, 160, 25)

        # — Optativas A —
        self.line_search_optativa_a = QLineEdit(self.widget)
        self.line_search_optativa_a.setPlaceholderText("Buscar asignatura A")
        self.line_search_optativa_a.setGeometry(430, 70, 410, 25)

        lbl_a = QLabel("Asignaturas A", self.widget)
        lbl_a.setGeometry(430, 25, 250, 40)
        lbl_a.setAlignment(Qt.AlignmentFlag.AlignLeft)
        # Evita fijar familia no instalada en mac; usa la fuente del sistema y solo ajusta tamaño/peso
        fa = lbl_a.font()
        fa.setPointSize(20)
        fa.setWeight(QFont.Weight.Bold)
        lbl_a.setFont(fa)
        lbl_a.setStyleSheet("color: rgb(12, 28, 140);")

        self.optativas_listado_a_tab3 = QTableWidget(self.widget)
        self.optativas_listado_a_tab3.setGeometry(430, 105, 410, 300)
        self.optativas_listado_a_tab3.setColumnCount(8)
        self.optativas_listado_a_tab3.setHorizontalHeaderLabels(
            ["Optativa", "Docente", "Semestres", "Cupo", "Día", "Inicio", "Fin", "Salón"]
        )
        self._apply_table_theme(self.optativas_listado_a_tab3)

        self.btn_inscribir_a = QPushButton("Inscribir A", self.widget)
        self.btn_inscribir_a.setGeometry(430, 415, 100, 30)

        # — Optativas B —
        self.line_search_optativa_b = QLineEdit(self.widget)
        self.line_search_optativa_b.setPlaceholderText("Buscar asignatura B")
        self.line_search_optativa_b.setGeometry(860, 70, 410, 25)

        lbl_b = QLabel("Asignaturas B", self.widget)
        lbl_b.setGeometry(860, 25, 250, 40)
        lbl_b.setAlignment(Qt.AlignmentFlag.AlignLeft)
        fb = lbl_b.font()
        fb.setPointSize(20)
        fb.setWeight(QFont.Weight.Bold)
        lbl_b.setFont(fb)
        lbl_b.setStyleSheet("color: rgb(12, 28, 140);")

        self.optativas_listado_b_tab3 = QTableWidget(self.widget)
        self.optativas_listado_b_tab3.setGeometry(860, 105, 410, 300)
        self.optativas_listado_b_tab3.setColumnCount(8)
        self.optativas_listado_b_tab3.setHorizontalHeaderLabels(
            ["Optativa", "Docente", "Semestres", "Cupo", "Día", "Inicio", "Fin", "Salón"]
        )
        self._apply_table_theme(self.optativas_listado_b_tab3)

        self.btn_inscribir_b = QPushButton("Inscribir B", self.widget)
        self.btn_inscribir_b.setGeometry(860, 415, 100, 30)

        # — Tabla Inscritas —
        lbl_ins = QLabel("Inscritas", self.widget)
        lbl_ins.setGeometry(10, 510, 100, 20)
        lbl_ins.setAlignment(Qt.AlignmentFlag.AlignLeft)
        fi = lbl_ins.font()
        fi.setPointSize(12)
        fi.setWeight(QFont.Weight.Bold)
        lbl_ins.setFont(fi)
        lbl_ins.setStyleSheet("color: rgb(12, 28, 140);")

        self.table_inscritas_tab3 = QTableWidget(self.widget)
        self.table_inscritas_tab3.setGeometry(10, 540, 820, 100)
        self.table_inscritas_tab3.setColumnCount(5)
        self.table_inscritas_tab3.setHorizontalHeaderLabels(
            ["Matrícula", "Asignatura", "Día", "Horario", "Docente"]
        )
        self._apply_table_theme(self.table_inscritas_tab3)
        self.table_inscritas_tab3.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.btn_quitar_inscrita = QPushButton("Quitar Inscrita", self.widget)
        self.btn_quitar_inscrita.setGeometry(850, 580, 120, 30)

    def _connect_signals(self):
        self.combo_inscritos_tab3.currentIndexChanged.connect(self.cargar_estudiantes_tab3)
        self.combo_semestre_tab3.currentTextChanged.connect(self.cargar_estudiantes_tab3)
        self.line_search_estudiante_tab3.textChanged.connect(self.cargar_estudiantes_tab3)

        self.line_search_optativa_a.textChanged.connect(self.filtrar_optativas_a_tab3)
        self.line_search_optativa_b.textChanged.connect(self.filtrar_optativas_b_tab3)

        self.chk_ya_curso_a.stateChanged.connect(self._on_checkbox_ya_curso_changed)
        self.chk_ya_curso_b.stateChanged.connect(self._on_checkbox_ya_curso_changed)

        # Señal original
        self.table_estudiantes_tab3.itemSelectionChanged.connect(self._on_estudiante_tab3_changed)

        # FIX macOS: forzar disparo al click / cambio de celda current
        self.table_estudiantes_tab3.currentCellChanged.connect(
            lambda _cr, _cc, _pr, _pc: self._on_estudiante_tab3_changed()
        )
        self.table_estudiantes_tab3.cellClicked.connect(
            lambda _r, _c: self._on_estudiante_tab3_changed()
        )

        self.btn_inscribir_a.clicked.connect(self.inscribir_optativa_a)
        self.btn_inscribir_b.clicked.connect(self.inscribir_optativa_b)
        self.btn_quitar_inscrita.clicked.connect(self.quitar_inscrita)

    def cargar_estudiantes_tab3(self):
        self.table_estudiantes_tab3.setRowCount(0)

        # Estados permitidos para inscribir (excluye bajas)
        estados_ok = ("REGULAR", "RECURSAMIENTO", "RECURSAMIENTO PARALELO", "MOVILIDAD PARCIAL", "MOVILIDAD")
        placeholders = ",".join(["?"] * len(estados_ok))

        all_students = self.db.run_query(
            f"SELECT matricula, nombre, apellido_paterno, apellido_materno, semestre, estado "
            f"FROM estudiantes WHERE UPPER(estado) IN ({placeholders}) "
            f"ORDER BY nombre, apellido_paterno, apellido_materno",
            tuple(estados_ok),
            fetch="all"
        )

        # map matrícula -> tipos inscritos
        tipos_map = {}
        for mat, *_ in all_students or []:
            rows = self.db.run_query(
                "SELECT o.tipo FROM inscripciones i JOIN optativas o ON i.optativa_id=o.id WHERE i.matricula=?",
                (mat,),
                fetch="all"
            )
            tipos_map[mat] = {r[0] for r in rows} if rows else set()

        row_idx = 0
        modo = self.combo_inscritos_tab3.currentText()
        sem_sel = self.combo_semestre_tab3.currentText()
        texto = self.line_search_estudiante_tab3.text().lower().strip()

        for mat, nom, ap, am, sem, est in all_students or []:
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

            if modo == "Inscritos":
                if not (llevaA and llevaB):
                    continue
            elif modo == "No inscritos":
                if (llevaA or llevaB):
                    continue
            elif modo == "Parcial":
                if not ((llevaA and not llevaB) or (llevaB and not llevaA)):
                    continue

            self.table_estudiantes_tab3.insertRow(row_idx)
            self.table_estudiantes_tab3.setItem(row_idx, 0, QTableWidgetItem(mat))
            self.table_estudiantes_tab3.setItem(row_idx, 1, QTableWidgetItem(nombre_comp))
            self.table_estudiantes_tab3.setItem(row_idx, 2, QTableWidgetItem(sem))
            self.table_estudiantes_tab3.setItem(row_idx, 3, QTableWidgetItem(est))
            row_idx += 1

        # Si no hay filas, limpia dependientes y listo
        if self.table_estudiantes_tab3.rowCount() == 0:
            self.table_inscritas_tab3.setRowCount(0)
            self.optativas_listado_a_tab3.setRowCount(0)
            self.optativas_listado_b_tab3.setRowCount(0)
            return

        # FIX macOS: asegurar selección + current cell para que currentRow() no sea -1
        if self.table_estudiantes_tab3.currentRow() < 0:
            self.table_estudiantes_tab3.selectRow(0)
            self.table_estudiantes_tab3.setCurrentCell(0, 0)

        # Forzar recarga dependiente (inscritas y optativas)
        self._on_estudiante_tab3_changed()

    def filtrar_optativas_a_tab3(self):
        texto = self.line_search_optativa_a.text().lower().strip()
        for i in range(self.optativas_listado_a_tab3.rowCount()):
            item = self.optativas_listado_a_tab3.item(i, 0)
            name = item.text().lower() if item else ""
            hide = bool(texto) and (texto not in name)
            self.optativas_listado_a_tab3.setRowHidden(i, hide)

    def filtrar_optativas_b_tab3(self):
        texto = self.line_search_optativa_b.text().lower().strip()
        for i in range(self.optativas_listado_b_tab3.rowCount()):
            item = self.optativas_listado_b_tab3.item(i, 0)
            name = item.text().lower() if item else ""
            hide = bool(texto) and (texto not in name)
            self.optativas_listado_b_tab3.setRowHidden(i, hide)

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
            docente = f"{d1n} {d1p} {d1m}" + (f" & {d2n} {d2p} {d2m}" if d2n else "")
            self.table_inscritas_tab3.insertRow(i)
            self.table_inscritas_tab3.setItem(i, 0, QTableWidgetItem(mat))
            self.table_inscritas_tab3.setItem(i, 1, QTableWidgetItem(opt))
            self.table_inscritas_tab3.setItem(i, 2, QTableWidgetItem(dia))
            self.table_inscritas_tab3.setItem(i, 3, QTableWidgetItem(f"{hi}-{hf}"))
            self.table_inscritas_tab3.setItem(i, 4, QTableWidgetItem(docente))

    def _on_estudiante_tab3_changed(self):
        """
        Se ejecuta al cambiar la fila seleccionada en la tabla de estudiantes.
        Guarda el estado de 'Ya cursó A/B' del estudiante anterior y restablece
        los checkboxes para el nuevo estudiante.
        """
        # Asegura que haya fila válida (macOS: puede quedar currentRow=-1 tras repoblar)
        new = self.table_estudiantes_tab3.currentRow()
        if new < 0 and self.table_estudiantes_tab3.rowCount() > 0:
            self.table_estudiantes_tab3.selectRow(0)
            self.table_estudiantes_tab3.setCurrentCell(0, 0)
            new = 0
        if new < 0:
            # no hay estudiantes
            self.table_inscritas_tab3.setRowCount(0)
            self.optativas_listado_a_tab3.setRowCount(0)
            self.optativas_listado_b_tab3.setRowCount(0)
            return

        old = self._last_tab3_student_row

        # 1) Guardar el estado de A/B del estudiante anterior
        if old >= 0 and old < self.table_estudiantes_tab3.rowCount():
            item_old = self.table_estudiantes_tab3.item(old, 0)
            if item_old:
                mat_old = item_old.text()
                self.ya_curso[mat_old] = (
                    self.chk_ya_curso_a.isChecked(),
                    self.chk_ya_curso_b.isChecked()
                )

        # 2) Actualizar índice de la nueva fila
        self._last_tab3_student_row = new

        # 3) Recuperar y aplicar el estado de checkboxes para el nuevo estudiante
        item_new = self.table_estudiantes_tab3.item(new, 0)
        if item_new:
            mat_new = item_new.text()
            yaA, yaB = self.ya_curso.get(mat_new, (False, False))

            self.chk_ya_curso_a.blockSignals(True)
            self.chk_ya_curso_b.blockSignals(True)
            self.chk_ya_curso_a.setChecked(yaA)
            self.chk_ya_curso_b.setChecked(yaB)
            self.chk_ya_curso_a.blockSignals(False)
            self.chk_ya_curso_b.blockSignals(False)

        # 4) Recargar datos dependientes de la selección
        self._reload_inscritas_tab3()
        self.cargar_optativas_a_tab3()
        self.cargar_optativas_b_tab3()
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
                self.table_estudiantes_tab3.setCurrentCell(i, 0)
                break

    def _control_optativas_a_b_habilitadas(self):
        row = self.table_estudiantes_tab3.currentRow()
        if row < 0:
            return
        mat = self.table_estudiantes_tab3.item(row, 0).text()
        # inscripciones A/B actuales para chequear solapamientos
        insA = self.db.run_query(
            "SELECT o.dia, o.inicio, o.fin FROM inscripciones i "
            "JOIN optativas o ON i.optativa_id=o.id WHERE i.matricula=? AND o.tipo='A'",
            (mat,), fetch="all"
        )
        insB = self.db.run_query(
            "SELECT o.dia, o.inicio, o.fin FROM inscripciones i "
            "JOIN optativas o ON i.optativa_id=o.id WHERE i.matricula=? AND o.tipo='B'",
            (mat,), fetch="all"
        )
        # para cada listado, deshabilitar filas en conflicto
        for table, other_ins in (
            (self.optativas_listado_a_tab3, insB),
            (self.optativas_listado_b_tab3, insA)
        ):
            for i in range(table.rowCount()):
                day_item = table.item(i, 4)
                hi_item = table.item(i, 5)
                hf_item = table.item(i, 6)
                if not (day_item and hi_item and hf_item):
                    continue

                day = day_item.text()
                hi = hi_item.text()
                hf = hf_item.text()

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

        matricula = self.table_estudiantes_tab3.item(row, 0).text()
        sem_alumno = self.table_estudiantes_tab3.item(row, 2).text()

        # Inscripciones B actuales (tipo 'B')
        insB = self.db.run_query(
            "SELECT o.dia, o.inicio, o.fin FROM inscripciones i "
            "JOIN optativas o ON i.optativa_id=o.id "
            "WHERE i.matricula=? AND o.tipo='B'",
            (matricula,), fetch="all"
        )
        # Inscripciones A actuales (tipo 'A')
        insA_cur = self.db.run_query(
            "SELECT o.dia, o.inicio, o.fin FROM inscripciones i "
            "JOIN optativas o ON i.optativa_id=o.id "
            "WHERE i.matricula=? AND o.tipo='A'",
            (matricula,), fetch="all"
        )

        # Todas las optativas A
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
        for (opt_id, nombre, d1n, d1p, d1m, d2n, d2p, d2m,
             sems, cupo, dia, hi, hf, sal) in res:

            # 1) semestre
            if sem_alumno not in (sems or ""):
                continue

            # 2) cupo
            count = self.db.run_query(
                "SELECT COUNT(*) FROM inscripciones WHERE optativa_id=?", (opt_id,), fetch="one"
            )[0]
            if count >= cupo:
                continue

            # 3) solapamiento con B
            dia_norm = dia.strip().lower()
            if any(d2.strip().lower() == dia_norm and self.times_overlap(hi, hf, hi2, hf2)
                   for d2, hi2, hf2 in insB):
                continue

            # 4) solapamiento con otras A ya inscritas
            if any(d2.strip().lower() == dia_norm and self.times_overlap(hi, hf, hi2, hf2)
                   for d2, hi2, hf2 in insA_cur):
                continue

            docente = f"{d1n} {d1p} {d1m}"
            if d2n:
                docente += f" & {d2n} {d2p} {d2m}"

            filas.append((opt_id, nombre, docente, sems, cupo, count, dia, hi, hf, sal))

        # poblar tabla A
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

        matricula = self.table_estudiantes_tab3.item(row, 0).text()
        sem_alumno = self.table_estudiantes_tab3.item(row, 2).text()

        # Inscripciones A actuales (tipo 'A')
        insA = self.db.run_query(
            "SELECT o.dia, o.inicio, o.fin FROM inscripciones i "
            "JOIN optativas o ON i.optativa_id=o.id "
            "WHERE i.matricula=? AND o.tipo='A'",
            (matricula,), fetch="all"
        )
        # Inscripciones B actuales (tipo 'B')
        insB_cur = self.db.run_query(
            "SELECT o.dia, o.inicio, o.fin FROM inscripciones i "
            "JOIN optativas o ON i.optativa_id=o.id "
            "WHERE i.matricula=? AND o.tipo='B'",
            (matricula,), fetch="all"
        )

        # Todas las optativas B
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
        for (opt_id, nombre, d1n, d1p, d1m, d2n, d2p, d2m,
             sems, cupo, dia, hi, hf, sal) in res:

            # 1) semestre
            if sem_alumno not in (sems or ""):
                continue

            # 2) cupo
            count = self.db.run_query(
                "SELECT COUNT(*) FROM inscripciones WHERE optativa_id=?", (opt_id,), fetch="one"
            )[0]
            if count >= cupo:
                continue

            # 3) solapamiento con A
            dia_norm = dia.strip().lower()
            if any(d2.strip().lower() == dia_norm and self.times_overlap(hi, hf, hi2, hf2)
                   for d2, hi2, hf2 in insA):
                continue

            # 4) solapamiento con otras B ya inscritas
            if any(d2.strip().lower() == dia_norm and self.times_overlap(hi, hf, hi2, hf2)
                   for d2, hi2, hf2 in insB_cur):
                continue

            docente = f"{d1n} {d1p} {d1m}"
            if d2n:
                docente += f" & {d2n} {d2p} {d2m}"

            filas.append((opt_id, nombre, docente, sems, cupo, count, dia, hi, hf, sal))

        # poblar tabla B
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
            QMessageBox.warning(self.widget, "Advertencia", f"La asignatura '{nombre}' ya alcanzó su cupo.")
            return

        # límite por estado (1 A normal, 2 A si recursamiento)
        estado_row = self.db.run_query("SELECT UPPER(estado) FROM estudiantes WHERE matricula=?", (mat,), fetch="one")
        estado = (estado_row[0] if estado_row else "").upper()
        max_por_tipo = 2 if estado in ("RECURSAMIENTO", "RECURSAMIENTO PARALELO") else 1
        actuales = self.db.run_query(
            "SELECT COUNT(*) FROM inscripciones i JOIN optativas o ON i.optativa_id=o.id "
            "WHERE i.matricula=? AND o.tipo='A'", (mat,), fetch="one"
        )[0]
        if actuales >= max_por_tipo:
            QMessageBox.warning(
                self.widget, "Advertencia",
                f"Este estudiante ya tiene {actuales} Asignatura(s) A permitidas para su condición."
            )
            return

        # solapamiento con B
        others = self.db.run_query(
            "SELECT o.dia, o.inicio, o.fin, o.nombre FROM inscripciones i "
            "JOIN optativas o ON i.optativa_id=o.id "
            "WHERE i.matricula=? AND o.tipo='B'",
            (mat,), fetch="all"
        )
        for d2, hi2, hf2, n2 in others:
            if d2.strip().lower() == dia.strip().lower() and self.times_overlap(hi, hf, hi2, hf2):
                QMessageBox.warning(self.widget, "Advertencia", f"Se superpone con '{n2}'.")
                return

        self.db.run_query("INSERT INTO inscripciones(matricula, optativa_id) VALUES(?, ?)", (mat, oid))

        self._reload_inscritas_tab3()
        self.cargar_optativas_a_tab3()
        self.cargar_optativas_b_tab3()
        self._control_optativas_a_b_habilitadas()
        self.inscripciones_changed.emit()

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
            QMessageBox.warning(self.widget, "Advertencia", f"La asignatura '{nombre}' ya alcanzó su cupo.")
            return

        estado_row = self.db.run_query("SELECT UPPER(estado) FROM estudiantes WHERE matricula=?", (mat,), fetch="one")
        estado = (estado_row[0] if estado_row else "").upper()
        max_por_tipo = 2 if estado in ("RECURSAMIENTO", "RECURSAMIENTO PARALELO") else 1
        actuales = self.db.run_query(
            "SELECT COUNT(*) FROM inscripciones i JOIN optativas o ON i.optativa_id=o.id "
            "WHERE i.matricula=? AND o.tipo='B'", (mat,), fetch="one"
        )[0]
        if actuales >= max_por_tipo:
            QMessageBox.warning(
                self.widget, "Advertencia",
                f"Este estudiante ya tiene {actuales} Asignatura(s) B permitidas para su condición."
            )
            return

        # solapamiento con A
        others = self.db.run_query(
            "SELECT o.dia, o.inicio, o.fin, o.nombre FROM inscripciones i "
            "JOIN optativas o ON i.optativa_id=o.id "
            "WHERE i.matricula=? AND o.tipo='A'",
            (mat,), fetch="all"
        )
        for d2, hi2, hf2, n2 in others:
            if d2.strip().lower() == dia.strip().lower() and self.times_overlap(hi, hf, hi2, hf2):
                QMessageBox.warning(self.widget, "Advertencia", f"Se superpone con '{n2}'.")
                return

        self.db.run_query("INSERT INTO inscripciones(matricula, optativa_id) VALUES(?, ?)", (mat, oid))

        self._reload_inscritas_tab3()
        self.cargar_optativas_b_tab3()
        self.cargar_optativas_a_tab3()
        self._control_optativas_a_b_habilitadas()
        self.inscripciones_changed.emit()

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
        self.inscripciones_changed.emit()

    def times_overlap(self, start1, end1, start2, end2):
        t1_start = QTime.fromString(start1, "HH:mm")
        t1_end = QTime.fromString(end1, "HH:mm")
        t2_start = QTime.fromString(start2, "HH:mm")
        t2_end = QTime.fromString(end2, "HH:mm")
        return t1_start < t2_end and t2_start < t1_end

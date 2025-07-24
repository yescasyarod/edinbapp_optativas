#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QFileDialog
)
import csv
from utils import obtener_ruta


class TabEstudiantes:
    def __init__(self, db, is_admin: bool = False):
        self.db = db
        self.is_admin = is_admin
        self.widget = QWidget()
        self.editando_estudiante = False
        self.fila_editando_estudiante = -1

        self._setup_ui()
        self._connect_signals()

        # No admin: ajustes iniciales
        if not self.is_admin:
            self.line_matricula.setReadOnly(True)
            self.combo_semestre_est.setEnabled(True)
            self.btn_quitar_estudiante.hide()
            self.btn_editar_estudiante.setGeometry(1170, 460, 151, 31)

    # ---------------------- UI ----------------------
    def _setup_ui(self):
        self._tab = self.widget
        self._tab.setStyleSheet("background-color: white;")

        # Label ESTUDIANTES
        self.label_estudiantes = QLabel("ESTUDIANTES", self._tab)
        self.label_estudiantes.setGeometry(40, 40, 231, 25)
        self.label_estudiantes.setFont(QFont("Noto Sans", 20, QFont.Weight.Bold))
        self.label_estudiantes.setStyleSheet("color: rgb(12, 28, 140);")

        # Combo filtro semestre
        self.combo_filtrar_estudiantes = QComboBox(self._tab)
        self.combo_filtrar_estudiantes.setGeometry(290, 36, 201, 32)
        self.combo_filtrar_estudiantes.setFont(QFont("Noto Sans", 8, QFont.Weight.Bold))
        self.combo_filtrar_estudiantes.setStyleSheet(
            "border: 1.5px solid #0c1c8c; border-radius: 5px; "
            "color: rgb(12, 28, 140); background-color: white;"
        )
        self.combo_filtrar_estudiantes.addItems(
            ["Todos", "1°", "2°", "3°", "4°", "5°", "6°", "7°"]
        )

        # Línea búsqueda
        self.line_buscar_estudiante = QLineEdit(self._tab)
        self.line_buscar_estudiante.setGeometry(710, 36, 481, 31)
        self.line_buscar_estudiante.setFont(QFont("Noto Sans", 8, QFont.Weight.Bold))
        self.line_buscar_estudiante.setStyleSheet(
            "border: 1.5px solid #0c1c8c; border-radius: 5px; "
            "color: rgb(12, 28, 140); background-color: white;"
        )
        self.line_buscar_estudiante.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.line_buscar_estudiante.setPlaceholderText("BUSCAR ESTUDIANTE")

        # Tabla estudiantes
        self.table_estudiantes = QTableWidget(self._tab)
        self.table_estudiantes.setGeometry(40, 90, 1281, 361)
        self.table_estudiantes.setColumnCount(4)
        self.table_estudiantes.setHorizontalHeaderLabels(
            ["Matrícula", "Nombre", "Semestre", "Condición"]
        )
        self.table_estudiantes.setAlternatingRowColors(True)
        self.table_estudiantes.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_estudiantes.horizontalHeader().setStretchLastSection(True)
        self.table_estudiantes.setColumnWidth(1, 400)
        self.table_estudiantes.setStyleSheet(
            "background-color: #d9dced; alternate-background-color: #e8eaf4;"
        )
        self.table_estudiantes.horizontalHeader().setStyleSheet(
            "background-color: #bfc4e0; font-weight: bold; color: #0c1c8c;"
        )

        # Botones EDITAR / QUITAR
        self.btn_editar_estudiante = QPushButton("EDITAR", self._tab)
        self.btn_editar_estudiante.setGeometry(1010, 460, 151, 31)
        self.btn_editar_estudiante.setFont(QFont("Noto Sans", 7, QFont.Weight.Bold))
        self.btn_editar_estudiante.setStyleSheet(
            "border:1.5px solid #0c1c8c; border-radius:12; "
            "color: rgb(12,28,140); background-color:white;"
        )

        self.btn_quitar_estudiante = QPushButton("QUITAR", self._tab)
        self.btn_quitar_estudiante.setGeometry(1170, 460, 151, 31)
        self.btn_quitar_estudiante.setFont(QFont("Noto Sans", 7, QFont.Weight.Bold))
        self.btn_quitar_estudiante.setStyleSheet(
            "border:1.5px solid #0c1c8c; border-radius:12; "
            "color: rgb(12,28,140); background-color:white;"
        )

        # Sección AGREGAR
        self.label_agregar_estudiante = QLabel("AGREGAR ESTUDIANTE", self._tab)
        self.label_agregar_estudiante.setGeometry(40, 500, 231, 25)
        self.label_agregar_estudiante.setFont(
            QFont("Noto Sans", 12, QFont.Weight.Bold)
        )
        self.label_agregar_estudiante.setStyleSheet("color: rgb(12,28,140);")

        self.line_nombre_est = QLineEdit(self._tab)
        self.line_nombre_est.setGeometry(40, 540, 251, 26)
        self.line_nombre_est.setFont(QFont("Noto Sans", 8, QFont.Weight.Bold))
        self.line_nombre_est.setStyleSheet(
            "QLineEdit {color: rgb(12,28,140); background:transparent; "
            "border:none; border-bottom:2px solid #0c1c8c;}"
            "QLineEdit:disabled {color:#7f7f7f; background:#f2f2f2; "
            "border:none; border-bottom:2px solid #b3b3b3;}"
        )
        self.line_nombre_est.setPlaceholderText("NOMBRE")

        self.line_apellido_pat_est = QLineEdit(self._tab)
        self.line_apellido_pat_est.setGeometry(330, 540, 231, 26)
        self.line_apellido_pat_est.setFont(QFont("Noto Sans", 8, QFont.Weight.Bold))
        self.line_apellido_pat_est.setStyleSheet(
            "QLineEdit {color: rgb(12,28,140); background:transparent; "
            "border:none; border-bottom:2px solid #0c1c8c;}"
            "QLineEdit:disabled {color:#7f7f7f; background:#f2f2f2; "
            "border:none; border-bottom:2px solid #b3b3b3;}"
        )
        self.line_apellido_pat_est.setPlaceholderText("APELLIDO PATERNO")

        self.line_apellido_mat_est = QLineEdit(self._tab)
        self.line_apellido_mat_est.setGeometry(40, 590, 251, 26)
        self.line_apellido_mat_est.setFont(QFont("Noto Sans", 8, QFont.Weight.Bold))
        self.line_apellido_mat_est.setStyleSheet(
            "QLineEdit {color: rgb(12,28,140); background:transparent; "
            "border:none; border-bottom:2px solid #0c1c8c;}"
            "QLineEdit:disabled {color:#7f7f7f; background:#f2f2f2; "
            "border:none; border-bottom:2px solid #b3b3b3;}"
        )
        self.line_apellido_mat_est.setPlaceholderText("APELLIDO MATERNO")

        # >>>>>>>>>>>> CAMBIO 1: stylesheet con :disabled
        self.line_matricula = QLineEdit(self._tab)
        self.line_matricula.setGeometry(330, 590, 191, 26)
        self.line_matricula.setFont(QFont("Noto Sans", 8, QFont.Weight.Bold))
        self.line_matricula.setStyleSheet(
            "QLineEdit {color: rgb(12,28,140); background:transparent; "
            "border:none; border-bottom:2px solid #0c1c8c;}"
            "QLineEdit:disabled {color:#7f7f7f; background:#f2f2f2; "
            "border:none; border-bottom:2px solid #b3b3b3;}"
        )
        self.line_matricula.setPlaceholderText("MATRÍCULA")
        # <<<<<<<<<<<<<<<

        # >>>>>>>>>>>> CAMBIO 1 bis: stylesheet con :disabled
        self.combo_semestre_est = QComboBox(self._tab)
        self.combo_semestre_est.setGeometry(600, 540, 201, 32)
        self.combo_semestre_est.setFont(QFont("Noto Sans", 8, QFont.Weight.Bold))
        self.combo_semestre_est.setStyleSheet(
            "QComboBox {border:1.5px solid #0c1c8c; border-radius:5px; "
            "color: rgb(96,102,140); background-color:white;}"
            "QComboBox:disabled {color:#7f7f7f; background:#f2f2f2; "
            "border:1.5px solid #b3b3b3;}"
        )
        self.combo_semestre_est.addItems(["1°", "2°", "3°", "4°", "5°", "6°", "7°"])
        # <<<<<<<<<<<<<<<

        self.combo_estado = QComboBox(self._tab)
        self.combo_estado.setGeometry(600, 590, 201, 32)
        self.combo_estado.setFont(QFont("Noto Sans", 8, QFont.Weight.Bold))
        self.combo_estado.setStyleSheet(
            "border:1.5px solid #0c1c8c; border-radius:5px; "
            "color: rgb(96,102,140); background-color:white;"
        )
        self.combo_estado.addItems(
            ["Activo", "Baja Temporal", "Irregular", "Baja Definitiva"]
        )

        # Botón AGREGAR
        self.btn_agregar_estudiante = QPushButton("AGREGAR", self._tab)
        self.btn_agregar_estudiante.setGeometry(40, 640, 151, 31)
        self.btn_agregar_estudiante.setFont(QFont("Noto Sans", 8, QFont.Weight.Bold))
        self.btn_agregar_estudiante.setStyleSheet(
            "border:1.5px solid #0c1c8c; border-radius:12; "
            "color: rgb(12,28,140); background-color:white;"
        )

        # Botón CARGAR CSV (solo admin)
        self.btn_cargar_estudiantes_csv = QPushButton(
            "CARGAR ESTUDIANTES (CSV)", self._tab
        )
        self.btn_cargar_estudiantes_csv.setGeometry(1050, 640, 271, 29)
        self.btn_cargar_estudiantes_csv.setFont(QFont("Noto Sans", 8, QFont.Weight.Bold))
        self.btn_cargar_estudiantes_csv.setStyleSheet(
            "border:1.5px solid #0c1c8c; border-radius:12; "
            "color: rgb(12,28,140); background-color:white;"
        )
        if not self.is_admin:
            self.btn_cargar_estudiantes_csv.hide()

    # ---------------------- Señales ----------------------
    def _connect_signals(self):
        self.line_buscar_estudiante.textChanged.connect(self.filtrar_estudiantes)
        self.combo_filtrar_estudiantes.currentTextChanged.connect(self.filtrar_estudiantes)
        self.btn_agregar_estudiante.clicked.connect(self.agregar_estudiante)
        self.btn_editar_estudiante.clicked.connect(self.editar_estudiante)
        self.btn_quitar_estudiante.clicked.connect(self.quitar_estudiante)
        if self.is_admin:
            self.btn_cargar_estudiantes_csv.clicked.connect(self.cargar_estudiantes_csv)

    # ---------------------- Internos ----------------------
    def _bloquear_campos_admin_only(self, bloquear: bool):
        # >>>>>>>>>>>> CAMBIO 2: aquí se deshabilitan / habilitan
        if bloquear:
            self.line_matricula.setDisabled(True)
            self.combo_semestre_est.setDisabled(True)
        else:
            self.line_matricula.setDisabled(False)
            self.line_matricula.setReadOnly(True)
            self.combo_semestre_est.setDisabled(False)
        # <<<<<<<<<<<<<<

    # ---------------------- Lógica ----------------------
    def cargar_estudiantes(self):
        self.table_estudiantes.setRowCount(0)
        query = """
            SELECT matricula, nombre, apellido_paterno, apellido_materno, semestre, estado
            FROM estudiantes
            ORDER BY nombre, apellido_paterno, apellido_materno
        """
        rows = self.db.run_query(query, fetch="all")
        if not rows:
            return
        for i, (mat, nom, ap_pat, ap_mat, sem, est) in enumerate(rows):
            nombre_completo = f"{nom} {ap_pat} {ap_mat}"
            self.table_estudiantes.insertRow(i)
            self.table_estudiantes.setItem(i, 0, QTableWidgetItem(mat))
            self.table_estudiantes.setItem(i, 1, QTableWidgetItem(nombre_completo))
            self.table_estudiantes.setItem(i, 2, QTableWidgetItem(sem))
            self.table_estudiantes.setItem(i, 3, QTableWidgetItem(est))

    def filtrar_estudiantes(self):
        texto = self.line_buscar_estudiante.text().lower().strip()
        sem_sel = self.combo_filtrar_estudiantes.currentText()
        for fila in range(self.table_estudiantes.rowCount()):
            nombre = self.table_estudiantes.item(fila, 1).text().lower()
            semestre = self.table_estudiantes.item(fila, 2).text()
            visible = True
            if texto and texto not in nombre:
                visible = False
            if sem_sel != "Todos" and semestre != sem_sel:
                visible = False
            self.table_estudiantes.setRowHidden(fila, not visible)

    def agregar_estudiante(self):
        mat = self.line_matricula.text().strip()
        nom = self.line_nombre_est.text().strip()
        ap_pat = self.line_apellido_pat_est.text().strip()
        ap_mat = self.line_apellido_mat_est.text().strip()
        sem = self.combo_semestre_est.currentText()
        est = self.combo_estado.currentText()
        if not mat or not nom or not ap_pat:
            return

        if self.editando_estudiante:
            if self.is_admin:
                self.db.run_query(
                    "UPDATE estudiantes SET nombre=?, apellido_paterno=?, apellido_materno=?, semestre=?, estado=? WHERE matricula=?",
                    (nom, ap_pat, ap_mat, sem, est, mat)
                )
            else:
                self.db.run_query(
                    "UPDATE estudiantes SET nombre=?, apellido_paterno=?, apellido_materno=?, estado=? WHERE matricula=?",
                    (nom, ap_pat, ap_mat, est, mat)
                )
            self.editando_estudiante = False
            self.fila_editando_estudiante = -1
            self.btn_agregar_estudiante.setText("AGREGAR")

            # >>>>>>>>>>>> CAMBIO 3: restaurar al modo agregar (no-admin)
            if not self.is_admin:
                self._bloquear_campos_admin_only(False)
            # <<<<<<<<<<<<<<

        else:
            try:
                self.db.run_query(
                    "INSERT INTO estudiantes (matricula,nombre,apellido_paterno,apellido_materno,semestre,estado) VALUES (?,?,?,?,?,?)",
                    (mat, nom, ap_pat, ap_mat, sem, est)
                )
            except Exception:
                return

        # Limpia
        self.line_matricula.clear()
        self.line_nombre_est.clear()
        self.line_apellido_pat_est.clear()
        self.line_apellido_mat_est.clear()
        self.combo_semestre_est.setCurrentIndex(0)
        self.combo_estado.setCurrentIndex(0)
        self.cargar_estudiantes()
        self.filtrar_estudiantes()

    def editar_estudiante(self):
        fila = self.table_estudiantes.currentRow()
        if fila < 0:
            return

        mat = self.table_estudiantes.item(fila, 0).text()
        nombre_split = self.table_estudiantes.item(fila, 1).text().split()
        if len(nombre_split) >= 3:
            ap_mat = nombre_split[-1]
            ap_pat = nombre_split[-2]
            nom = " ".join(nombre_split[:-2])
        elif len(nombre_split) == 2:
            nom = nombre_split[0]
            ap_pat = nombre_split[1]
            ap_mat = ""
        else:
            nom = nombre_split[0] if nombre_split else ""
            ap_pat = ""
            ap_mat = ""

        sem = self.table_estudiantes.item(fila, 2).text()
        est = self.table_estudiantes.item(fila, 3).text()

        self.line_matricula.setText(mat)
        self.line_nombre_est.setText(nom)
        self.line_apellido_pat_est.setText(ap_pat)
        self.line_apellido_mat_est.setText(ap_mat)
        self.combo_semestre_est.setCurrentText(sem)
        self.combo_estado.setCurrentText(est)

        self.editando_estudiante = True
        self.fila_editando_estudiante = fila
        self.btn_agregar_estudiante.setText("ACEPTAR")

        # >>>>>>>>>>>> CAMBIO 4: deshabilitar en modo edición si no-admin
        if not self.is_admin:
            self._bloquear_campos_admin_only(True)
        else:
            self.line_matricula.setReadOnly(False)
            self.combo_semestre_est.setEnabled(True)
        # <<<<<<<<<<<<<<

    def quitar_estudiante(self):
        fila = self.table_estudiantes.currentRow()
        if fila < 0:
            return
        mat = self.table_estudiantes.item(fila, 0).text()
        respuesta = QMessageBox.question(
            self.widget, "Advertencia",
            f"¿Está seguro de quitar el estudiante {mat}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return
        self.db.run_query("DELETE FROM estudiantes WHERE matricula=?", (mat,))
        self.table_estudiantes.removeRow(fila)

    def cargar_estudiantes_csv(self):
        fn, _ = QFileDialog.getOpenFileName(
            self.widget,
            "Selecciona CSV de Estudiantes",
            obtener_ruta("datos"),
            "CSV Files (*.csv)"
        )
        if not fn:
            return
        self.db.run_query("DELETE FROM estudiantes")
        with open(fn, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.db.run_query(
                    "INSERT INTO estudiantes (matricula,nombre,apellido_paterno,apellido_materno,semestre,estado) VALUES (?,?,?,?,?,?)",
                    (
                        row["matricula"].strip(),
                        row["nombre"].strip(),
                        row["apellido_paterno"].strip(),
                        row["apellido_materno"].strip(),
                        row["semestre"].strip(),
                        row["estado"].strip()
                    )
                )
        self.cargar_estudiantes()
        self.filtrar_estudiantes()

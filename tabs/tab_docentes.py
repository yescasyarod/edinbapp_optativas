#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import csv
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QFileDialog
)
# Permite importar utils desde el nivel superior
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import obtener_ruta


class TabDocentes:
    def __init__(self, db, is_admin: bool = False):
        self.db = db
        self.is_admin = is_admin
        self.widget = QWidget()
        self.editando_docente = False
        self.fila_editando_docente = -1
        self.docente_rfc_original = None

        self._setup_ui()
        self._connect_signals()
        # Carga inicial
        self.cargar_profesores_tab1()

        # Ocultar controles de edición/agregado si no es admin
        if not self.is_admin:
            self.btn_editar_profesor.hide()
            self.btn_quitar_profesor.hide()
            self.label_agregar_docente.hide()
            self.line_rfc_profesor.hide()
            self.line_nombres_profesor.hide()
            self.line_apellido_pat_profesor.hide()
            self.line_apellido_mat_profesor.hide()
            self.btn_agregar_profesor.hide()

    def _setup_ui(self):
        # Raíz y fondo
        self._tab = self.widget
        self._tab.setStyleSheet("background-color: white;")

        # Label DOCENTES
        self.label_docentes = QLabel("DOCENTES", self._tab)
        self.label_docentes.setGeometry(40, 40, 231, 25)
        self.label_docentes.setFont(QFont("Noto Sans", 20, QFont.Weight.Bold))
        self.label_docentes.setStyleSheet("color: rgb(12, 28, 140);")

        # Línea búsqueda
        self.line_buscar_docente = QLineEdit(self._tab)
        self.line_buscar_docente.setGeometry(710, 36, 481, 31)
        self.line_buscar_docente.setFont(QFont("Noto Sans", 8, QFont.Weight.Bold))
        self.line_buscar_docente.setStyleSheet(
            "border: 1.5px solid #0c1c8c; border-radius: 5px; "
            "color: rgb(12, 28, 140); background-color: white;"
        )
        self.line_buscar_docente.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.line_buscar_docente.setPlaceholderText("BUSCAR DOCENTE")

        # Tabla docentes
        self.table_profesores = QTableWidget(self._tab)
        self.table_profesores.setGeometry(40, 90, 1281, 361)
        self.table_profesores.setColumnCount(2)
        self.table_profesores.setHorizontalHeaderLabels(["RFC", "Nombre completo"])
        self.table_profesores.setAlternatingRowColors(True)
        self.table_profesores.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_profesores.horizontalHeader().setStretchLastSection(True)
        self.table_profesores.setColumnWidth(1, 400)
        self.table_profesores.setStyleSheet(
            "background-color: #d9dced; alternate-background-color: #e8eaf4;"
        )
        self.table_profesores.horizontalHeader().setStyleSheet(
            "background-color: #bfc4e0; font-weight: bold; color: #0c1c8c;"
        )

        # Botones EDITAR / QUITAR
        self.btn_editar_profesor = QPushButton("EDITAR", self._tab)
        self.btn_editar_profesor.setGeometry(1010, 460, 151, 31)
        self.btn_editar_profesor.setFont(QFont("Noto Sans", 7, QFont.Weight.Bold))
        self.btn_editar_profesor.setStyleSheet(
            "border:1.5px solid #0c1c8c; border-radius:12; "
            "color: rgb(12,28,140); background-color:white;"
        )

        self.btn_quitar_profesor = QPushButton("QUITAR", self._tab)
        self.btn_quitar_profesor.setGeometry(1170, 460, 151, 31)
        self.btn_quitar_profesor.setFont(QFont("Noto Sans", 7, QFont.Weight.Bold))
        self.btn_quitar_profesor.setStyleSheet(
            "border:1.5px solid #0c1c8c; border-radius:12; "
            "color: rgb(12,28,140); background-color:white;"
        )

        # Sección AGREGAR
        self.label_agregar_docente = QLabel("AGREGAR DOCENTE", self._tab)
        self.label_agregar_docente.setGeometry(40, 500, 231, 25)
        self.label_agregar_docente.setFont(
            QFont("Noto Sans", 12, QFont.Weight.Bold)
        )
        self.label_agregar_docente.setStyleSheet("color: rgb(12,28,140);")

        # Campos de entrada
        self.line_rfc_profesor = QLineEdit(self._tab)
        self.line_rfc_profesor.setGeometry(40, 540, 251, 26)
        self.line_rfc_profesor.setFont(QFont("Noto Sans", 8, QFont.Weight.Bold))
        self.line_rfc_profesor.setStyleSheet(
            "color: rgb(12,28,140); background:transparent; "
            "border:none; border-bottom:2px solid #0c1c8c;"
        )
        self.line_rfc_profesor.setPlaceholderText("RFC")

        self.line_nombres_profesor = QLineEdit(self._tab)
        self.line_nombres_profesor.setGeometry(330, 540, 231, 26)
        self.line_nombres_profesor.setFont(QFont("Noto Sans", 8, QFont.Weight.Bold))
        self.line_nombres_profesor.setStyleSheet(
            "color: rgb(12,28,140); background:transparent; "
            "border:none; border-bottom:2px solid #0c1c8c;"
        )
        self.line_nombres_profesor.setPlaceholderText("NOMBRES")

        self.line_apellido_pat_profesor = QLineEdit(self._tab)
        self.line_apellido_pat_profesor.setGeometry(40, 590, 251, 26)
        self.line_apellido_pat_profesor.setFont(QFont("Noto Sans", 8, QFont.Weight.Bold))
        self.line_apellido_pat_profesor.setStyleSheet(
            "color: rgb(12,28,140); background:transparent; "
            "border:none; border-bottom:2px solid #0c1c8c;"
        )
        self.line_apellido_pat_profesor.setPlaceholderText("APELLIDO PATERNO")

        self.line_apellido_mat_profesor = QLineEdit(self._tab)
        self.line_apellido_mat_profesor.setGeometry(330, 590, 231, 26)
        self.line_apellido_mat_profesor.setFont(QFont("Noto Sans", 8, QFont.Weight.Bold))
        self.line_apellido_mat_profesor.setStyleSheet(
            "color: rgb(12,28,140); background:transparent; "
            "border:none; border-bottom:2px solid #0c1c8c;"
        )
        self.line_apellido_mat_profesor.setPlaceholderText("APELLIDO MATERNO")

        # Botón AGREGAR
        self.btn_agregar_profesor = QPushButton("AGREGAR", self._tab)
        self.btn_agregar_profesor.setGeometry(40, 640, 151, 31)
        self.btn_agregar_profesor.setFont(QFont("Noto Sans", 8, QFont.Weight.Bold))
        self.btn_agregar_profesor.setStyleSheet(
            "border:1.5px solid #0c1c8c; border-radius:12; "
            "color: rgb(12,28,140); background-color:white;"
        )

        # Botón CARGAR CSV (solo admin)
        self.btn_cargar_docentes = QPushButton(
            "CARGAR DOCENTES (CSV)", self._tab
        )
        self.btn_cargar_docentes.setGeometry(1050, 640, 271, 29)
        self.btn_cargar_docentes.setFont(
            QFont("Noto Sans", 8, QFont.Weight.Bold)
        )
        self.btn_cargar_docentes.setStyleSheet(
            "border:1.5px solid #0c1c8c; border-radius:12; "
            "color: rgb(12,28,140); background-color:white;"
        )
        if not self.is_admin:
            self.btn_cargar_docentes.hide()

    def _connect_signals(self):
        self.line_buscar_docente.textChanged.connect(self.filtrar_profesores_tab1)
        self.btn_agregar_profesor.clicked.connect(self.agregar_profesor)
        self.btn_editar_profesor.clicked.connect(self.editar_profesor)
        self.btn_quitar_profesor.clicked.connect(self.quitar_profesor)
        if self.is_admin:
            self.btn_cargar_docentes.clicked.connect(self.cargar_docentes_csv)

    def cargar_profesores_tab1(self):
        self.table_profesores.setRowCount(0)
        rows = self.db.run_query(
            "SELECT rfc, nombre, apellido_paterno, apellido_materno "
            "FROM docentes ORDER BY nombre, apellido_paterno, apellido_materno",
            fetch="all"
        )
        for i, (rfc, nom, ap_pat, ap_mat) in enumerate(rows or []):
            nombre_completo = f"{nom} {ap_pat} {ap_mat}"
            self.table_profesores.insertRow(i)
            self.table_profesores.setItem(i, 0, QTableWidgetItem(rfc))
            self.table_profesores.setItem(i, 1, QTableWidgetItem(nombre_completo))

    def filtrar_profesores_tab1(self):
        texto = self.line_buscar_docente.text().lower().strip()
        for fila in range(self.table_profesores.rowCount()):
            rfc = self.table_profesores.item(fila, 0).text().lower()
            nombre = self.table_profesores.item(fila, 1).text().lower()
            visible = True
            if texto and texto not in rfc and texto not in nombre:
                visible = False
            self.table_profesores.setRowHidden(fila, not visible)

    def agregar_profesor(self):
        rfc = self.line_rfc_profesor.text().strip()
        nom = self.line_nombres_profesor.text().strip()
        ap_pat = self.line_apellido_pat_profesor.text().strip()
        ap_mat = self.line_apellido_mat_profesor.text().strip()
        if not rfc or not nom or not ap_pat:
            return

        if self.editando_docente:
            if rfc == self.docente_rfc_original:
                self.db.run_query(
                    "UPDATE docentes SET nombre=?, apellido_paterno=?, apellido_materno=? WHERE rfc=?",
                    (nom, ap_pat, ap_mat, rfc)
                )
            else:
                try:
                    self.db.run_query(
                        "UPDATE docentes SET rfc=?, nombre=?, apellido_paterno=?, apellido_materno=? WHERE rfc=?",
                        (rfc, nom, ap_pat, ap_mat, self.docente_rfc_original)
                    )
                except Exception:
                    return
            self.editando_docente = False
            self.docente_rfc_original = None
            self.btn_agregar_profesor.setText("AGREGAR")
        else:
            try:
                self.db.run_query(
                    "INSERT INTO docentes (rfc, nombre, apellido_paterno, apellido_materno) VALUES (?, ?, ?, ?)",
                    (rfc, nom, ap_pat, ap_mat)
                )
            except Exception:
                return

        # Limpiar campos y recargar tabla
        self.line_rfc_profesor.clear()
        self.line_nombres_profesor.clear()
        self.line_apellido_pat_profesor.clear()
        self.line_apellido_mat_profesor.clear()
        self.cargar_profesores_tab1()
        self.filtrar_profesores_tab1()

    def editar_profesor(self):
        fila = self.table_profesores.currentRow()
        if fila < 0:
            return
        rfc = self.table_profesores.item(fila, 0).text()
        partes = self.table_profesores.item(fila, 1).text().split()
        if len(partes) >= 3:
            ap_mat = partes[-1]
            ap_pat = partes[-2]
            nombres = " ".join(partes[:-2])
        elif len(partes) == 2:
            nombres, ap_pat = partes
            ap_mat = ""
        else:
            nombres = partes[0] if partes else ""
            ap_pat = ap_mat = ""

        self.line_rfc_profesor.setText(rfc)
        self.line_nombres_profesor.setText(nombres)
        self.line_apellido_pat_profesor.setText(ap_pat)
        self.line_apellido_mat_profesor.setText(ap_mat)
        self.editando_docente = True
        self.docente_rfc_original = rfc
        self.btn_agregar_profesor.setText("ACEPTAR")

    def quitar_profesor(self):
        fila = self.table_profesores.currentRow()
        if fila < 0:
            return
        rfc = self.table_profesores.item(fila, 0).text()
        resp = QMessageBox.question(
            self.widget, "Advertencia",
            f"¿Está seguro de quitar el docente con RFC {rfc}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp != QMessageBox.StandardButton.Yes:
            return
        self.db.run_query("DELETE FROM docentes WHERE rfc=?", (rfc,))
        self.table_profesores.removeRow(fila)

    def cargar_docentes_csv(self):
        fn, _ = QFileDialog.getOpenFileName(
            self.widget,
            "Selecciona CSV de Docentes",
            obtener_ruta("datos"),
            "CSV Files (*.csv)"
        )
        if not fn:
            return
        # Reemplaza todos los docentes
        self.db.run_query("DELETE FROM docentes")
        with open(fn, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.db.run_query(
                    "INSERT INTO docentes (rfc, nombre, apellido_paterno, apellido_materno) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        row["rfc"].strip(),
                        row["nombre"].strip(),
                        row["apellido_paterno"].strip(),
                        row["apellido_materno"].strip()
                    )
                )
        self.cargar_profesores_tab1()
        self.filtrar_profesores_tab1()

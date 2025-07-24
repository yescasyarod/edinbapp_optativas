# proyecto/tabs/tab_estadisticas.py

from PySide6.QtWidgets import (
    QWidget, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QVBoxLayout
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

class TabEstadisticas:
    def __init__(self, db):
        self.db = db
        self.widget = QWidget()
        self.widget.setStyleSheet("background-color: white;")
        self._setup_ui()
        self._connect_signals()
        # NO llamamos a cargar_estadisticas() aquí para que empiece VACÍO

    def _setup_ui(self):
        layout = QVBoxLayout(self.widget)

        # Título
        title = QLabel("Top de Optativas por velocidad de llenado")
        title.setFont(QFont("Noto Sans", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: rgb(12,28,140);")
        layout.addWidget(title)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Optativa", "Inscritos", "Cupo", "% Llenado"])
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        # estilos iguales a TabEstudiantes
        self.table.setStyleSheet(
            "background-color: #d9dced; alternate-background-color: #e8eaf4;"
        )
        self.table.horizontalHeader().setStyleSheet(
            "background-color: #bfc4e0; font-weight: bold; color: #0c1c8c;"
        )
        layout.addWidget(self.table)

        # Botón reiniciar
        self.btn_reiniciar = QPushButton("Reiniciar estadísticas")
        self.btn_reiniciar.setFont(QFont("Noto Sans", 8, QFont.Weight.Bold))
        self.btn_reiniciar.setStyleSheet(
            "border:1.5px solid #0c1c8c; border-radius:12; "
            "color: rgb(12,28,140); background-color:white;"
        )
        layout.addWidget(self.btn_reiniciar)

    def _connect_signals(self):
        # limpiar tabla al pulsar Reiniciar
        self.btn_reiniciar.clicked.connect(self._clear_table)

    def _clear_table(self):
        self.table.setRowCount(0)

    def cargar_estadisticas(self):
        # 1) Vaciar
        self.table.setRowCount(0)

        # 2) Consultar velocidad (ratio) y número de inscritos
        rows = self.db.run_query(
            """
            SELECT o.nombre,
                   COUNT(i.id)          AS inscritos,
                   o.cupo,
                   -- ratio: inscritos/cupo
                   CAST(COUNT(i.id) AS REAL)/o.cupo AS ratio
            FROM optativas o
            LEFT JOIN inscripciones i ON o.id = i.optativa_id
            GROUP BY o.id
            ORDER BY ratio DESC, inscritos DESC
            """,
            fetch="all"
        )

        # 3) Poblar, del que más rápido se llena al que menos
        for i, (nombre, inscritos, cupo, ratio) in enumerate(rows):
            porcentaje = f"{(ratio * 100):.1f}%"
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(nombre))
            self.table.setItem(i, 1, QTableWidgetItem(str(inscritos)))
            self.table.setItem(i, 2, QTableWidgetItem(str(cupo)))
            self.table.setItem(i, 3, QTableWidgetItem(porcentaje))

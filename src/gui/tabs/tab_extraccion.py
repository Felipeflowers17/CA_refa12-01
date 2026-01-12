from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QDate  # <--- Importamos QDate

from qfluentwidgets import (
    CalendarPicker, SpinBox, PrimaryPushButton, 
    FluentIcon as FIF, ProgressBar, InfoBar, CardWidget
)

class TabExtraccion(QFrame):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        
        self.v_layout = QVBoxLayout(self)
        self.v_layout.setSpacing(20)
        self.v_layout.setContentsMargins(30, 20, 30, 20)

        # --- Tarjeta de Configuración ---
        card = CardWidget(self)
        card_layout = QVBoxLayout(card)
        
        # Título
        title = QLabel("Scraping Manual", self)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        card_layout.addWidget(title)
        
        # Selección de Fechas
        dates_layout = QHBoxLayout()
        
        self.date_from = CalendarPicker(self)
        # CORRECCIÓN 1: Usamos QDate de Qt, no datetime de Python
        self.date_from.setDate(QDate.currentDate())
        self.date_from.setDateFormat(Qt.ISODate) 
        
        self.date_to = CalendarPicker(self)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setDateFormat(Qt.ISODate)
        
        dates_layout.addWidget(QLabel("Desde:"))
        dates_layout.addWidget(self.date_from)
        dates_layout.addSpacing(20)
        dates_layout.addWidget(QLabel("Hasta:"))
        dates_layout.addWidget(self.date_to)
        dates_layout.addStretch()
        
        card_layout.addLayout(dates_layout)

        # Límite de Páginas
        pages_layout = QHBoxLayout()
        self.spin_pages = SpinBox(self)
        self.spin_pages.setRange(0, 1000)
        self.spin_pages.setValue(0) # 0 = Todas
        self.spin_pages.setFixedWidth(160)
        
        pages_layout.addWidget(QLabel("Máx Páginas (0 = Todas):"))
        pages_layout.addWidget(self.spin_pages)
        pages_layout.addStretch()
        
        card_layout.addLayout(pages_layout)
        self.v_layout.addWidget(card)

        # --- Zona de Acción ---
        self.btn_run = PrimaryPushButton("Iniciar Scraping", self)
        self.btn_run.setIcon(FIF.SEARCH)
        self.btn_run.clicked.connect(self.iniciar_proceso)
        
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        
        self.lbl_status = QLabel("", self)
        self.lbl_status.setStyleSheet("color: #666;")

        self.v_layout.addWidget(self.btn_run)
        self.v_layout.addWidget(self.lbl_status)
        self.v_layout.addWidget(self.progress_bar)
        self.v_layout.addStretch()

    def iniciar_proceso(self):
        # Bloquear UI
        self.btn_run.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        
        # CORRECCIÓN 2: Convertir QDate de vuelta a Python date para el backend
        qdate_from = self.date_from.date
        qdate_to = self.date_to.date
        
        # toPython() convierte QDate a datetime.date
        # (Disponible en PySide6 moderno. Si falla, usar: qdate.toPython())
        py_date_from = qdate_from.toPython()
        py_date_to = qdate_to.toPython()

        config = {
            "date_from": py_date_from, 
            "date_to": py_date_to,
            "max_paginas": self.spin_pages.value()
        }
        
        # Llamar al Controlador
        self.controller.run_extraction_task(
            config,
            on_progress=self.actualizar_progreso,
            on_finish=self.proceso_terminado,
            on_error=self.proceso_error
        )

    def actualizar_progreso(self, texto, valor):
        if texto:
            self.lbl_status.setText(texto)
        if valor is not None:
            self.progress_bar.setValue(valor)

    def proceso_terminado(self, resultado):
        self.btn_run.setEnabled(True)
        self.progress_bar.hide()
        self.lbl_status.setText(f"Listo. {resultado} nuevas licitaciones encontradas.")
        InfoBar.success("Proceso Completado", "La extracción ha finalizado exitosamente.", parent=self)

    def proceso_error(self, error_msg):
        self.btn_run.setEnabled(True)
        self.progress_bar.hide()
        self.lbl_status.setText("Error en el proceso.")
        InfoBar.error("Error", error_msg, parent=self)
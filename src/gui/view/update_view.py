from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from qfluentwidgets import (
    CardWidget, CheckBox, PrimaryPushButton, FluentIcon as FIF,
    ProgressBar, InfoBar, StrongBodyLabel, BodyLabel
)

class UpdateView(QFrame):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setObjectName("update_view")
        
        # Layout Principal
        self.v_layout = QVBoxLayout(self)
        self.v_layout.setContentsMargins(30, 30, 30, 30)
        self.v_layout.setSpacing(20)

        # 1. Título y Descripción
        self.lbl_title = StrongBodyLabel("Actualizar Información de Pestañas", self)
        self.lbl_title.setStyleSheet("font-size: 20px; font-weight: bold;")
        
        self.lbl_desc = BodyLabel(
            "Esta herramienta busca cambios recientes (fechas, estados) en el portal Mercado Público "
            "para las licitaciones que ya tienes guardadas.", self
        )
        self.lbl_desc.setWordWrap(True)
        
        self.v_layout.addWidget(self.lbl_title)
        self.v_layout.addWidget(self.lbl_desc)

        # 2. Tarjeta de Opciones
        self.card = CardWidget(self)
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(20, 20, 20, 20)
        self.card_layout.setSpacing(15)
        
        self.lbl_card_title = StrongBodyLabel("Selecciona qué actualizar:", self.card)
        self.card_layout.addWidget(self.lbl_card_title)
        
        # Checkboxes [Manual source: 7]
        self.chk_candidatas = CheckBox("Candidatas (Recientes)", self.card)
        self.chk_seguimiento = CheckBox("Seguimiento (Favoritos)", self.card)
        self.chk_ofertadas = CheckBox("Ofertadas", self.card)
        
        # Por defecto marcamos lo más lógico
        self.chk_seguimiento.setChecked(True)
        self.chk_ofertadas.setChecked(True)
        
        self.card_layout.addWidget(self.chk_candidatas)
        self.card_layout.addWidget(self.chk_seguimiento)
        self.card_layout.addWidget(self.chk_ofertadas)
        
        self.v_layout.addWidget(self.card)

        # 3. Zona de Acción
        self.btn_update = PrimaryPushButton("Actualizar Ahora", self)
        self.btn_update.setIcon(FIF.SYNC)
        self.btn_update.clicked.connect(self.iniciar_actualizacion)
        
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        
        self.lbl_status = BodyLabel("", self)
        self.lbl_status.setStyleSheet("color: #666;")

        self.v_layout.addWidget(self.btn_update)
        self.v_layout.addWidget(self.lbl_status)
        self.v_layout.addWidget(self.progress_bar)
        
        self.v_layout.addStretch()

    def iniciar_actualizacion(self):
        # 1. Recopilar selección
        alcances = []
        if self.chk_candidatas.isChecked(): alcances.append("candidatas")
        if self.chk_seguimiento.isChecked(): alcances.append("seguimiento")
        if self.chk_ofertadas.isChecked(): alcances.append("ofertadas")
        
        if not alcances:
            InfoBar.warning("Atención", "Selecciona al menos una pestaña para actualizar.", parent=self)
            return

        # 2. Bloquear UI
        self.btn_update.setEnabled(False)
        self.chk_candidatas.setEnabled(False)
        self.chk_seguimiento.setEnabled(False)
        self.chk_ofertadas.setEnabled(False)
        
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.lbl_status.setText("Iniciando conexión...")

        # 3. Llamar al Controlador (Hilo secundario)
        self.controller.run_update_task(
            alcances,
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
        self._restaurar_ui()
        self.lbl_status.setText("Actualización completada.")
        self.progress_bar.setValue(100)
        InfoBar.success("Listo", "La información se ha sincronizado correctamente.", parent=self)

    def proceso_error(self, error_msg):
        self._restaurar_ui()
        self.lbl_status.setText("Error en la actualización.")
        InfoBar.error("Error", f"Ocurrió un fallo: {error_msg}", parent=self)

    def _restaurar_ui(self):
        self.btn_update.setEnabled(True)
        self.chk_candidatas.setEnabled(True)
        self.chk_seguimiento.setEnabled(True)
        self.chk_ofertadas.setEnabled(True)
        self.progress_bar.hide()
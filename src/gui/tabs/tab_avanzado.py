from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import QTime
from qfluentwidgets import (
    CardWidget, SwitchButton, TimePicker, PrimaryPushButton, 
    InfoBar, BodyLabel
)

class TabAvanzado(QFrame):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        
        # Tarjeta Piloto Automático
        card = CardWidget(self)
        card_layout = QVBoxLayout(card)
        
        title = QLabel("Piloto Automático", self)
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        card_layout.addWidget(title)
        
        desc = BodyLabel(
            "Extraer información automáticamente todos los días a la hora seleccionada.\n"
            "Se buscarán licitaciones del día anterior (Ayer).", self
        )
        desc.setWordWrap(True)
        card_layout.addWidget(desc)
        card_layout.addSpacing(15)
        
        # Controles
        self.switch_auto = SwitchButton("Extracción Diaria", self)
        
        self.time_picker = TimePicker(self)
        self.time_picker.setTime(QTime(8, 0)) # Default 08:00
        
        card_layout.addWidget(self.switch_auto)
        card_layout.addSpacing(10)
        card_layout.addWidget(QLabel("Hora de ejecución:", self))
        card_layout.addWidget(self.time_picker)
        
        layout.addWidget(card)
        
        # Botón Guardar
        self.btn_save = PrimaryPushButton("Guardar Configuración", self)
        self.btn_save.clicked.connect(self.guardar_config)
        layout.addWidget(self.btn_save)
        
        layout.addStretch()
        
        self.cargar_estado()

    def cargar_estado(self):
        config = self.controller.get_autopilot_config()
        self.switch_auto.setChecked(config["enabled"])
        
        t_str = config["time"] or "08:00"
        try:
            h, m = map(int, t_str.split(":"))
            self.time_picker.setTime(QTime(h, m))
        except:
            pass

    def guardar_config(self):
        enabled = self.switch_auto.isChecked()
        t = self.time_picker.time
        t_str = f"{t.hour():02d}:{t.minute():02d}"
        
        self.controller.save_autopilot_config(enabled, t_str)
        InfoBar.success("Guardado", "Configuración de Piloto Automático actualizada.", parent=self)
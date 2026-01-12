from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt
from qfluentwidgets import (
    CardWidget, PlainTextEdit, ComboBox, PrimaryPushButton, 
    FluentIcon as FIF, ProgressBar, InfoBar, StrongBodyLabel, BodyLabel
)

class TabImportacion(QFrame):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        
        self.v_layout = QVBoxLayout(self)
        self.v_layout.setSpacing(20)
        self.v_layout.setContentsMargins(30, 20, 30, 20)

        # --- Tarjeta Principal ---
        card = CardWidget(self)
        card_layout = QVBoxLayout(card)
        
        # Título
        title = StrongBodyLabel("Importación Manual por Código", self)
        title.setStyleSheet("font-size: 18px;")
        desc = BodyLabel("Pega una lista de códigos (uno por línea) para buscarlos y guardarlos directamente.", self)
        desc.setWordWrap(True)
        
        card_layout.addWidget(title)
        card_layout.addWidget(desc)
        card_layout.addSpacing(10)
        
        # Área de Texto
        self.txt_codes = PlainTextEdit(self)
        self.txt_codes.setPlaceholderText("Ejemplo:\n1234-56-LE24\n5555-10-LP24\n...")
        self.txt_codes.setMinimumHeight(200)
        card_layout.addWidget(self.txt_codes)
        
        # Opciones de Destino
        opts_layout = QHBoxLayout()
        opts_layout.addWidget(BodyLabel("Guardar en:", self))
        
        self.combo_dest = ComboBox(self)
        self.combo_dest.addItems(["Candidatas", "Seguimiento", "Ofertadas"])
        self.combo_dest.setFixedWidth(200)
        
        opts_layout.addWidget(self.combo_dest)
        opts_layout.addStretch()
        
        card_layout.addLayout(opts_layout)
        self.v_layout.addWidget(card)

        # --- Zona de Acción ---
        self.btn_run = PrimaryPushButton("Importar Códigos", self)
        self.btn_run.setIcon(FIF.DOWNLOAD)
        self.btn_run.clicked.connect(self.iniciar_importacion)
        
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        
        self.lbl_status = BodyLabel("", self)
        self.lbl_status.setStyleSheet("color: #666;")

        self.v_layout.addWidget(self.btn_run)
        self.v_layout.addWidget(self.lbl_status)
        self.v_layout.addWidget(self.progress_bar)
        self.v_layout.addStretch()

    def iniciar_importacion(self):
        # 1. Obtener texto
        raw_text = self.txt_codes.toPlainText()
        # Separar por líneas y limpiar espacios
        codigos = [line.strip() for line in raw_text.split('\n') if line.strip()]
        
        if not codigos:
            InfoBar.warning("Campo Vacío", "Por favor escribe al menos un código.", parent=self)
            return

        # 2. Mapear destino
        destino_map = {
            "Candidatas": "candidatas",
            "Seguimiento": "seguimiento",
            "Ofertadas": "ofertadas"
        }
        destino = destino_map.get(self.combo_dest.currentText(), "candidatas")

        # 3. Bloquear UI
        self.btn_run.setEnabled(False)
        self.txt_codes.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        
        # 4. Llamar al Controller
        self.controller.run_manual_import(
            codigos, 
            destino,
            on_progress=self.actualizar_progreso,
            on_finish=self.proceso_terminado,
            on_error=self.proceso_error
        )

    def actualizar_progreso(self, texto, valor):
        if texto:
            self.lbl_status.setText(texto)
        if valor is not None:
            self.progress_bar.setValue(valor)

    def proceso_terminado(self, total_procesados):
        self._restaurar_ui()
        self.lbl_status.setText(f"Proceso finalizado. {total_procesados} importados.")
        InfoBar.success("Importación Exitosa", f"Se procesaron {total_procesados} códigos.", parent=self)
        self.txt_codes.clear()

    def proceso_error(self, error_msg):
        self._restaurar_ui()
        self.lbl_status.setText("Error en la importación.")
        InfoBar.error("Error", error_msg, parent=self)

    def _restaurar_ui(self):
        self.btn_run.setEnabled(True)
        self.txt_codes.setEnabled(True)
        self.progress_bar.hide()
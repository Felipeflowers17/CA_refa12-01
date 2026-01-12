from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt
from qfluentwidgets import (
    SubtitleLabel, PrimaryPushButton, PushButton, 
    PlainTextEdit, CaptionLabel
)

class NoteDialog(QDialog):
    def __init__(self, codigo_ca, current_note="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Notas Personales")
        self.resize(400, 300)
        
        # Estilo fondo blanco limpio
        self.setStyleSheet("QDialog { background-color: #ffffff; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título
        layout.addWidget(SubtitleLabel(f"Notas para {codigo_ca}", self))
        layout.addWidget(CaptionLabel("Escribe recordatorios o detalles importantes aquí.", self))

        # Área de Texto
        self.text_edit = PlainTextEdit(self)
        self.text_edit.setPlaceholderText("Ej: Contactar proveedor, falta certificado, etc...")
        self.text_edit.setPlainText(current_note)
        layout.addWidget(self.text_edit)

        # Botones
        h_layout = QHBoxLayout()
        self.btn_cancel = PushButton("Cancelar", self)
        self.btn_save = PrimaryPushButton("Guardar Nota", self)
        
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self.accept)

        h_layout.addStretch()
        h_layout.addWidget(self.btn_cancel)
        h_layout.addWidget(self.btn_save)
        
        layout.addLayout(h_layout)

    def get_text(self):
        return self.text_edit.toPlainText()
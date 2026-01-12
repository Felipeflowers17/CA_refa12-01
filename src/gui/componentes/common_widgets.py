from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class PlaceholderView(QFrame):
    """
    Vista genérica para secciones que aún no están implementadas.
    Se mueve aquí para evitar importaciones circulares.
    """
    def __init__(self, text, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text.replace(" ", "-"))
        layout = QVBoxLayout(self)
        label = QLabel(f"Vista: {text}", self)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
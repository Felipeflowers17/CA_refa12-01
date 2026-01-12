from PySide6.QtWidgets import QStyledItemDelegate, QStyle
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QBrush, QPen

class ScoreBadgeDelegate(QStyledItemDelegate):
    """
    Renderiza un número como una 'insignia' (Badge) de color.
    Verde: Positivo | Gris: Neutro | Rojo: Negativo
    """
    def paint(self, painter: QPainter, option, index):
        # Guardamos el estado del painter
        painter.save()
        
        # 1. Obtener datos
        try:
            score = int(index.data())
        except (ValueError, TypeError):
            score = 0
            
        # 2. Definir Colores según lógica de negocio
        if score >= 10:
            bg_color = QColor("#107C10")  # Verde Oscuro (Excelencia)
            text_color = Qt.white
        elif score > 0:
            bg_color = QColor("#dff6dd")  # Verde Claro
            text_color = QColor("#107C10")
        elif score == 0:
            bg_color = QColor("#f3f3f3")  # Gris (Neutro)
            text_color = QColor("#666666")
        elif score > -50:
            bg_color = QColor("#fde7e9")  # Rojo Claro
            text_color = QColor("#c50f1f")
        else:
            bg_color = QColor("#c50f1f")  # Rojo Intenso (Bloqueo)
            text_color = Qt.white

        # 3. Configurar área de dibujo (centrada con padding)
        rect = option.rect
        badge_width = 50
        badge_height = 22
        
        # Centrar el badge en la celda
        x = rect.x() + (rect.width() - badge_width) / 2
        y = rect.y() + (rect.height() - badge_height) / 2
        badge_rect = QRectF(x, y, badge_width, badge_height)
        
        # 4. Dibujar Fondo (Cápsula redondeada)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(badge_rect, 10, 10) # Radio 10 para efecto píldora
        
        # 5. Dibujar Texto
        painter.setPen(QPen(text_color))
        # Ajuste fino para centrar texto verticalmente
        painter.drawText(badge_rect, Qt.AlignCenter, str(score))
        
        painter.restore()
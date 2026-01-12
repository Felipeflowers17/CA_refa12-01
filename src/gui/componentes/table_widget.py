from typing import List, Dict
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTableWidgetItem, QHeaderView
from qfluentwidgets import TableWidget

class LicitacionesTable(TableWidget):
    """
    Tabla personalizada para mostrar licitaciones.
    Soporta:
    - Columnas redimensionables manualmente.
    - Columna especial para iconos de notas.
    - Bloqueo de edición (Solo lectura).
    - Menú contextual y doble clic.
    """
    # Señales: (data_row, global_position)
    custom_context_menu_requested = Signal(dict, object) 
    # Señales: (codigo_ca)
    row_double_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # --- Configuración Visual ---
        self.setBorderVisible(True)
        self.setBorderRadius(8)
        self.setWordWrap(False)
        self.verticalHeader().hide()
        
        # Comportamiento de Selección y Edición
        self.setSelectionBehavior(TableWidget.SelectRows)
        self.setEditTriggers(TableWidget.NoEditTriggers) # Bloqueo global de edición
        
        # --- Definición de Columnas ---
        self.headers = [
            "Score",           # 0
            "Nota",            # 1 (Icono)
            "Nombre Licitación", # 2 (El más largo)
            "Estado",          # 3
            "Código",          # 4
            "Organismo",       # 5
            "F. Publicación",  # 6
            "F. Cierre",       # 7
            "F. 2do Llamado",  # 8
            "Monto (CLP)"      # 9
        ]
        self.setColumnCount(len(self.headers))
        self.setHorizontalHeaderLabels(self.headers)
        
        # --- AJUSTE DE TAMAÑOS (CORREGIDO) ---
        
        # 1. Modo Interactivo: Permite al usuario redimensionar cualquier columna manualmente
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        # 2. Anchos Iniciales Recomendados
        self.setColumnWidth(0, 60)   # Score (Pequeño)
        self.setColumnWidth(1, 50)   # Nota (Muy pequeño, solo icono)
        self.setColumnWidth(2, 400)  # Nombre: Ancho fijo inicial grande, pero ajustable
        self.setColumnWidth(3, 120)  # Estado
        self.setColumnWidth(4, 120)  # Código
        self.setColumnWidth(5, 200)  # Organismo
        self.setColumnWidth(6, 110)  # Fechas
        self.setColumnWidth(7, 110)
        self.setColumnWidth(8, 110)
        
        # 3. Estirar la última columna (Monto) para llenar el espacio vacío a la derecha
        self.horizontalHeader().setStretchLastSection(True)
        
        # --- Eventos ---
        self.itemDoubleClicked.connect(self._on_dbl_click)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)
        
        # Almacén de datos local
        self.current_data: List[Dict] = []

    def set_data(self, data_list: List[Dict]):
        """Recibe la lista de diccionarios del Controller y llena la tabla."""
        self.current_data = data_list
        self.setRowCount(len(data_list))
        self.setSortingEnabled(False) # Desactivar sorting mientras insertamos masivamente

        for row, item in enumerate(data_list):
            # Helper para crear items de SOLO LECTURA
            def create_item(text):
                it = QTableWidgetItem(str(text))
                # Flags: Habilitado y Seleccionable, pero NO Editable
                it.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                return it

            # 0. Score (Con Tooltip de detalle)
            score_val = item.get('puntuacion_final', 0)
            score_item = create_item(score_val)
            score_item.setTextAlignment(Qt.AlignCenter)
            
            detalle = item.get('puntaje_detalle')
            if detalle:
                tooltip_txt = "\n".join(detalle) if isinstance(detalle, list) else str(detalle)
                score_item.setToolTip(f"Detalle Puntaje:\n{tooltip_txt}")
            self.setItem(row, 0, score_item)

            # 1. Nota (Icono Visual)
            txt_nota = "📝" if item.get('tiene_nota') else ""
            nota_item = create_item(txt_nota)
            nota_item.setTextAlignment(Qt.AlignCenter)
            if item.get('tiene_nota'):
                nota_item.setToolTip("Esta licitación tiene notas personales.")
            self.setItem(row, 1, nota_item)

            # 2. Nombre (Con Tooltip por si se corta)
            nombre = item.get('nombre', '')
            nombre_item = create_item(nombre)
            nombre_item.setToolTip(nombre)
            self.setItem(row, 2, nombre_item)

            # 3. Estado
            self.setItem(row, 3, create_item(item.get('estado_ca_texto', '')))
            
            # 4. Código
            self.setItem(row, 4, create_item(item.get('codigo_ca', '')))
            
            # 5. Organismo
            self.setItem(row, 5, create_item(item.get('organismo_nombre', '')))
            
            # 6. Fecha Publicación
            f_pub = item.get('fecha_publicacion')
            self.setItem(row, 6, create_item(f_pub if f_pub else ""))

            # 7. Fecha Cierre
            f_cierre = item.get('fecha_cierre')
            f_txt = f_cierre.strftime("%d-%m %H:%M") if f_cierre else ""
            self.setItem(row, 7, create_item(f_txt))

            # 8. Fecha 2do Llamado
            f_2do = item.get('fecha_cierre_segundo_llamado')
            f2_txt = f_2do.strftime("%d-%m %H:%M") if f_2do else "N/A"
            self.setItem(row, 8, create_item(f2_txt))
            
            # 9. Monto (Formateado)
            monto = item.get('monto_clp') or 0
            monto_txt = f"${int(monto):,}".replace(",", ".") if monto else "N/A"
            self.setItem(row, 9, create_item(monto_txt))

        self.setSortingEnabled(True) # Reactivar sorting

    def _on_dbl_click(self, item):
        row = item.row()
        if 0 <= row < len(self.current_data):
            # Obtenemos el código oculto en los datos originales, no de la celda visual
            codigo = self.current_data[row].get('codigo_ca')
            if codigo:
                self.row_double_clicked.emit(codigo)

    def _on_context_menu(self, pos):
        item = self.itemAt(pos)
        if item:
            row = item.row()
            global_pos = self.mapToGlobal(pos)
            if 0 <= row < len(self.current_data):
                data_row = self.current_data[row]
                self.custom_context_menu_requested.emit(data_row, global_pos)
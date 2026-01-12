from PySide6.QtWidgets import QFrame, QVBoxLayout, QStackedWidget
from qfluentwidgets import SegmentedWidget

# Importamos las pestañas reales
from src.gui.tabs.tab_extraccion import TabExtraccion
from src.gui.tabs.tab_exportacion import TabExportacion
from src.gui.tabs.tab_puntajes import TabPuntajes
from src.gui.tabs.tab_avanzado import TabAvanzado
from src.gui.tabs.tab_importacion import TabImportacion

# Importación de componentes comunes
from src.gui.componentes.common_widgets import PlaceholderView 

class ToolsView(QFrame):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        
        # --- CORRECCIÓN AQUÍ ---
        # QFluentWidgets exige que este widget tenga un nombre único
        self.setObjectName("herramientas_view") 
        # -----------------------

        self.controller = controller
        
        self.v_layout = QVBoxLayout(self)
        self.v_layout.setContentsMargins(0, 0, 0, 0)

        # 1. Barra de Navegación (Pivot/Segmented)
        self.pivot = SegmentedWidget(self)
        self.v_layout.addWidget(self.pivot)
        self.v_layout.addSpacing(10)

        # 2. Stack de Vistas
        self.stacked_widget = QStackedWidget(self)
        
        # Instancias Reales
        self.tab_extraer = TabExtraccion(self.controller)
        self.tab_importar = TabImportacion(self.controller)
        self.tab_exportar = TabExportacion(self.controller)
        self.tab_puntajes = TabPuntajes(self.controller)
        self.tab_avanzado = TabAvanzado(self.controller)
        
        # Añadir al Stack
        self.stacked_widget.addWidget(self.tab_extraer)
        self.stacked_widget.addWidget(self.tab_importar)
        self.stacked_widget.addWidget(self.tab_exportar)
        self.stacked_widget.addWidget(self.tab_puntajes)
        self.stacked_widget.addWidget(self.tab_avanzado)
        
        self.v_layout.addWidget(self.stacked_widget)

        # 3. Vincular
        self.addSubInterface(self.tab_extraer, "Extraer")
        self.addSubInterface(self.tab_importar, "Importar")
        self.addSubInterface(self.tab_exportar, "Exportar")
        self.addSubInterface(self.tab_puntajes, "Puntajes")
        self.addSubInterface(self.tab_avanzado, "Avanzado")

        self.pivot.currentItemChanged.connect(
            lambda tag: self.stacked_widget.setCurrentWidget(self.findChild(QFrame, tag))
        )
        
        # Configuración inicial
        self.stacked_widget.setCurrentWidget(self.tab_extraer)
        self.pivot.setCurrentItem("Extraer")

    def addSubInterface(self, widget, text):
        widget.setObjectName(text)
        self.pivot.addItem(routeKey=text, text=text)
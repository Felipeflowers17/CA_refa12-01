import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from src.gui.view.update_view import UpdateView

from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon as FIF
)

# --- IMPORTACIONES CORREGIDAS ---
from src.controllers.main_controller import MainController
from src.gui.view.listings_view import ListingsView
from src.gui.view.tools_view import ToolsView

# Importamos el Placeholder desde el nuevo archivo neutral
from src.gui.componentes.common_widgets import PlaceholderView

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        
        # 1. Inicializar Lógica
        self.controller = MainController()

        # 2. Configuración Ventana
        self.setWindowTitle("Monitor CA - Gestión Licitaciones")
        self.resize(1200, 800)
        
        # 3. Crear Interfaces (Vistas REALES)
        self.candidatas_interface = ListingsView(self.controller, "candidatas")
        self.seguimiento_interface = ListingsView(self.controller, "seguimiento")
        self.ofertadas_interface = ListingsView(self.controller, "ofertadas")
        
        # Placeholders para lo que aun no hacemos
        self.update_interface = UpdateView(self.controller)
        self.tools_interface = ToolsView(self.controller)
        self.home_interface = PlaceholderView("Dashboard")

        # 4. Inicializar Navegación (igual que antes)
        self.init_navigation()

    def init_navigation(self):
        # A. Home (Opcional, dashboard)
        self.addSubInterface(
            self.home_interface, FIF.HOME, "Inicio"
        )

        # B. Bloque Principal (Tablas)
        self.navigationInterface.addSeparator()
        
        self.addSubInterface(
            self.candidatas_interface, FIF.SEARCH, "Candidatas",
            NavigationItemPosition.SCROLL
        )
        self.addSubInterface(
            self.seguimiento_interface, FIF.HEART, "Seguimiento",
            NavigationItemPosition.SCROLL
        )
        self.addSubInterface(
            self.ofertadas_interface, FIF.SHOPPING_CART, "Ofertadas",
            NavigationItemPosition.SCROLL
        )

        # C. Bloque Herramientas
        self.navigationInterface.addSeparator()
        
        self.addSubInterface(
            self.update_interface, FIF.SYNC, "Actualizar info pestañas",
            NavigationItemPosition.SCROLL
        )
        self.addSubInterface(
            self.tools_interface, FIF.DEVELOPER_TOOLS, "Herramientas",
            NavigationItemPosition.SCROLL
        )

        # D. Footer (Settings)
        self.addSubInterface(
            PlaceholderView("Configuración"), FIF.SETTING, "Configuración", 
            NavigationItemPosition.BOTTOM
        )

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
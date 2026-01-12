# src/gui/views/listings_view.py
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QMenu
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QDesktopServices
from src.gui.componentes.note_dialog import NoteDialog
from src.gui.componentes.detail_drawer import DetailDrawer

from qfluentwidgets import (
    PrimaryPushButton, SearchLineEdit, FluentIcon as FIF, 
    StateToolTip, InfoBar, InfoBarPosition
)

from src.gui.componentes.table_widget import LicitacionesTable
from config.config import URL_BASE_WEB, URL_BASE_API # Para construir url ficha web

class ListingsView(QFrame):
    def __init__(self, controller, view_type: str, parent=None):
        """
        view_type: 'candidatas', 'seguimiento', 'ofertadas'
        """
        super().__init__(parent)
        self.controller = controller
        self.view_type = view_type
        self.setObjectName(view_type) # Para estilos CSS si fuera necesario

        # Layout Principal
        self.v_layout = QVBoxLayout(self)
        self.v_layout.setContentsMargins(20, 20, 20, 20)
        self.v_layout.setSpacing(15)

        # 1. Barra Superior (Buscador y Botón Refrescar)
        self.h_layout = QHBoxLayout()
        
        self.search_box = SearchLineEdit(self)
        self.search_box.setPlaceholderText("Buscar por código, nombre u organismo...")
        self.search_box.textChanged.connect(self.filtrar_tabla)
        
        self.btn_refresh = PrimaryPushButton("Refrescar Tablas", self)
        self.btn_refresh.setIcon(FIF.SYNC)
        self.btn_refresh.clicked.connect(self.cargar_datos)

        self.h_layout.addWidget(self.search_box)
        self.h_layout.addWidget(self.btn_refresh)
        
        self.v_layout.addLayout(self.h_layout)

        # 2. Tabla
        self.table = LicitacionesTable(self)
        self.table.row_double_clicked.connect(self.abrir_detalle)
        self.table.custom_context_menu_requested.connect(self.mostrar_menu_contextual)
        
        self.v_layout.addWidget(self.table)

        # 3. Cargar datos iniciales
        self.cargar_datos()

    def cargar_datos(self):
        """Pide al controlador los datos frescos y actualiza la tabla."""
        # Mostrar loading ligero
        self.btn_refresh.setEnabled(False)
        try:
            datos = self.controller.get_data_for_view(self.view_type)
            self.table.set_data(datos)
        except Exception as e:
            InfoBar.error(
                title="Error de Carga",
                content=f"No se pudieron cargar los datos: {e}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                parent=self
            )
        finally:
            self.btn_refresh.setEnabled(True)

    def filtrar_tabla(self, texto):
        """Filtro rápido en cliente (sin ir a BD)."""
        texto = texto.lower()
        for i in range(self.table.rowCount()):
            ocultar = True
            # Buscamos en Código (col 2), Organismo (col 3) y Nombre (col 4)
            for col_idx in [2, 3, 4]:
                item = self.table.item(i, col_idx)
                if item and texto in item.text().lower():
                    ocultar = False
                    break
            self.table.setRowHidden(i, ocultar)

    def abrir_detalle(self, codigo_ca: str):
        data = self.controller.get_licitacion_detail(codigo_ca)
        if data:
            # Creamos el diálogo (Notar el cambio a DetailDrawer)
            drawer = DetailDrawer(parent=self.window())
            drawer.set_data(data)
            
            # USAR .exec() PARA DIALOGOS MODALES
            drawer.exec()  
        else:
            print(f"Error: No se encontraron detalles para {codigo_ca}")

    def mostrar_menu_contextual(self, row_data: dict, global_pos):
        menu = QMenu(self)
        codigo = row_data.get('codigo_ca')

        # Acción Común: Ver en Web
        action_web = QAction(FIF.GLOBE.icon(), "Ver ficha web", self)
        action_web.triggered.connect(lambda: self._abrir_web(codigo))
        
        # --- NUEVO: Acción Común: Agregar/Editar Nota ---
        action_nota = QAction(FIF.EDIT.icon(), "Agregar/Editar nota", self)
        action_nota.triggered.connect(lambda: self._gestionar_nota(codigo))
        # -----------------------------------------------

        menu.addAction(action_web)
        menu.addAction(action_nota) # Ahora aparece en TODAS
        menu.addSeparator()

        if self.view_type == "candidatas":
            action_seg = QAction(FIF.HEART.icon(), "Seguir (Favorito)", self)
            action_seg.triggered.connect(lambda: self._mover_seguimiento(codigo))
            menu.addAction(action_seg)
            
        elif self.view_type == "seguimiento":
            action_ofertar = QAction(FIF.SHOPPING_CART.icon(), "Mover a Ofertada", self)
            action_ofertar.triggered.connect(lambda: self._mover_ofertar(codigo))
            
            action_unfollow = QAction(FIF.DELETE.icon(), "Dejar de seguir", self)
            action_unfollow.triggered.connect(lambda: self._dejar_seguir(codigo))
            
            menu.addAction(action_ofertar)
            menu.addAction(action_unfollow)
            
        elif self.view_type == "ofertadas":
            action_undo = QAction(FIF.RETURN.icon(), "Mover a Seguimiento", self)
            action_undo.triggered.connect(lambda: self._mover_seguimiento(codigo))
            menu.addAction(action_undo)

        menu.exec(global_pos)

    # --- ACCIONES DEL MENÚ ---

    def _abrir_web(self, codigo):
        url = f"{URL_BASE_WEB}/ficha?code={codigo}" # Usamos constante de config.py
        QDesktopServices.openUrl(QUrl(url))

    def _mover_seguimiento(self, codigo):
        self.controller.move_to_seguimiento(codigo)
        self.cargar_datos() # Refrescar para ver cambios
        InfoBar.success("Movido a Seguimiento", f"{codigo} ahora es favorita.", parent=self)

    def _mover_ofertar(self, codigo):
        self.controller.move_to_ofertar(codigo)
        self.cargar_datos()
        InfoBar.success("Movido a Ofertadas", f"{codigo} marcada como ofertada.", parent=self)

    def _dejar_seguir(self, codigo):
        self.controller.stop_following(codigo)
        self.cargar_datos() # Desaparecerá de la lista
        InfoBar.warning("Eliminado", f"{codigo} ya no está en seguimiento.", parent=self)

    def _gestionar_nota(self, codigo):
        # 1. Obtener nota actual
        nota_actual = self.controller.get_note(codigo)

        # 2. Abrir diálogo
        dlg = NoteDialog(codigo, nota_actual, parent=self.window())
        if dlg.exec():
            # 3. Guardar si el usuario aceptó
            nueva_nota = dlg.get_text()
            self.controller.save_note(codigo, nueva_nota)
            InfoBar.success("Nota Guardada", f"Nota actualizada para {codigo}", parent=self)
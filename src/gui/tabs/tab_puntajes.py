# src/gui/tabs/tab_puntajes.py

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QHeaderView, 
    QTableWidgetItem, QMenu, QWidget, QSplitter, 
    QListWidget, QComboBox, QLabel, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt
from qfluentwidgets import (
    SegmentedWidget, TableWidget, PrimaryPushButton, SearchLineEdit, 
    FluentIcon as FIF, InfoBar, SpinBox, MessageBoxBase, 
    SubtitleLabel, CheckBox
)

# Importamos el Delegate visual para los Badges de colores
from src.gui.componentes.delegates import ScoreBadgeDelegate

# --- DIÁLOGO EDICIÓN KEYWORD (Agregar/Editar) ---
class KeywordDialog(MessageBoxBase):
    def __init__(self, categories_list, parent=None, current_data=None):
        super().__init__(parent)
        
        mode_text = "Editar" if current_data else "Agregar"
        self.lbl_title = SubtitleLabel(f"{mode_text} Palabra Clave", self)
        self.viewLayout.addWidget(self.lbl_title)
        self.viewLayout.setSpacing(15)
        
        # 1. Inputs Principales
        self.txt_keyword = SearchLineEdit(self)
        self.txt_keyword.setPlaceholderText("Ej: insumos medicos")
        
        self.combo_cat = QComboBox()
        self.combo_cat.setEditable(True)
        self.combo_cat.addItems(categories_list)
        self.combo_cat.setPlaceholderText("Selecciona o escribe nueva...")
        
        # 2. Configuración de Puntajes
        self.spin_title = SpinBox(); self.spin_title.setRange(-100, 100)
        self.chk_title = CheckBox("Título", self)
        
        self.spin_desc = SpinBox(); self.spin_desc.setRange(-100, 100)
        self.chk_desc = CheckBox("Descripción", self)

        self.spin_prod = SpinBox(); self.spin_prod.setRange(-100, 100)
        self.chk_prod = CheckBox("Productos", self)

        # 3. Lógica de Pre-llenado (Si es edición)
        if current_data:
            self.txt_keyword.setText(current_data['keyword'])
            self.combo_cat.setCurrentText(current_data['category'])
            
            p_t = current_data['p_title']
            self.spin_title.setValue(p_t)
            self.chk_title.setChecked(p_t != 0)
            
            p_d = current_data['p_desc']
            self.spin_desc.setValue(p_d)
            self.chk_desc.setChecked(p_d != 0)
            
            p_p = current_data['p_prod']
            self.spin_prod.setValue(p_p)
            self.chk_prod.setChecked(p_p != 0)
        else:
            # Valores por defecto
            self.spin_title.setValue(5); self.chk_title.setChecked(True)
            self.spin_desc.setValue(2); self.chk_desc.setChecked(True)
            self.spin_prod.setValue(0); self.chk_prod.setChecked(False)

        # Layouts Internos
        row1 = QHBoxLayout(); row1.addWidget(self.chk_title); row1.addWidget(self.spin_title)
        row2 = QHBoxLayout(); row2.addWidget(self.chk_desc); row2.addWidget(self.spin_desc)
        row3 = QHBoxLayout(); row3.addWidget(self.chk_prod); row3.addWidget(self.spin_prod)

        self.viewLayout.addWidget(QLabel("Palabra:"))
        self.viewLayout.addWidget(self.txt_keyword)
        self.viewLayout.addWidget(QLabel("Categoría (Familia):"))
        self.viewLayout.addWidget(self.combo_cat)
        
        self.viewLayout.addWidget(QLabel("Asignar Puntajes:"))
        self.viewLayout.addLayout(row1)
        self.viewLayout.addLayout(row2)
        self.viewLayout.addLayout(row3)

        self.yesButton.setText("Guardar")
        self.cancelButton.setText("Cancelar")
        
        self.widget.setMinimumWidth(380)

    def get_data(self):
        return {
            "keyword": self.txt_keyword.text().strip(),
            "category": self.combo_cat.currentText().strip(),
            "p_title": self.spin_title.value() if self.chk_title.isChecked() else 0,
            "p_desc": self.spin_desc.value() if self.chk_desc.isChecked() else 0,
            "p_prod": self.spin_prod.value() if self.chk_prod.isChecked() else 0
        }

# --- DIÁLOGO PUNTAJE ORGANISMO ---
class ScoreDialog(MessageBoxBase):
    def __init__(self, org_name, current_score=5, mode="prioritario", parent=None):
        super().__init__(parent)
        
        title_text = "Definir Importancia" if mode.lower() == "prioritario" else "Definir Penalización"
        self.lbl_title = SubtitleLabel(title_text, self)
        self.viewLayout.addWidget(self.lbl_title)
        
        self.lbl_org = QLabel(org_name, self)
        self.lbl_org.setWordWrap(True)
        self.lbl_org.setStyleSheet("font-size: 14px; color: #555; margin-bottom: 10px;")
        
        self.spin_score = SpinBox()
        self.spin_score.setRange(-1000, 1000)
        self.spin_score.setValue(current_score)
        
        self.viewLayout.addWidget(self.lbl_org)
        self.viewLayout.addWidget(QLabel("Puntos:"))
        self.viewLayout.addWidget(self.spin_score)
        
        self.yesButton.setText("Guardar")
        self.cancelButton.setText("Cancelar")


# --- CLASE PRINCIPAL DE LA PESTAÑA ---
class TabPuntajes(QFrame):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        
        self.v_layout = QVBoxLayout(self)
        self.v_layout.setContentsMargins(20, 20, 20, 20)
        self.v_layout.setSpacing(10)
        
        self.current_tag = "org" 

        # --- HEADER (Navegación + Herramientas) ---
        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0,0,0,0)
        header_layout.setSpacing(10)

        # 1. Selector de Vista (Alineado a la izquierda)
        self.pivot = SegmentedWidget(self)
        self.pivot.addItem("org", "Organismos")
        self.pivot.addItem("kw", "Palabras Clave")
        self.pivot.setCurrentItem("org")
        self.pivot.currentItemChanged.connect(self.switch_view)
        
        h_nav = QHBoxLayout()
        h_nav.addWidget(self.pivot)
        h_nav.addStretch() 
        header_layout.addLayout(h_nav)

        # 2. Barra de Herramientas
        h_tools = QHBoxLayout()
        self.search_box = SearchLineEdit(self)
        self.search_box.setPlaceholderText("Buscar Organismo...")
        self.search_box.setFixedWidth(300)
        self.search_box.textChanged.connect(self.filter_table_text)
        
        self.btn_add = PrimaryPushButton(FIF.ADD, "Agregar Palabra", self)
        self.btn_add.clicked.connect(self.open_add_keyword)
        self.btn_add.hide() 
        
        self.btn_recalc = PrimaryPushButton(FIF.SYNC, "Recalcular Todo", self)
        self.btn_recalc.clicked.connect(self.ejecutar_recalculo)
        
        h_tools.addWidget(self.search_box)
        h_tools.addWidget(self.btn_add)
        h_tools.addStretch()
        h_tools.addWidget(self.btn_recalc)
        
        header_layout.addLayout(h_tools)
        self.v_layout.addWidget(header_container)

        # --- CONTENIDO PRINCIPAL ---
        
        # A. VISTA ORGANISMOS (Splitter: Sectores | Tabla)
        self.container_org = QWidget()
        self.layout_org_split = QHBoxLayout(self.container_org)
        self.layout_org_split.setContentsMargins(0, 0, 0, 0)

        # Panel Izquierdo: Lista de Sectores
        self.list_sectors = QListWidget()
        self.list_sectors.setFixedWidth(220)
        self.list_sectors.itemClicked.connect(self.filter_by_sector)
        self.list_sectors.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_sectors.customContextMenuRequested.connect(self.menu_sector)

        # Panel Derecho: Tabla Organismos
        self.table_org = TableWidget(self)
        self.setup_table_org()

        # Splitter Org
        self.splitter_org = QSplitter(Qt.Horizontal)
        self.splitter_org.addWidget(self.list_sectors)
        self.splitter_org.addWidget(self.table_org)
        self.splitter_org.setStretchFactor(1, 1) # Tabla ocupa espacio restante

        self.layout_org_split.addWidget(self.splitter_org)

        # B. VISTA KEYWORDS (Splitter: Categorías | Tabla)
        self.container_kw = QWidget()
        self.layout_kw_split = QHBoxLayout(self.container_kw)
        self.layout_kw_split.setContentsMargins(0, 0, 0, 0)
        
        # Panel Izquierdo: Lista de Categorías
        self.list_categories = QListWidget()
        self.list_categories.setFixedWidth(220)
        self.list_categories.itemClicked.connect(self.filter_by_category)
        self.list_categories.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_categories.customContextMenuRequested.connect(self.menu_category)
        
        # Panel Derecho: Tabla Keywords
        self.table_kw = TableWidget()
        self.setup_table_kw()
        
        # Splitter KW
        self.splitter_kw = QSplitter(Qt.Horizontal)
        self.splitter_kw.addWidget(self.list_categories)
        self.splitter_kw.addWidget(self.table_kw)
        self.splitter_kw.setStretchFactor(1, 1)
        
        self.layout_kw_split.addWidget(self.splitter_kw)
        
        # Agregamos ambos contenedores al layout principal
        self.v_layout.addWidget(self.container_org, 1)
        self.v_layout.addWidget(self.container_kw, 1)
        
        # Estado Inicial
        self.container_kw.hide()
        self.load_sectors_sidebar()
        self.load_organisms()

    # --- CONFIGURACIÓN DE TABLAS ---

    def setup_table_org(self):
        # Columnas actualizadas con "Sector"
        headers = ["ID", "Organismo", "Sector", "Estado", "Puntos", "Es Nuevo"]
        self.table_org.setColumnCount(len(headers))
        self.table_org.setHorizontalHeaderLabels(headers)
        self.table_org.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_org.verticalHeader().hide()
        
        # Anchos
        self.table_org.setColumnWidth(0, 40)
        self.table_org.setColumnWidth(2, 140) # Columna Sector

        self.table_org.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_org.customContextMenuRequested.connect(self.menu_org)

    def setup_table_kw(self):
        headers = ["ID", "Palabra Clave", "Categoría", "Título", "Desc.", "Prod."]
        self.table_kw.setColumnCount(len(headers))
        self.table_kw.setHorizontalHeaderLabels(headers)
        self.table_kw.verticalHeader().hide()
        
        self.table_kw.setColumnWidth(0, 40)
        self.table_kw.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_kw.setColumnWidth(2, 130)
        
        # Delegate Visual (Badges de Colores)
        delegate = ScoreBadgeDelegate(self.table_kw)
        self.table_kw.setItemDelegateForColumn(3, delegate)
        self.table_kw.setItemDelegateForColumn(4, delegate)
        self.table_kw.setItemDelegateForColumn(5, delegate)
        
        # Menú Contextual
        self.table_kw.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_kw.customContextMenuRequested.connect(self.menu_keyword)

    # --- LÓGICA DE NAVEGACIÓN (SWITCH) ---

    def switch_view(self, tag):
        self.current_tag = tag
        self.search_box.clear()
        
        if tag == "org":
            self.container_kw.hide()
            self.btn_add.hide()
            self.container_org.show() # Mostrar vista Organismos
            self.search_box.setPlaceholderText("Buscar Organismo...")
            self.load_sectors_sidebar()
            self.load_organisms(self._get_current_sector_filter())
        else:
            self.container_org.hide()
            self.container_kw.show()  # Mostrar vista Keywords
            self.btn_add.show()
            self.search_box.setPlaceholderText("Buscar Palabra Clave...")
            self.load_categories_sidebar()
            self.load_keywords(None) 

    # --- CARGADORES DE DATOS ORGANISMOS (SECTORES) ---

    def load_sectors_sidebar(self):
        """Carga la lista de sectores."""
        current = self.list_sectors.currentItem()
        curr_text = current.text() if current else "Todas"
        
        self.list_sectors.clear()
        self.list_sectors.addItem("Todas")
        self.list_sectors.addItem("General")
        
        # Cargar sectores de usuario
        sectores = self.controller.get_sectors()
        for s in sectores:
            if s and s not in ["Todas", "General"]:
                self.list_sectors.addItem(s)
                
        # Restaurar selección
        items = self.list_sectors.findItems(curr_text, Qt.MatchExactly)
        if items: self.list_sectors.setCurrentItem(items[0])
        else: self.list_sectors.setCurrentRow(0)

    def filter_by_sector(self, item):
        sector_name = item.text()
        filter_val = None if sector_name == "Todas" else sector_name
        self.load_organisms(filter_val)

    def load_organisms(self, sector_filter=None):
        data = self.controller.get_all_organisms_config(sector_filter)
        
        self.table_org.setRowCount(len(data))
        self.table_org.setSortingEnabled(False)
        for r, item in enumerate(data):
            self.table_org.setItem(r, 0, QTableWidgetItem(str(item['ID'])))
            self.table_org.setItem(r, 1, QTableWidgetItem(item['Organismo']))
            self.table_org.setItem(r, 2, QTableWidgetItem(item['Sector'])) # Nueva Columna
            
            estado_txt = item['Estado']
            estado_item = QTableWidgetItem(estado_txt)
            if estado_txt == "Prioritario":
                estado_item.setForeground(Qt.darkGreen)
            elif estado_txt == "No Deseado":
                estado_item.setForeground(Qt.red)
                
            self.table_org.setItem(r, 3, estado_item)
            self.table_org.setItem(r, 4, QTableWidgetItem(str(item['Puntos Asignados'])))
            self.table_org.setItem(r, 5, QTableWidgetItem(item['Es Nuevo']))
        self.table_org.setSortingEnabled(True)

    # --- CARGADORES DE DATOS KEYWORDS (CATEGORÍAS) ---

    def load_categories_sidebar(self):
        """Carga categorías sin duplicados."""
        current = self.list_categories.currentItem()
        curr_text = current.text() if current else "Todas"

        self.list_categories.clear()
        self.list_categories.addItem("Todas")
        self.list_categories.addItem("Sin Categoría")
        
        cats = self.controller.get_categories()
        for c in cats:
            if c and c not in ["Todas", "Sin Categoría"]:
                self.list_categories.addItem(c)
        
        items = self.list_categories.findItems(curr_text, Qt.MatchExactly)
        if items: self.list_categories.setCurrentItem(items[0])
        else: self.list_categories.setCurrentRow(0)

    def filter_by_category(self, item):
        cat_text = item.text()
        filter_val = None if cat_text == "Todas" else cat_text
        self.load_keywords(filter_val)

    def load_keywords(self, category_filter=None):
        data = self.controller.get_keywords(category_filter)
        self.table_kw.setRowCount(len(data))
        self.table_kw.setSortingEnabled(False)
        for r, item in enumerate(data):
            self.table_kw.setItem(r, 0, QTableWidgetItem(str(item['ID'])))
            self.table_kw.setItem(r, 1, QTableWidgetItem(item['Palabra Clave']))
            self.table_kw.setItem(r, 2, QTableWidgetItem(item['Categoría']))
            self.table_kw.setItem(r, 3, QTableWidgetItem(str(item['Puntos Título'])))
            self.table_kw.setItem(r, 4, QTableWidgetItem(str(item['Puntos Descripción'])))
            self.table_kw.setItem(r, 5, QTableWidgetItem(str(item['Puntos Productos'])))
        self.table_kw.setSortingEnabled(True)

    def _refresh_kw_view(self):
        self.load_categories_sidebar()
        curr = self.list_categories.currentItem()
        cat = curr.text() if curr and curr.text() != "Todas" else None
        self.load_keywords(cat)

    # --- MENÚS CONTEXTUALES (ORGANISMOS/SECTORES) ---

    def menu_sector(self, pos):
        item = self.list_sectors.itemAt(pos)
        if not item: return
        sec_name = item.text()
        
        if sec_name in ["Todas", "General"]: return # Proteger sistemas
        
        menu = QMenu(self)
        act_rename = menu.addAction(FIF.EDIT.icon(), "Renombrar Sector")
        act_del = menu.addAction(FIF.DELETE.icon(), "Eliminar Sector")
        
        action = menu.exec(self.list_sectors.mapToGlobal(pos))
        
        if action == act_rename:
            new_name, ok = QInputDialog.getText(self, "Renombrar", "Nuevo nombre:", text=sec_name)
            if ok and new_name and new_name != sec_name:
                self.controller.rename_sector(sec_name, new_name)
                self.load_sectors_sidebar()
                # Si el filtro activo era este, refrescar la tabla
                if self._get_current_sector_filter() == sec_name:
                    self.filter_by_sector(self.list_sectors.findItems(new_name, Qt.MatchExactly)[0])
                InfoBar.success("Renombrado", "Sector actualizado.", parent=self)
                
        elif action == act_del:
            reply = QMessageBox.question(self, "Eliminar", 
                f"¿Eliminar sector '{sec_name}'?\nLos organismos pasarán a 'General'.",
                QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.controller.delete_sector(sec_name)
                self.load_sectors_sidebar()
                self.load_organisms(None)
                InfoBar.success("Eliminado", "Sector borrado.", parent=self)

    def menu_org(self, pos):
        item = self.table_org.itemAt(pos)
        if not item: return
        row = item.row()
        org_id = int(self.table_org.item(row, 0).text())
        org_name = self.table_org.item(row, 1).text()
        
        menu = QMenu(self)
        
        # Submenú Puntuación
        menu_score = menu.addMenu(FIF.EDIT.icon(), "Cambiar Puntuación")
        act_prio = menu_score.addAction("Marcar Prioritario (+)")
        act_undesired = menu_score.addAction("Marcar No Deseado (-)")
        act_neutral = menu_score.addAction("Marcar Neutro (0)")
        
        menu.addSeparator()
        
        # Acción Mover Sector
        act_move = menu.addAction(FIF.TAG.icon(), "Mover a Sector...")
        
        action = menu.exec(self.table_org.mapToGlobal(pos))
        
        if action == act_prio: self.open_score_dialog(org_id, org_name, 5, "PRIORITARIO")
        elif action == act_undesired: self.open_score_dialog(org_id, org_name, -100, "NO_DESEADO")
        elif action == act_neutral: 
            self.controller.set_organism_rule(org_id, "neutro", 0)
            self.load_organisms(self._get_current_sector_filter())

        elif action == act_move:
            self.prompt_move_sector(org_id, org_name)

    def prompt_move_sector(self, org_id, org_name):
        sectors = self.controller.get_sectors()
        # Añadimos opción especial para crear uno nuevo
        items = sectors + ["(Crear Nuevo...)"]
        
        item, ok = QInputDialog.getItem(self, "Mover Organismo", 
                                      f"Selecciona sector para:\n{org_name}", 
                                      items, 0, True)
        if ok and item:
            sector_final = item
            if item == "(Crear Nuevo...)":
                text, ok2 = QInputDialog.getText(self, "Nuevo Sector", "Nombre del Sector:")
                if ok2 and text: sector_final = text
                else: return
            
            self.controller.set_organism_sector(org_id, sector_final)
            self.load_sectors_sidebar()
            self.load_organisms(self._get_current_sector_filter())
            InfoBar.success("Movido", "Organismo actualizado.", parent=self)

    # --- MENÚS CONTEXTUALES (KEYWORDS) ---

    def menu_category(self, pos):
        item = self.list_categories.itemAt(pos)
        if not item: return
        cat_name = item.text()
        
        if cat_name in ["Todas", "Sin Categoría"]: return 
        
        menu = QMenu(self)
        act_rename = menu.addAction(FIF.EDIT.icon(), "Renombrar Categoría")
        act_delete_all = menu.addAction(FIF.DELETE.icon(), "Eliminar Categoría")
        
        action = menu.exec(self.list_categories.mapToGlobal(pos))
        
        if action == act_rename:
            new_name, ok = QInputDialog.getText(self, "Renombrar", "Nuevo nombre:", text=cat_name)
            if ok and new_name and new_name not in ["Todas", "Sin Categoría"]:
                self.controller.rename_category(cat_name, new_name)
                self._refresh_kw_view()
                InfoBar.success("Renombrado", "Categoría actualizada.", parent=self)
                
        elif action == act_delete_all:
            reply = QMessageBox.question(self, "Eliminar", 
                f"¿Eliminar '{cat_name}'?\nLas palabras pasarán a 'Sin Categoría'.",
                QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.controller.rename_category(cat_name, "Sin Categoría") 
                self._refresh_kw_view()
                InfoBar.warning("Eliminado", f"Categoría '{cat_name}' eliminada.", parent=self)

    def menu_keyword(self, pos):
        item = self.table_kw.itemAt(pos)
        if not item: return
        
        menu = QMenu(self)
        act_edit = menu.addAction(FIF.EDIT.icon(), "Editar")
        act_del = menu.addAction(FIF.DELETE.icon(), "Eliminar")
        
        action = menu.exec(self.table_kw.mapToGlobal(pos))
        
        if action == act_edit:
            self.edit_keyword_prompt(item)
        elif action == act_del:
            self.delete_keyword_logic(item.row())

    # --- ACCIONES CRUD (KEYWORDS) ---

    def open_add_keyword(self):
        cats = self.controller.get_categories()
        dlg = KeywordDialog(cats, self)
        if dlg.exec():
            data = dlg.get_data()
            if data['keyword']:
                try:
                    self.controller.add_keyword(
                        data['keyword'], 
                        data['p_title'], data['p_desc'], data['p_prod'],
                        data['category']
                    )
                    self._refresh_kw_view()
                    InfoBar.success("Agregada", f"Palabra '{data['keyword']}' guardada.", parent=self)
                except Exception as e:
                    InfoBar.error("Error", str(e), parent=self)

    def edit_keyword_prompt(self, item):
        row = item.row()
        kw_id = int(self.table_kw.item(row, 0).text())
        
        current_data = {
            'keyword': self.table_kw.item(row, 1).text(),
            'category': self.table_kw.item(row, 2).text(),
            'p_title': int(self.table_kw.item(row, 3).text()),
            'p_desc': int(self.table_kw.item(row, 4).text()),
            'p_prod': int(self.table_kw.item(row, 5).text())
        }
        
        cats = self.controller.get_categories()
        dlg = KeywordDialog(cats, self, current_data=current_data)
        
        if dlg.exec():
            data = dlg.get_data()
            if data['keyword']:
                try:
                    self.controller.update_keyword(
                        kw_id,
                        data['keyword'], 
                        data['p_title'], data['p_desc'], data['p_prod'],
                        data['category']
                    )
                    self._refresh_kw_view()
                    InfoBar.success("Actualizada", f"Palabra '{data['keyword']}' editada.", parent=self)
                except Exception as e:
                    InfoBar.error("Error", str(e), parent=self)

    def delete_keyword_logic(self, row):
        kw_id = int(self.table_kw.item(row, 0).text())
        kw_text = self.table_kw.item(row, 1).text()
        self.controller.delete_keyword(kw_id)
        self._refresh_kw_view()
        InfoBar.warning("Eliminada", f"Palabra '{kw_text}' borrada.", parent=self)

    # --- UTILIDADES ---

    def _get_current_sector_filter(self):
        curr = self.list_sectors.currentItem()
        if not curr or curr.text() == "Todas": return None
        return curr.text()

    def filter_table_text(self, text):
        target = self.table_org if self.current_tag == "org" else self.table_kw
        text = text.lower()
        for i in range(target.rowCount()):
            match = False
            item = target.item(i, 1) 
            if item and text in item.text().lower(): match = True
            target.setRowHidden(i, not match)

    def ejecutar_recalculo(self):
        self.btn_recalc.setEnabled(False)
        self.controller.recalcular_puntajes(lambda: [
            self.btn_recalc.setEnabled(True),
            InfoBar.success("Recálculo Completo", "Los puntajes se han actualizado.", parent=self)
        ])

    def open_score_dialog(self, org_id, name, default_score, mode):
        dlg = ScoreDialog(name, default_score, mode, self)
        if dlg.exec():
            score = dlg.spin_score.value()
            self.controller.set_organism_rule(org_id, mode, score)
            self.load_organisms(self._get_current_sector_filter())
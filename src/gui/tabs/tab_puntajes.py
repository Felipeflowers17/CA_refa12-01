from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QHeaderView, 
                               QTableWidgetItem, QDialog, QLabel, QMenu, QWidget)
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import (
    SegmentedWidget, TableWidget, PrimaryPushButton, SearchLineEdit, 
    FluentIcon as FIF, InfoBar, SpinBox, MessageBoxBase, SubtitleLabel, CheckBox
)

# --- DIÁLOGO EDICIÓN KEYWORD ---
class KeywordDialog(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 1. Título Manual (Corrección del error)
        self.lbl_title = SubtitleLabel("Editar Palabra Clave", self)
        self.viewLayout.addWidget(self.lbl_title)
        
        self.viewLayout.setSpacing(15)
        
        # Inputs
        self.txt_keyword = SearchLineEdit(self)
        self.txt_keyword.setPlaceholderText("Ej: insumos medicos")
        
        # Configuración de Pesos
        self.spin_title = SpinBox()
        self.spin_title.setRange(-100, 100); self.spin_title.setValue(5)
        self.chk_title = CheckBox("Título", self); self.chk_title.setChecked(True)
        
        self.spin_desc = SpinBox()
        self.spin_desc.setRange(-100, 100); self.spin_desc.setValue(2)
        self.chk_desc = CheckBox("Descripción", self); self.chk_desc.setChecked(True)

        self.spin_prod = SpinBox()
        self.spin_prod.setRange(-100, 100); self.spin_prod.setValue(0)
        self.chk_prod = CheckBox("Productos", self)

        # Layouts filas
        row1 = QHBoxLayout(); row1.addWidget(self.chk_title); row1.addWidget(self.spin_title)
        row2 = QHBoxLayout(); row2.addWidget(self.chk_desc); row2.addWidget(self.spin_desc)
        row3 = QHBoxLayout(); row3.addWidget(self.chk_prod); row3.addWidget(self.spin_prod)

        self.viewLayout.addWidget(self.txt_keyword)
        self.viewLayout.addWidget(QLabel("Asignar Puntajes:"))
        self.viewLayout.addLayout(row1)
        self.viewLayout.addLayout(row2)
        self.viewLayout.addLayout(row3)

        self.yesButton.setText("Guardar")
        self.cancelButton.setText("Cancelar")
        
        self.widget.setMinimumWidth(350)

    def get_data(self):
        return {
            "keyword": self.txt_keyword.text(),
            "p_title": self.spin_title.value() if self.chk_title.isChecked() else 0,
            "p_desc": self.spin_desc.value() if self.chk_desc.isChecked() else 0,
            "p_prod": self.spin_prod.value() if self.chk_prod.isChecked() else 0
        }
    
# --- DIÁLOGO PUNTAJE ORGANISMO ---
class ScoreDialog(MessageBoxBase):
    def __init__(self, org_name, current_score=5, mode="prioritario", parent=None):
        super().__init__(parent)
        if mode.lower() == "prioritario":
            title_text = "Definir Importancia"
        else:
            title_text = "Definir Penalización"
        
        # 1. Título Manual (Corrección del error)
        self.lbl_title = SubtitleLabel(title_text, self)
        self.viewLayout.addWidget(self.lbl_title)
        
        # Subtítulo con el nombre del organismo
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

# --- WIDGET PRINCIPAL ---
class TabPuntajes(QFrame):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.v_layout = QVBoxLayout(self)
        self.v_layout.setContentsMargins(20, 20, 20, 20)
        
        # Variable de estado para corregir el error de routeKey
        self.current_tag = "org" 

        # 1. Sub-Navegación
        self.pivot = SegmentedWidget(self)
        self.pivot.addItem("org", "Organismos")
        self.pivot.addItem("kw", "Palabras Clave")
        self.pivot.setCurrentItem("org")
        self.pivot.currentItemChanged.connect(self.switch_view)
        
        self.v_layout.addWidget(self.pivot)
        
        # 2. Barra de Herramientas
        h_tools = QHBoxLayout()
        self.search_box = SearchLineEdit(self)
        self.search_box.setPlaceholderText("Buscar Organismo...")
        self.search_box.setFixedWidth(300)
        self.search_box.textChanged.connect(self.filter_table)
        
        self.btn_add = PrimaryPushButton(FIF.ADD, "Agregar Palabra", self)
        self.btn_add.clicked.connect(self.open_add_keyword)
        self.btn_add.hide() # Solo visible en modo keywords
        
        self.btn_recalc = PrimaryPushButton(FIF.SYNC, "Recalcular Todo", self)
        self.btn_recalc.clicked.connect(self.ejecutar_recalculo)
        
        h_tools.addWidget(self.search_box)
        h_tools.addWidget(self.btn_add)
        h_tools.addStretch()
        h_tools.addWidget(self.btn_recalc)
        
        self.v_layout.addLayout(h_tools)

        # 3. Tablas
        self.table_org = TableWidget(self)
        self.setup_table_org()
        
        self.table_kw = TableWidget(self)
        self.setup_table_kw()
        self.table_kw.hide()
        
        self.v_layout.addWidget(self.table_org)
        self.v_layout.addWidget(self.table_kw)

        # Cargar datos iniciales
        self.load_organisms()

    def setup_table_org(self):
        headers = ["ID", "Organismo", "Estado", "Puntos", "Es Nuevo"]
        self.table_org.setColumnCount(len(headers))
        self.table_org.setHorizontalHeaderLabels(headers)
        self.table_org.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_org.verticalHeader().hide()
        self.table_org.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_org.customContextMenuRequested.connect(self.menu_org)

    def setup_table_kw(self):
        headers = ["ID", "Palabra Clave", "Pts. Título", "Pts. Desc.", "Pts. Prod."]
        self.table_kw.setColumnCount(len(headers))
        self.table_kw.setHorizontalHeaderLabels(headers)
        self.table_kw.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_kw.verticalHeader().hide()
        self.table_kw.itemDoubleClicked.connect(self.delete_keyword_prompt)

    def switch_view(self, tag):
        """Cambia la vista y actualiza la variable de estado."""
        self.current_tag = tag  # Actualizamos el tag
        self.search_box.clear()
        
        if tag == "org":
            self.table_kw.hide()
            self.btn_add.hide()
            self.table_org.show()
            self.search_box.setPlaceholderText("Buscar Organismo...")
            self.load_organisms()
        else:
            self.table_org.hide()
            self.table_kw.show()
            self.btn_add.show()
            self.search_box.setPlaceholderText("Buscar Palabra Clave...")
            self.load_keywords()

    # --- CARGA DE DATOS (Corrección de Claves) ---
    def load_organisms(self):
        data = self.controller.get_all_organisms_config()
        self.table_org.setRowCount(len(data))
        self.table_org.setSortingEnabled(False)
        for r, item in enumerate(data):
            # Usamos las claves originales en Mayúsculas
            self.table_org.setItem(r, 0, QTableWidgetItem(str(item['ID'])))
            self.table_org.setItem(r, 1, QTableWidgetItem(item['Organismo']))
            
            # Colorear estado
            estado_txt = item['Estado']
            estado_item = QTableWidgetItem(estado_txt)
            
            if estado_txt == "Prioritario":
                estado_item.setForeground(Qt.darkGreen)
            elif estado_txt == "No Deseado":
                estado_item.setForeground(Qt.red)
                
            self.table_org.setItem(r, 2, estado_item)
            self.table_org.setItem(r, 3, QTableWidgetItem(str(item['Puntos Asignados'])))
            self.table_org.setItem(r, 4, QTableWidgetItem(item['Es Nuevo']))
        self.table_org.setSortingEnabled(True)

    def load_keywords(self):
        data = self.controller.get_all_keywords()
        self.table_kw.setRowCount(len(data))
        self.table_kw.setSortingEnabled(False)
        for r, item in enumerate(data):
            # Usamos las claves originales
            self.table_kw.setItem(r, 0, QTableWidgetItem(str(item['ID'])))
            self.table_kw.setItem(r, 1, QTableWidgetItem(item['Palabra Clave']))
            self.table_kw.setItem(r, 2, QTableWidgetItem(str(item['Puntos Título'])))
            self.table_kw.setItem(r, 3, QTableWidgetItem(str(item['Puntos Descripción'])))
            self.table_kw.setItem(r, 4, QTableWidgetItem(str(item['Puntos Productos'])))
        self.table_kw.setSortingEnabled(True)

    # --- ACCIONES ORGANISMOS ---
    def menu_org(self, pos):
        item = self.table_org.itemAt(pos)
        if not item: return
        row = item.row()
        org_id = int(self.table_org.item(row, 0).text())
        org_name = self.table_org.item(row, 1).text()
        
        menu = QMenu(self)
        
        act_prio = menu.addAction(FIF.HEART.icon(), "Marcar Prioritario (+)")
        act_undesired = menu.addAction(FIF.DELETE.icon(), "Marcar No Deseado (-)")
        act_neutral = menu.addAction(FIF.CANCEL.icon(), "Marcar Neutro (0)")
        
        action = menu.exec(self.table_org.mapToGlobal(pos))
        
        if action == act_prio:
            # CAMBIO AQUÍ: "PRIORITARIO" en mayúsculas
            self.open_score_dialog(org_id, org_name, 5, "PRIORITARIO")
        elif action == act_undesired:
            # CAMBIO AQUÍ: "NO_DESEADO" en mayúsculas
            self.open_score_dialog(org_id, org_name, -100, "NO_DESEADO")
        elif action == act_neutral:
            self.controller.set_organism_rule(org_id, "neutro", 0)
            self.load_organisms()

    def open_score_dialog(self, org_id, name, default_score, mode):
        dlg = ScoreDialog(name, default_score, mode, self)
        if dlg.exec():
            score = dlg.spin_score.value()
            self.controller.set_organism_rule(org_id, mode, score)
            self.load_organisms()

    # --- ACCIONES KEYWORDS ---
    def open_add_keyword(self):
        dlg = KeywordDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            if data['keyword']:
                try:
                     self.controller.add_keyword(
                        data['keyword'], data['p_title'], data['p_desc'], data['p_prod']
                    )
                     self.load_keywords()
                     InfoBar.success("Agregada", f"Palabra '{data['keyword']}' guardada.", parent=self)
                except Exception as e:
                    InfoBar.error("Error", str(e), parent=self)

    def delete_keyword_prompt(self, item):
        row = item.row()
        kw_id = int(self.table_kw.item(row, 0).text())
        kw_text = self.table_kw.item(row, 1).text()
        
        # Eliminación directa (doble click)
        self.controller.delete_keyword(kw_id)
        self.load_keywords()
        InfoBar.warning("Eliminada", f"Palabra '{kw_text}' borrada.", parent=self)

    def filter_table(self, text):
        """Filtra las filas según el texto y la pestaña activa."""
        # Solución al error: Usamos self.current_tag en vez de routeKey()
        target = self.table_org if self.current_tag == "org" else self.table_kw
        
        text = text.lower()
        for i in range(target.rowCount()):
            match = False
            # Buscar en nombre (columna 1)
            item = target.item(i, 1)
            if item and text in item.text().lower():
                match = True
            target.setRowHidden(i, not match)

    def ejecutar_recalculo(self):
        self.btn_recalc.setEnabled(False)
        self.controller.recalcular_puntajes(lambda: [
            self.btn_recalc.setEnabled(True),
            InfoBar.success("Recálculo Completo", "Los puntajes se han actualizado.", parent=self)
        ])
from PySide6.QtWidgets import QFrame, QVBoxLayout, QFileDialog, QLabel
from qfluentwidgets import (
    CheckBox, PrimaryPushButton, FluentIcon as FIF, 
    InfoBar, CardWidget
)

class TabExportacion(QFrame):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        # --- Sección 1: Qué exportar ---
        card_data = CardWidget(self)
        l_data = QVBoxLayout(card_data)
        l_data.addWidget(QLabel("1. Selecciona los datos:", self))
        
        self.chk_backup = CheckBox("Base de Datos Completa (Backup)", self)
        self.chk_visible = CheckBox("Pestañas Visibles (Gestión)", self)
        self.chk_visible.setChecked(True) # Default lógico
        self.chk_rules = CheckBox("Keywords y Organismos (Reglas)", self)
        
        l_data.addWidget(self.chk_backup)
        l_data.addWidget(self.chk_visible)
        l_data.addWidget(self.chk_rules)
        layout.addWidget(card_data)

        # --- Sección 2: Formatos ---
        card_fmt = CardWidget(self)
        l_fmt = QVBoxLayout(card_fmt)
        l_fmt.addWidget(QLabel("2. Selecciona formatos:", self))
        
        self.chk_excel = CheckBox("Excel (.xlsx)", self)
        self.chk_excel.setChecked(True)
        self.chk_csv = CheckBox("CSV (.csv)", self)
        
        l_fmt.addWidget(self.chk_excel)
        l_fmt.addWidget(self.chk_csv)
        layout.addWidget(card_fmt)

        # --- Botón Acción ---
        self.btn_export = PrimaryPushButton("Generar Archivos", self)
        self.btn_export.setIcon(FIF.SAVE)
        self.btn_export.clicked.connect(self.iniciar_exportacion)
        layout.addWidget(self.btn_export)
        
        layout.addStretch()

    def iniciar_exportacion(self):
        # 1. Identificar qué TIPOS de datos se seleccionaron
        selected_types = []
        if self.chk_backup.isChecked(): selected_types.append("bd_full")
        if self.chk_visible.isChecked(): selected_types.append("tabs")
        if self.chk_rules.isChecked(): selected_types.append("config")
        
        if not selected_types:
            InfoBar.warning("Atención", "Selecciona al menos un tipo de dato.", parent=self)
            return

        # 2. Identificar qué FORMATOS se seleccionaron
        selected_formats = []
        if self.chk_excel.isChecked(): selected_formats.append("excel")
        if self.chk_csv.isChecked(): selected_formats.append("csv")

        if not selected_formats:
            InfoBar.warning("Atención", "Selecciona al menos un formato (Excel o CSV).", parent=self)
            return

        # 3. Construir la lista de tareas (Combinatoria: Tipos x Formatos)
        # Esto asegura que si marcas ambos, se generen ambas tareas.
        tasks = []
        for dtype in selected_types:
            for fmt in selected_formats:
                tasks.append({
                    "tipo": dtype,
                    "format": fmt
                })

        # 4. Seleccionar Carpeta
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Destino")
        if not folder:
            return

        # 5. Ejecutar
        self.btn_export.setEnabled(False)
        self.controller.run_export_task(
            tasks, folder,
            on_finish=self.fin_exportacion,
            on_error=self.error_exportacion
        )

    def fin_exportacion(self, resultados):
        self.btn_export.setEnabled(True)
        msg = "\n".join(resultados)
        InfoBar.success("Exportación Exitosa", f"Archivos guardados en:\n{msg}", duration=5000, parent=self)

    def error_exportacion(self, error):
        self.btn_export.setEnabled(True)
        InfoBar.error("Error", str(error), parent=self)
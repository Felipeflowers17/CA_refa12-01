from PySide6.QtWidgets import QFrame, QVBoxLayout, QFileDialog, QLabel
from qfluentwidgets import (
    CheckBox, PrimaryPushButton, FluentIcon as FIF, 
    InfoBar, CardWidget, BodyLabel
)

class TabExportacion(QFrame):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        # --- Sección 1: Qué exportar [cite: 12] ---
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

        # --- Sección 2: Formatos [cite: 13] ---
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
        # 1. Validar selección
        tasks = []
        if self.chk_backup.isChecked(): tasks.append({"tipo": "bd_full"})
        if self.chk_visible.isChecked(): tasks.append({"tipo": "tabs"})
        if self.chk_rules.isChecked(): tasks.append({"tipo": "config"})
        
        if not tasks:
            InfoBar.warning("Atención", "Selecciona al menos un tipo de dato.", parent=self)
            return

        # 2. Seleccionar Carpeta
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Destino")
        if not folder:
            return

        # 3. Configurar formato para cada tarea
        fmt = "excel" if self.chk_excel.isChecked() else "csv"
        # Si ambos están marcados, priorizamos Excel en esta implementación simple, 
        # o podríamos duplicar tareas. Por simplicidad del manual:
        for t in tasks: t["format"] = fmt

        # 4. Ejecutar
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
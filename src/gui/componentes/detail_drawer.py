from PySide6.QtWidgets import (QDialog, QVBoxLayout, QWidget, QScrollArea, 
                               QHBoxLayout, QLabel, QFrame)
from PySide6.QtCore import Qt
from qfluentwidgets import (
    SubtitleLabel, StrongBodyLabel, BodyLabel, CaptionLabel, 
    CardWidget, FluentIcon as FIF, IconWidget, PrimaryPushButton
)

class DetailDrawer(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuración de la Ventana (Modal)
        self.setWindowTitle("Ficha de Licitación")
        self.resize(600, 750)
        # Estilo limpio tipo "Tarjeta Flotante"
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff; 
            }
        """)

        # Layout Principal
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(16)

        # 1. Título Propio
        self.lbl_main_title = SubtitleLabel("Ficha de Licitación", self)
        self.layout.addWidget(self.lbl_main_title)

        # 2. Área de Scroll (Contenido)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        # Usamos QFrame.NoFrame para evitar borde feo
        self.scroll.setFrameShape(QFrame.NoFrame) 
        self.scroll.setStyleSheet("background: transparent;")
        
        self.container = QWidget()
        self.container.setStyleSheet(".QWidget { background-color: #ffffff; }")
        
        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setSpacing(15)
        self.content_layout.setContentsMargins(0, 0, 10, 0)

        # --- Componentes Internos ---
        
        # A. SECCIÓN DE NOTA (Mejora solicitada)
        # Se muestra primero si existe una nota
        self.lbl_nota_titulo = StrongBodyLabel("📝 Nota Personal:", self)
        self.lbl_nota_contenido = BodyLabel("", self)
        self.lbl_nota_contenido.setWordWrap(True)
        # Estilo rosado e itálico para resaltar
        self.lbl_nota_contenido.setStyleSheet("color: #d63384; font-style: italic; margin-bottom: 10px;")
        
        # Ocultamos por defecto (se activa en set_data)
        self.lbl_nota_titulo.hide()
        self.lbl_nota_contenido.hide()
        
        self.content_layout.addWidget(self.lbl_nota_titulo)
        self.content_layout.addWidget(self.lbl_nota_contenido)

        # B. Encabezado Código y Nombre
        self.lbl_codigo = CaptionLabel("", self)
        self.lbl_codigo.setStyleSheet("color: #666;")
        self.lbl_titulo = StrongBodyLabel("", self)
        self.lbl_titulo.setWordWrap(True)
        self.lbl_titulo.setStyleSheet("font-size: 16px; color: #333;")

        self.content_layout.addWidget(self.lbl_codigo)
        self.content_layout.addWidget(self.lbl_titulo)
        
        # C. Tarjeta Resumen
        self.card_info = CardWidget(self)
        l_card = QHBoxLayout(self.card_info)
        
        self.lbl_estado = BodyLabel()
        self.lbl_monto = StrongBodyLabel()
        self.lbl_monto.setStyleSheet("color: #009faa;") 
        
        l_card.addWidget(IconWidget(FIF.INFO))
        l_card.addWidget(self.lbl_estado)
        l_card.addStretch()
        # Usamos TAG en lugar de PRICE_TAG para evitar error de versión
        l_card.addWidget(IconWidget(FIF.TAG))
        l_card.addWidget(self.lbl_monto)
        
        self.content_layout.addWidget(self.card_info)

        # D. Secciones de Texto
        self.lbl_organismo = self._crear_seccion("Organismo Comprador")
        self.lbl_fechas = self._crear_seccion("Fechas Clave")
        self.lbl_ubicacion = self._crear_seccion("Ubicación y Plazos")
        
        # E. Descripción Larga
        self.content_layout.addWidget(StrongBodyLabel("Descripción Técnica"))
        self.lbl_descripcion = BodyLabel("Cargando...", self)
        self.lbl_descripcion.setWordWrap(True)
        self.lbl_descripcion.setStyleSheet("""
            background-color: #f9f9f9; 
            padding: 10px; 
            border-radius: 6px; 
            border: 1px solid #e5e5e5;
        """)
        self.content_layout.addWidget(self.lbl_descripcion)

        # F. Productos
        self.content_layout.addWidget(StrongBodyLabel("Productos Solicitados"))
        self.lbl_productos = BodyLabel("", self)
        self.lbl_productos.setWordWrap(True)
        self.content_layout.addWidget(self.lbl_productos)

        self.content_layout.addStretch()
        
        # Asignar contenedor al scroll
        self.scroll.setWidget(self.container)
        self.layout.addWidget(self.scroll)

        # 3. Botón Cerrar (Pie de página)
        self.btn_close = PrimaryPushButton("Cerrar", self)
        self.btn_close.setFixedWidth(120)
        self.btn_close.clicked.connect(self.accept) # Cierra el diálogo
        
        self.layout.addWidget(self.btn_close, 0, Qt.AlignRight)

    def _crear_seccion(self, titulo):
        self.content_layout.addWidget(StrongBodyLabel(titulo))
        lbl = BodyLabel("", self)
        lbl.setWordWrap(True)
        self.content_layout.addWidget(lbl)
        self.content_layout.addSpacing(5)
        return lbl

    def set_data(self, data: dict):
        """Rellena la UI con los datos."""
        
        # 1. Gestionar Nota (Mostrar/Ocultar)
        nota = data.get('nota_usuario')
        if nota and str(nota).strip():
            self.lbl_nota_titulo.show()
            self.lbl_nota_contenido.setText(nota)
            self.lbl_nota_contenido.show()
        else:
            self.lbl_nota_titulo.hide()
            self.lbl_nota_contenido.hide()

        # 2. Datos Generales
        self.lbl_codigo.setText(f"Código: {data.get('codigo_ca', 'N/A')}")
        self.lbl_titulo.setText(data.get('nombre', 'Sin Nombre'))
        self.lbl_estado.setText(data.get('estado_ca_texto', 'N/A'))
        
        monto = data.get('monto_clp')
        txt_monto = f"${int(monto):,}".replace(",", ".") if monto else "N/A"
        self.lbl_monto.setText(txt_monto)
        
        self.lbl_organismo.setText(data.get('organismo_nombre', 'No especificado'))
        
        # Fechas (Incluimos 2do llamado si existe)
        pub = str(data.get('fecha_publicacion') or "")
        cierre = str(data.get('fecha_cierre') or "")
        cierre2 = str(data.get('fecha_cierre_p2') or "")
        
        txt_fechas = f"Publicación: {pub}\nCierre: {cierre}"
        if cierre2 and cierre2 != "No aplica":
            txt_fechas += f"\nCierre 2° Llamado: {cierre2}"
            
        self.lbl_fechas.setText(txt_fechas)
        
        direc = data.get('direccion_entrega') or "No especificada"
        plazo = data.get('plazo_entrega')
        self.lbl_ubicacion.setText(f"Dirección: {direc}\nPlazo: {plazo if plazo else '?'} días")
        
        self.lbl_descripcion.setText(data.get('descripcion') or "Sin detalle.")
        
        prods = data.get('productos_solicitados')
        if isinstance(prods, list) and len(prods) > 0:
            items = []
            for p in prods:
                if isinstance(p, dict):
                    cant = p.get('cantidad', 1)
                    nom = p.get('nombre', '')
                    items.append(f"• ({cant}) {nom}")
            self.lbl_productos.setText("\n".join(items))
        else:
            self.lbl_productos.setText("No hay productos listados.")
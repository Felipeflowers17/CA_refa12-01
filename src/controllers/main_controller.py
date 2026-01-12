# src/controllers/main_controller.py
import logging
from src.db.session import SessionLocal
from src.db.db_service import DbService
from src.scraper.scraper_service import ServicioScraper
from src.logic.score_engine import MotorPuntajes
from src.logic.etl_service import ServicioEtl
from src.logic.excel_service import ServicioExcel
from src.utils.settings_manager import GestorConfiguracion
from src.controllers.worker import GenericWorker

# Configuración correcta del logger
logger = logging.getLogger(__name__)

class MainController:
    def __init__(self):
        # 1. Inicialización de Servicios Backend
        self.session_factory = SessionLocal
        self.db_service = DbService(self.session_factory)
        
        # Servicios de Lógica
        self.scraper_service = ServicioScraper()
        self.score_engine = MotorPuntajes(self.db_service)
        self.etl_service = ServicioEtl(
            self.db_service, 
            self.scraper_service, 
            self.score_engine
        )
        self.excel_service = ServicioExcel(self.db_service)
        
        # Configuración persistente
        self.settings_manager = GestorConfiguracion()
        
        # Cache de workers para evitar garbage collection prematuro
        self._current_worker = None
        self._maintenance_worker = None

        # Arrancar mantenimiento
        self._iniciar_mantenimiento_silencioso()

    def _iniciar_mantenimiento_silencioso(self):
        """
        Ejecuta tareas de limpieza (borrar viejas, cerrar vencidas) 
        en un hilo separado al iniciar la app.
        """
        logger.info("Iniciando protocolo de mantenimiento automático...")
        
        # Usamos el método que ya existe en tu ETL Service
        self._maintenance_worker = GenericWorker(self.etl_service.ejecutar_limpieza_automatica)
        
        # No conectamos señales visuales porque es silencioso.
        self._maintenance_worker.finished_success.connect(
            lambda: logger.info("Mantenimiento automático finalizado con éxito.")
        )
        self._maintenance_worker.finished_error.connect(
            lambda err: logger.error(f"Error en mantenimiento automático: {err}")
        )
        
        self._maintenance_worker.start()

    # --- GESTIÓN DE DATOS (TABLAS) ---
    
    def get_data_for_view(self, view_type: str):
        """Retorna la lista de diccionarios para las tablas."""
        if view_type == "candidatas":
            min_score = self.settings_manager.obtener_valor("umbral_puntaje_minimo") or 5
            return self.db_service.exportar_candidatas() 
        elif view_type == "seguimiento":
            return self.db_service.exportar_seguimiento()
        elif view_type == "ofertadas":
            return self.db_service.exportar_ofertadas()
        return []

    def get_licitacion_detail(self, codigo_ca: str):
        with self.session_factory() as session:
            from src.db.db_models import CaLicitacion
            lic = session.query(CaLicitacion).filter_by(codigo_ca=codigo_ca).first()
            
            if lic:
                # Extraer nota si existe
                nota_texto = ""
                if lic.seguimiento and lic.seguimiento.notas:
                    nota_texto = lic.seguimiento.notas

                return {
                    "codigo_ca": lic.codigo_ca,
                    "nombre": lic.nombre,
                    "descripcion": lic.descripcion,
                    "organismo_nombre": lic.organismo.nombre if lic.organismo else "N/A",
                    "estado_ca_texto": lic.estado_ca_texto,
                    "monto_clp": lic.monto_clp,
                    "fecha_publicacion": str(lic.fecha_publicacion),
                    "fecha_cierre": str(lic.fecha_cierre),
                    "fecha_cierre_p2": str(lic.fecha_cierre_segundo_llamado) if lic.fecha_cierre_segundo_llamado else "No aplica",
                    "direccion_entrega": lic.direccion_entrega,
                    "plazo_entrega": lic.plazo_entrega,
                    "productos_solicitados": lic.productos_solicitados,
                    "nota_usuario": nota_texto
                }
            return None

    # --- ACCIONES RÁPIDAS (Context Menu) ---
    
    def move_to_ofertar(self, codigo_ca: str):
        with self.session_factory() as session:
            from src.db.db_models import CaLicitacion
            lic = session.query(CaLicitacion).filter_by(codigo_ca=codigo_ca).first()
            if lic:
                self.db_service.gestionar_ofertada(lic.ca_id, True)

    def move_to_seguimiento(self, codigo_ca: str):
        with self.session_factory() as session:
            from src.db.db_models import CaLicitacion
            lic = session.query(CaLicitacion).filter_by(codigo_ca=codigo_ca).first()
            if lic:
                self.db_service.gestionar_favorito(lic.ca_id, True)
                self.db_service.gestionar_ofertada(lic.ca_id, False)

    def stop_following(self, codigo_ca: str):
        with self.session_factory() as session:
            from src.db.db_models import CaLicitacion
            lic = session.query(CaLicitacion).filter_by(codigo_ca=codigo_ca).first()
            if lic:
                self.db_service.gestionar_favorito(lic.ca_id, False)
                self.db_service.gestionar_ofertada(lic.ca_id, False)
                self.db_service.ocultar_licitacion(lic.ca_id, True)

    # --- TAREAS EN SEGUNDO PLANO (Workers) ---

    def run_extraction_task(self, config_dict, on_progress, on_finish, on_error):
        """Ejecuta ETL completo en hilo secundario."""
        worker = GenericWorker(self.etl_service.ejecutar_etl_completo, configuracion=config_dict)
        self._conectar_worker(worker, on_progress, on_finish, on_error)
        worker.start()
        self._current_worker = worker

    def run_update_task(self, scope_list, on_progress, on_finish, on_error):
        """Ejecuta Actualización Selectiva."""
        worker = GenericWorker(self.etl_service.ejecutar_actualizacion_selectiva, alcances=scope_list)
        self._conectar_worker(worker, on_progress, on_finish, on_error)
        worker.start()
        self._current_worker = worker

    def run_export_task(self, export_tasks, output_path, on_finish, on_error):
        """Ejecuta exportación Excel/CSV."""
        def _wrapper_export(tasks, path):
             return self.excel_service.ejecutar_exportacion_lote(tasks, path)
        
        worker = GenericWorker(_wrapper_export, tasks=export_tasks, path=output_path)
        worker.finished_success.connect(on_finish)
        worker.finished_error.connect(on_error)
        worker.start()
        self._current_worker = worker

    def _conectar_worker(self, worker, on_prog, on_fin, on_err):
        worker.progress_text.connect(lambda t: on_prog(t, None))
        worker.progress_value.connect(lambda v: on_prog(None, v))
        worker.finished_success.connect(on_fin)
        worker.finished_error.connect(on_err)

    # --- GESTIÓN DE PUNTAJES (ORGANISMOS) ---
    def get_all_organisms_config(self, sector_filter=None):
        """Retorna organismos, opcionalmente filtrados por sector."""
        return self.db_service.exportar_config_organismos(sector_filter)

    def set_organism_rule(self, org_id: int, rule_type: str, points: int):
        if rule_type == 'neutro':
            self.db_service.eliminar_regla_organismo(org_id)
        else:
            # CORRECCIÓN: Convertir a mayúsculas para que coincida con el Enum de la BD
            # (prioritario -> PRIORITARIO, no_deseado -> NO_DESEADO)
            self.db_service.establecer_regla_organismo(org_id, rule_type.upper(), points)

    # --- GESTIÓN DE PUNTAJES (KEYWORDS) ---
    def get_all_keywords(self):
        return self.db_service.exportar_config_keywords()

    def add_keyword(self, text, p_title, p_desc, p_prod, category=None):
        """Pasamanos actualizado."""
        self.db_service.agregar_palabra_clave_flexible(text, p_title, p_desc, p_prod, category)

    def delete_keyword(self, keyword_id):
        self.db_service.eliminar_palabra_clave(keyword_id)
        
    def recalcular_puntajes(self, on_finish):
        """Fuerza un recálculo masivo de puntajes en segundo plano."""
        worker = GenericWorker(self.etl_service.ejecutar_recalculo_total)
        worker.finished_success.connect(on_finish)
        worker.start()
        self._current_worker = worker 

    # --- CONFIGURACIÓN AVANZADA ---
    def save_autopilot_config(self, enabled, time_str):
        self.settings_manager.establecer_valor("auto_extract_enabled", enabled)
        self.settings_manager.establecer_valor("auto_extract_time", time_str)
        self.settings_manager.guardar_configuracion(self.settings_manager.config)

    def get_autopilot_config(self):
        return {
            "enabled": self.settings_manager.obtener_valor("auto_extract_enabled"),
            "time": self.settings_manager.obtener_valor("auto_extract_time")
        }
    
    # --- GESTIÓN DE NOTAS ---

    def get_note(self, codigo_ca: str) -> str:
        """Obtiene la nota personal guardada para una licitación."""
        with self.session_factory() as session:
            from src.db.db_models import CaLicitacion
            lic = session.query(CaLicitacion).filter_by(codigo_ca=codigo_ca).first()
            if lic and lic.seguimiento and lic.seguimiento.notas:
                return lic.seguimiento.notas
            return ""

    def save_note(self, codigo_ca: str, nota: str):
        """Guarda o actualiza la nota del usuario."""
        with self.session_factory() as session:
            from src.db.db_models import CaLicitacion
            lic = session.query(CaLicitacion).filter_by(codigo_ca=codigo_ca).first()
            if lic:
                self.db_service.guardar_nota_usuario(lic.ca_id, nota)
    
    def run_manual_import(self, lista_codigos, destino, on_progress, on_finish, on_error):
        """Ejecuta la importación manual en segundo plano."""
        def _wrapper_import(codigos, dest, callback_texto, callback_porcentaje):
            return self.etl_service.importar_lista_manual(
                codigos, dest, callback_texto, callback_porcentaje
            )
        
        worker = GenericWorker(
            _wrapper_import, 
            codigos=lista_codigos, 
            dest=destino
        )
        self._conectar_worker(worker, on_progress, on_finish, on_error)
        worker.start()
        self._current_worker = worker

    def get_keywords(self, category_filter=None):
        """Obtiene keywords, opcionalmente filtradas por categoría."""
        keywords = self.db_service.obtener_palabras_clave_por_categoria(category_filter)
        # Convertimos a diccionarios para la vista
        return [{
            "ID": k.keyword_id,
            "Palabra Clave": k.keyword,
            "Categoría": k.categoria or "Sin Categoría", # Mostramos algo legible
            "Puntos Título": k.puntos_nombre,
            "Puntos Descripción": k.puntos_descripcion,
            "Puntos Productos": k.puntos_productos
        } for k in keywords]

    def get_categories(self):
        """Obtiene la lista de categorías únicas."""
        return self.db_service.obtener_lista_categorias()
    
    def update_keyword(self, kw_id, text, p_title, p_desc, p_prod, category):
        self.db_service.actualizar_palabra_clave(kw_id, text, p_title, p_desc, p_prod, category)

    def rename_category(self, old_name, new_name):
        self.db_service.renombrar_categoria(old_name, new_name)

    def delete_category_full(self, category_name):
        self.db_service.eliminar_categoria_completa(category_name)

    
    def get_sectors(self):
        """Obtiene la lista de sectores disponibles."""
        return self.db_service.obtener_lista_sectores()

    def set_organism_sector(self, org_id, sector_name):
        """Mueve un organismo a un nuevo sector."""
        self.db_service.mover_organismo_a_sector(org_id, sector_name)

    def rename_sector(self, old_name, new_name):
        self.db_service.renombrar_sector(old_name, new_name)

    def delete_sector(self, sector_name):
        self.db_service.eliminar_sector(sector_name)





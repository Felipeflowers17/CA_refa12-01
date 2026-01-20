# -*- coding: utf-8 -*-
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import sessionmaker, Session
from src.db.db_models import CaLicitacion
from src.utils.logger import configurar_logger

# Importamos los nuevos repositorios
from src.db.repositories.keyword_repository import KeywordRepository
from src.db.repositories.organismo_repository import OrganismoRepository
from src.db.repositories.licitacion_repository import LicitacionRepository
from src.db.repositories.etl_repository import EtlRepository

logger = configurar_logger(__name__)

class DbService:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory
        
        # Inicializamos los repositorios
        self.keyword_repo = KeywordRepository(session_factory)
        self.organismo_repo = OrganismoRepository(session_factory)
        self.licitacion_repo = LicitacionRepository(session_factory)
        self.etl_repo = EtlRepository(session_factory)
        
        logger.info("DbService (Fachada) inicializado con repositorios.")

    # =========================================================================
    # SECCIÓN 1: INGESTIÓN Y MANTENIMIENTO (Delega a EtlRepo)
    # =========================================================================
    
    def insertar_o_actualizar_masivo(self, compras: List[Dict]):
        self.etl_repo.insertar_o_actualizar_masivo(compras)

    def actualizar_fase_2_detalle(self, codigo_ca: str, datos_fase_2: Dict, puntuacion_total: int, detalle_completo: List[str]):
        self.etl_repo.actualizar_fase_2_detalle(codigo_ca, datos_fase_2, puntuacion_total, detalle_completo)

    def actualizar_puntajes_en_lote(self, lista_actualizaciones: List[Tuple[int, int, List[str]]]):
        self.etl_repo.actualizar_puntajes_en_lote(lista_actualizaciones)

    def obtener_datos_para_recalculo_puntajes(self) -> List[Dict]:
        return self.etl_repo.obtener_datos_recalculo()

    def obtener_candidatas_para_fase_2(self, umbral_minimo: int = 10) -> List[CaLicitacion]:
        return self.etl_repo.obtener_candidatas_fase_2(umbral_minimo)

    def obtener_rango_fechas_candidatas_activas(self) -> Tuple[Optional[object], Optional[object]]:
        return self.etl_repo.obtener_rango_fechas_activas()

    def limpiar_registros_antiguos(self) -> int:
        return self.etl_repo.limpiar_registros_antiguos()

    def cerrar_licitaciones_vencidas_localmente(self) -> int:
        return self.etl_repo.cerrar_vencidas_localmente()

    def marcar_organismos_como_vistos(self):
        self.organismo_repo.marcar_organismos_como_vistos()

    # =========================================================================
    # SECCIÓN 2: GESTIÓN DE LICITACIONES (Delega a LicitacionRepo)
    # =========================================================================

    def obtener_licitacion_por_id(self, ca_id: int):
        return self.licitacion_repo.obtener_por_id(ca_id)

    # --- Acciones del Usuario ---
    def gestionar_favorito(self, ca_id: int, es_favorito: bool):
        self.licitacion_repo.gestionar_favorito(ca_id, es_favorito)

    def gestionar_ofertada(self, ca_id: int, es_ofertada: bool):
        self.licitacion_repo.gestionar_ofertada(ca_id, es_ofertada)

    def ocultar_licitacion(self, ca_id: int, ocultar: bool = True):
        self.licitacion_repo.ocultar_licitacion(ca_id, ocultar)

    def guardar_nota_usuario(self, ca_id: int, nota: str):
        self.licitacion_repo.guardar_nota_usuario(ca_id, nota)

    # --- Consultas para Exportación / UI ---
    # Aquí mantenemos la conversión a diccionario para no romper el Controller
    def exportar_candidatas(self) -> List[Dict]:
        data = self.licitacion_repo.obtener_candidatas_filtradas()
        return self._convertir_a_diccionario_seguro(data)

    def exportar_seguimiento(self) -> List[Dict]:
        data = self.licitacion_repo.obtener_seguimiento()
        return self._convertir_a_diccionario_seguro(data)

    def exportar_ofertadas(self) -> List[Dict]:
        data = self.licitacion_repo.obtener_ofertadas()
        return self._convertir_a_diccionario_seguro(data)
    
    def obtener_licitaciones_seguimiento(self):
        # Necesario para el ETL service que pide objetos directos
        return self.licitacion_repo.obtener_seguimiento()
    
    def obtener_licitaciones_ofertadas(self):
        return self.licitacion_repo.obtener_ofertadas()

    def _convertir_a_diccionario_seguro(self, licitaciones: List[CaLicitacion]) -> List[Dict]:
        """Helper visual (se mantiene aquí porque es lógica de presentación)."""
        resultados = []
        for ca in licitaciones:
            tiene_nota = False
            if ca.seguimiento and ca.seguimiento.notas and ca.seguimiento.notas.strip():
                tiene_nota = True

            resultados.append({
                "puntuacion_final": ca.puntuacion_final,
                "puntaje_detalle": ca.puntaje_detalle,
                "codigo_ca": ca.codigo_ca,
                "nombre": ca.nombre,
                "descripcion": ca.descripcion,
                "organismo_nombre": ca.organismo.nombre if ca.organismo else "N/A",
                "direccion_entrega": ca.direccion_entrega,
                "estado_ca_texto": ca.estado_ca_texto,
                "fecha_publicacion": ca.fecha_publicacion,
                "fecha_cierre": ca.fecha_cierre,
                "fecha_cierre_segundo_llamado": ca.fecha_cierre_segundo_llamado,
                "proveedores_cotizando": ca.proveedores_cotizando,
                "productos_solicitados": str(ca.productos_solicitados) if ca.productos_solicitados else "",
                "es_favorito": ca.seguimiento.es_favorito if ca.seguimiento else False,
                "es_ofertada": ca.seguimiento.es_ofertada if ca.seguimiento else False,
                "tiene_nota": tiene_nota,
                "monto_clp": ca.monto_clp
            })
        return resultados

    # =========================================================================
    # SECCIÓN 3: CONFIGURACIÓN (Delega a KeywordRepo y OrganismoRepo)
    # =========================================================================

    # --- Keywords ---
    def obtener_todas_palabras_clave(self):
        return self.keyword_repo.obtener_todas()

    def agregar_palabra_clave_flexible(self, keyword, p_nom, p_desc, p_prod, categoria=None):
        self.keyword_repo.agregar(keyword, p_nom, p_desc, p_prod, categoria)

    def eliminar_palabra_clave(self, keyword_id):
        self.keyword_repo.eliminar(keyword_id)

    def obtener_palabras_clave_por_categoria(self, categoria=None):
        return self.keyword_repo.obtener_por_categoria(categoria)

    def obtener_lista_categorias(self):
        return self.keyword_repo.obtener_categorias_unicas()

    def actualizar_palabra_clave(self, kw_id, keyword, p_nom, p_desc, p_prod, categoria):
        self.keyword_repo.actualizar(kw_id, keyword, p_nom, p_desc, p_prod, categoria)

    def renombrar_categoria(self, old_name, new_name):
        self.keyword_repo.renombrar_categoria(old_name, new_name)

    def eliminar_categoria_completa(self, categoria):
        self.keyword_repo.eliminar_categoria_completa(categoria)

    def exportar_config_keywords(self):
        return self.keyword_repo.exportar_config()

    # --- Organismos ---
    def obtener_todos_organismos(self):
        return self.organismo_repo.obtener_todos()

    def obtener_reglas_organismos(self):
        return self.organismo_repo.obtener_reglas()

    def establecer_regla_organismo(self, org_id, rule_type, points):
        self.organismo_repo.establecer_regla(org_id, rule_type, points)

    def eliminar_regla_organismo(self, org_id):
        self.organismo_repo.eliminar_regla(org_id)

    def exportar_config_organismos(self, sector_filter=None):
        return self.organismo_repo.exportar_config(sector_filter)

    def obtener_lista_sectores(self):
        return self.organismo_repo.obtener_sectores()

    def mover_organismo_a_sector(self, org_id, sector_name):
        self.organismo_repo.mover_a_sector(org_id, sector_name)

    def renombrar_sector(self, old_name, new_name):
        self.organismo_repo.renombrar_sector(old_name, new_name)

    def eliminar_sector(self, sector_name):
        self.organismo_repo.eliminar_sector(sector_name)
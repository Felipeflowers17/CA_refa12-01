from typing import List, Optional
from sqlalchemy.orm import sessionmaker, Session, joinedload
from sqlalchemy import select, or_
from src.db.db_models import CaLicitacion, CaSeguimiento, CaOrganismo
from src.utils.logger import configurar_logger

logger = configurar_logger(__name__)

class LicitacionRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def obtener_por_id(self, ca_id: int) -> Optional[CaLicitacion]:
        with self.session_factory() as session:
            stmt = select(CaLicitacion).options(
                joinedload(CaLicitacion.organismo), 
                joinedload(CaLicitacion.seguimiento)
            ).where(CaLicitacion.ca_id == ca_id)
            return session.scalars(stmt).first()

    def obtener_candidatas_filtradas(self, umbral_minimo: int = 5) -> List[CaLicitacion]:
        with self.session_factory() as session:
            subq = select(CaSeguimiento.ca_id).where(
                or_(CaSeguimiento.es_favorito == True, CaSeguimiento.es_ofertada == True, CaSeguimiento.es_oculta == True)
            )
            stmt = select(CaLicitacion).options(
                joinedload(CaLicitacion.seguimiento), 
                joinedload(CaLicitacion.organismo).joinedload(CaOrganismo.sector)
            ).filter(
                CaLicitacion.puntuacion_final >= umbral_minimo, 
                CaLicitacion.ca_id.notin_(subq),
                or_(CaLicitacion.estado_ca_texto == 'Publicada', CaLicitacion.estado_ca_texto == 'Publicada - Segundo llamado')
            ).order_by(CaLicitacion.puntuacion_final.desc())
            return session.scalars(stmt).all()

    def obtener_seguimiento(self) -> List[CaLicitacion]:
        with self.session_factory() as session:
            stmt = select(CaLicitacion).options(
                joinedload(CaLicitacion.seguimiento), 
                joinedload(CaLicitacion.organismo).joinedload(CaOrganismo.sector)
            ).join(CaSeguimiento, CaLicitacion.ca_id == CaSeguimiento.ca_id).filter(
                CaSeguimiento.es_favorito == True, CaSeguimiento.es_ofertada == False
            ).order_by(CaLicitacion.fecha_cierre.asc())
            return session.scalars(stmt).all()

    def obtener_ofertadas(self) -> List[CaLicitacion]:
        with self.session_factory() as session:
            stmt = select(CaLicitacion).options(
                joinedload(CaLicitacion.seguimiento), 
                joinedload(CaLicitacion.organismo).joinedload(CaOrganismo.sector)
            ).join(CaSeguimiento, CaLicitacion.ca_id == CaSeguimiento.ca_id).filter(
                CaSeguimiento.es_ofertada == True
            ).order_by(CaLicitacion.fecha_cierre.asc())
            return session.scalars(stmt).all()

    def _actualizar_seguimiento(self, ca_id: int, es_favorito: Optional[bool] = None, es_ofertada: Optional[bool] = None, es_oculta: Optional[bool] = None):
        with self.session_factory() as session:
            try:
                seguimiento = session.get(CaSeguimiento, ca_id)
                if seguimiento:
                    if es_favorito is not None: seguimiento.es_favorito = es_favorito
                    if es_ofertada is not None: seguimiento.es_ofertada = es_ofertada
                    if es_oculta is not None: seguimiento.es_oculta = es_oculta
                    if es_ofertada: seguimiento.es_favorito = True
                    if es_oculta: 
                        seguimiento.es_favorito = False
                        seguimiento.es_ofertada = False
                else:
                    nuevo = CaSeguimiento(
                        ca_id=ca_id, 
                        es_favorito=es_favorito or False, 
                        es_ofertada=es_ofertada or False,
                        es_oculta=es_oculta or False
                    )
                    session.add(nuevo)
                session.commit()
            except Exception as e:
                logger.error(f"Error seguimiento {ca_id}: {e}")
                session.rollback()

    def gestionar_favorito(self, ca_id: int, es_favorito: bool): 
        self._actualizar_seguimiento(ca_id, es_favorito=es_favorito)
        
    def gestionar_ofertada(self, ca_id: int, es_ofertada: bool): 
        self._actualizar_seguimiento(ca_id, es_ofertada=es_ofertada)

    def ocultar_licitacion(self, ca_id: int, ocultar: bool = True):
        self._actualizar_seguimiento(ca_id, es_oculta=ocultar)

    def guardar_nota_usuario(self, ca_id: int, nota: str):
        with self.session_factory() as session:
            try:
                seguimiento = session.get(CaSeguimiento, ca_id)
                if seguimiento: seguimiento.notas = nota
                else: 
                    nuevo = CaSeguimiento(ca_id=ca_id, notas=nota)
                    session.add(nuevo)
                session.commit()
            except Exception as e:
                logger.error(f"Error nota {ca_id}: {e}")
                session.rollback()
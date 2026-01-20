from typing import List, Dict, Optional
from sqlalchemy.orm import sessionmaker, Session, joinedload
from sqlalchemy import select, update, delete
from src.db.db_models import CaOrganismo, CaSector, CaOrganismoRegla, TipoReglaOrganismo
from src.utils.logger import configurar_logger

logger = configurar_logger(__name__)

class OrganismoRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def obtener_todos(self) -> List[CaOrganismo]:
        with self.session_factory() as session: 
            return session.scalars(select(CaOrganismo).order_by(CaOrganismo.nombre)).all()

    def obtener_reglas(self) -> List[CaOrganismoRegla]:
        with self.session_factory() as session: 
            return session.scalars(select(CaOrganismoRegla).options(joinedload(CaOrganismoRegla.organismo))).all()

    def establecer_regla(self, org_id: int, rule_type: str, points: int):
        rule_type = str(rule_type).upper() 
        with self.session_factory() as session:
            regla = session.query(CaOrganismoRegla).filter_by(organismo_id=org_id).first()
            if regla:
                regla.tipo = rule_type
                regla.puntos = points
            else:
                nueva_regla = CaOrganismoRegla(organismo_id=org_id, tipo=rule_type, puntos=points)
                session.add(nueva_regla)
            session.commit()

    def eliminar_regla(self, organismo_id: int):
        with self.session_factory() as session:
            stmt = select(CaOrganismoRegla).where(CaOrganismoRegla.organismo_id == organismo_id)
            regla = session.scalars(stmt).first()
            if regla: 
                session.delete(regla)
                session.commit()

    def exportar_config(self, sector_filter: Optional[str] = None) -> List[Dict]:
        with self.session_factory() as session:
            stmt = select(CaOrganismo, CaOrganismoRegla, CaSector).outerjoin(
                CaOrganismoRegla, CaOrganismo.organismo_id == CaOrganismoRegla.organismo_id
            ).join(
                CaSector, CaOrganismo.sector_id == CaSector.sector_id
            ).order_by(CaOrganismo.nombre)
            
            if sector_filter and sector_filter != "Todos":
                stmt = stmt.where(CaSector.nombre == sector_filter)

            resultados = []
            for org, regla, sector in session.execute(stmt):
                estado = "Neutro"
                puntos = 0
                if regla:
                    if regla.tipo == TipoReglaOrganismo.PRIORITARIO:
                        estado = "Prioritario"
                        puntos = regla.puntos
                    elif regla.tipo == TipoReglaOrganismo.NO_DESEADO:
                        estado = "No Deseado"
                        puntos = regla.puntos 
                
                resultados.append({
                    "ID": org.organismo_id,
                    "Organismo": org.nombre,
                    "Sector": sector.nombre,
                    "Estado": estado,
                    "Puntos Asignados": puntos,
                    "Es Nuevo": "Sí" if org.es_nuevo else "No"
                })
            return resultados

    def obtener_sectores(self) -> List[str]:
        with self.session_factory() as session:
            stmt = select(CaSector.nombre).distinct().order_by(CaSector.nombre)
            return list(session.scalars(stmt).all())

    def mover_a_sector(self, org_id: int, nombre_sector: str):
        with self.session_factory() as session:
            sector = session.scalars(select(CaSector).filter_by(nombre=nombre_sector)).first()
            if not sector:
                sector = CaSector(nombre=nombre_sector)
                session.add(sector)
                session.flush()
            
            org = session.get(CaOrganismo, org_id)
            if org:
                org.sector_id = sector.sector_id
                session.commit()

    def renombrar_sector(self, nombre_actual: str, nombre_nuevo: str):
        with self.session_factory() as session:
            sector = session.scalars(select(CaSector).filter_by(nombre=nombre_actual)).first()
            if sector:
                sector.nombre = nombre_nuevo
                session.commit()

    def eliminar_sector(self, nombre_sector: str):
        with self.session_factory() as session:
            sector_a_borrar = session.scalars(select(CaSector).filter_by(nombre=nombre_sector)).first()
            if not sector_a_borrar: return

            sector_general = session.scalars(select(CaSector).filter_by(nombre="General")).first()
            if not sector_general:
                sector_general = CaSector(nombre="General")
                session.add(sector_general)
                session.flush()
            
            stmt_update = update(CaOrganismo).where(
                CaOrganismo.sector_id == sector_a_borrar.sector_id
            ).values(sector_id=sector_general.sector_id)
            session.execute(stmt_update)
            
            session.delete(sector_a_borrar)
            session.commit()

    def marcar_organismos_como_vistos(self):
        with self.session_factory() as session:
            try:
                stmt = update(CaOrganismo).where(CaOrganismo.es_nuevo == True).values(es_nuevo=False)
                session.execute(stmt)
                session.commit()
            except Exception as e:
                logger.error(f"Error reseteando organismos nuevos: {e}")
                session.rollback()
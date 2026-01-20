from typing import List, Dict, Tuple, Optional, Set
from datetime import date, datetime, timedelta
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import select, or_, update, func, bindparam, and_, not_
from sqlalchemy.dialects.postgresql import insert
from src.db.db_models import CaLicitacion, CaOrganismo, CaSector, CaSeguimiento
from src.utils.logger import configurar_logger

logger = configurar_logger(__name__)

class EtlRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def _asegurar_organismos_existen(self, session: Session, nombres_organismos: Set[str]) -> Dict[str, int]:
        if not nombres_organismos: return {}
        nombres_norm = {n.strip() for n in nombres_organismos if n}
        
        stmt = select(CaOrganismo.nombre, CaOrganismo.organismo_id).where(CaOrganismo.nombre.in_(nombres_norm))
        existentes = {nombre: oid for nombre, oid in session.execute(stmt).all()}
        
        faltantes = nombres_norm - set(existentes.keys())
        if faltantes:
            sector_default = session.scalars(select(CaSector).limit(1)).first()
            if not sector_default:
                sector_default = CaSector(nombre="General")
                session.add(sector_default)
                session.flush()
            
            nuevos_orgs = [{"nombre": nombre, "sector_id": sector_default.sector_id, "es_nuevo": True} for nombre in faltantes]
            session.execute(insert(CaOrganismo), nuevos_orgs)
            
            stmt_nuevos = select(CaOrganismo.nombre, CaOrganismo.organismo_id).where(CaOrganismo.nombre.in_(faltantes))
            for nombre, oid in session.execute(stmt_nuevos).all():
                existentes[nombre] = oid
        return existentes

    def insertar_o_actualizar_masivo(self, compras: List[Dict]):
        if not compras: return
        with self.session_factory() as session:
            try:
                nombres_orgs = {c.get("organismo", "No Especificado") for c in compras}
                mapa_orgs = self._asegurar_organismos_existen(session, nombres_orgs)
                
                data_to_upsert = []
                codigos_vistos = set()
                
                for item in compras:
                    codigo = item.get("codigo", item.get("id"))
                    if not codigo or codigo in codigos_vistos: continue
                    codigos_vistos.add(codigo)
                    
                    org_nombre = (item.get("organismo") or "No Especificado").strip()
                    
                    record = {
                        "codigo_ca": codigo,
                        "nombre": item.get("nombre"),
                        "monto_clp": item.get("monto_disponible_CLP"),
                        "fecha_publicacion": item.get("fecha_publicacion"),
                        "fecha_cierre": item.get("fecha_cierre"),
                        "proveedores_cotizando": item.get("cantidad_provedores_cotizando"),
                        "estado_ca_texto": item.get("estado"),
                        "estado_convocatoria": item.get("estado_convocatoria"),
                        "organismo_id": mapa_orgs.get(org_nombre),
                    }
                    data_to_upsert.append(record)
                
                if data_to_upsert:
                    stmt = insert(CaLicitacion).values(data_to_upsert)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=['codigo_ca'],
                        set_={
                            "proveedores_cotizando": stmt.excluded.proveedores_cotizando,
                            "estado_ca_texto": stmt.excluded.estado_ca_texto, 
                            "fecha_cierre": stmt.excluded.fecha_cierre,       
                            "estado_convocatoria": stmt.excluded.estado_convocatoria,
                            "monto_clp": stmt.excluded.monto_clp
                        }
                    )
                    session.execute(stmt)
                    session.commit()
            except Exception as e:
                session.rollback()
                raise e

    def actualizar_fase_2_detalle(self, codigo_ca: str, datos_fase_2: Dict, puntuacion_total: int, detalle_completo: List[str]):
        with self.session_factory() as session:
            try:
                lic = session.scalars(select(CaLicitacion).where(CaLicitacion.codigo_ca == codigo_ca)).first()
                if not lic: return
                
                lic.descripcion = datos_fase_2.get("descripcion")
                lic.productos_solicitados = datos_fase_2.get("productos_solicitados")
                lic.direccion_entrega = datos_fase_2.get("direccion_entrega")
                lic.puntuacion_final = puntuacion_total
                lic.plazo_entrega = datos_fase_2.get("plazo_entrega")
                lic.puntaje_detalle = detalle_completo 
                lic.fecha_cierre_segundo_llamado = datos_fase_2.get("fecha_cierre_p2")
                if datos_fase_2.get("estado"): lic.estado_ca_texto = datos_fase_2.get("estado")
                if datos_fase_2.get("estado_convocatoria") is not None: lic.estado_convocatoria = datos_fase_2.get("estado_convocatoria")
                
                session.commit()
            except Exception:
                session.rollback()
                raise

    def actualizar_puntajes_en_lote(self, lista_actualizaciones: List[Tuple[int, int, List[str]]]):
        if not lista_actualizaciones: return
        datos_para_update = [{"b_ca_id": c, "b_puntuacion": p, "b_detalle": d} for c, p, d in lista_actualizaciones]
        stmt = update(CaLicitacion).where(CaLicitacion.ca_id == bindparam("b_ca_id")).values(puntuacion_final=bindparam("b_puntuacion"), puntaje_detalle=bindparam("b_detalle"))
        
        with self.session_factory() as session:
            try:
                session.connection().execute(stmt, datos_para_update)
                session.commit()
            except Exception as e:
                session.rollback()
                raise e

    def obtener_datos_recalculo(self) -> List[Dict]:
        with self.session_factory() as session:
            stmt = select(
                CaLicitacion.ca_id, CaLicitacion.codigo_ca, CaLicitacion.nombre, CaLicitacion.estado_ca_texto, 
                CaLicitacion.descripcion, CaLicitacion.productos_solicitados, CaLicitacion.puntuacion_final, 
                CaOrganismo.nombre.label("organismo_nombre")
            ).outerjoin(CaOrganismo, CaLicitacion.organismo_id == CaOrganismo.organismo_id)
            rows = session.execute(stmt).all()
            return [{
                "ca_id": r.ca_id, "codigo_ca": r.codigo_ca, "nombre": r.nombre, "estado_ca_texto": r.estado_ca_texto, 
                "organismo_nombre": r.organismo_nombre or "", "descripcion": r.descripcion, 
                "productos_solicitados": r.productos_solicitados, "puntuacion_final_actual": r.puntuacion_final or 0 
            } for r in rows]

    def obtener_candidatas_fase_2(self, umbral: int) -> List[CaLicitacion]:
        with self.session_factory() as session:
            stmt = select(CaLicitacion).filter(CaLicitacion.puntuacion_final >= umbral, CaLicitacion.descripcion.is_(None)).order_by(CaLicitacion.fecha_cierre.asc())
            return session.scalars(stmt).all()

    def obtener_rango_fechas_activas(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        with self.session_factory() as session:
            subq = select(CaSeguimiento.ca_id).where(or_(CaSeguimiento.es_favorito == True, CaSeguimiento.es_ofertada == True, CaSeguimiento.es_oculta == True))
            stmt = select(func.min(CaLicitacion.fecha_publicacion), func.max(CaLicitacion.fecha_publicacion)).filter(
                CaLicitacion.ca_id.notin_(subq), or_(CaLicitacion.estado_ca_texto.ilike('%Publicada%'), CaLicitacion.estado_ca_texto.ilike('%Segundo%'))
            )
            return session.execute(stmt).first()

    def limpiar_registros_antiguos(self) -> int:
        with self.session_factory() as session:
            fecha_corte = date.today() - timedelta(days=30)
            criterios = and_(
                not_(CaLicitacion.estado_ca_texto.ilike("%Publicada%")),
                or_(and_(CaLicitacion.fecha_cierre_segundo_llamado.isnot(None), CaLicitacion.fecha_cierre_segundo_llamado < fecha_corte),
                    and_(CaLicitacion.fecha_cierre_segundo_llamado.is_(None), CaLicitacion.fecha_cierre < fecha_corte)),
                ~CaLicitacion.seguimiento.has(CaSeguimiento.es_favorito == True),
                ~CaLicitacion.seguimiento.has(CaSeguimiento.es_ofertada == True)
            )
            eliminadas = session.query(CaLicitacion).filter(criterios).delete(synchronize_session=False)
            if eliminadas > 0: session.commit()
            return eliminadas

    def cerrar_vencidas_localmente(self) -> int:
        with self.session_factory() as session:
            fecha_limite = date.today() - timedelta(days=14)
            filtro = or_(and_(CaLicitacion.fecha_cierre_segundo_llamado.isnot(None), CaLicitacion.fecha_cierre_segundo_llamado < fecha_limite),
                         and_(CaLicitacion.fecha_cierre_segundo_llamado.is_(None), CaLicitacion.fecha_cierre < fecha_limite))
            registros = session.query(CaLicitacion).filter(CaLicitacion.estado_ca_texto.ilike("%Publicada%"), filtro).all()
            for lic in registros: lic.estado_ca_texto = "Cerrada (Vencida Local)"
            if registros: session.commit()
            return len(registros)
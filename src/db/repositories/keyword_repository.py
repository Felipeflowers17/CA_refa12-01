from typing import List, Optional
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import select, delete, update, or_
from src.db.db_models import CaPalabraClave
from src.utils.logger import configurar_logger

logger = configurar_logger(__name__)

class KeywordRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def obtener_todas(self) -> List[CaPalabraClave]:
        with self.session_factory() as session: 
            return session.scalars(select(CaPalabraClave).order_by(CaPalabraClave.keyword)).all()

    def obtener_por_categoria(self, categoria: Optional[str] = None) -> List[CaPalabraClave]:
        with self.session_factory() as session:
            stmt = select(CaPalabraClave).order_by(CaPalabraClave.keyword)
            if categoria:
                if categoria == "Sin Categoría":
                    stmt = stmt.filter(or_(CaPalabraClave.categoria.is_(None), CaPalabraClave.categoria == ""))
                else:
                    stmt = stmt.filter(CaPalabraClave.categoria == categoria)
            return session.scalars(stmt).all()

    def obtener_categorias_unicas(self) -> List[str]:
        with self.session_factory() as session:
            stmt = select(CaPalabraClave.categoria).distinct().where(
                CaPalabraClave.categoria.isnot(None), 
                CaPalabraClave.categoria != "",
                CaPalabraClave.categoria != "Sin Categoría" 
            ).order_by(CaPalabraClave.categoria)
            return list(session.scalars(stmt).all())

    def agregar(self, keyword: str, p_nom: int, p_desc: int, p_prod: int, categoria: str = None):
        with self.session_factory() as session:
            existente = session.scalars(select(CaPalabraClave).filter_by(keyword=keyword.lower().strip())).first()
            if existente:
                existente.puntos_nombre = p_nom
                existente.puntos_descripcion = p_desc
                existente.puntos_productos = p_prod
                existente.categoria = categoria
            else:
                nuevo = CaPalabraClave(
                    keyword=keyword.lower().strip(),
                    puntos_nombre=p_nom,
                    puntos_descripcion=p_desc,
                    puntos_productos=p_prod,
                    categoria=categoria
                )
                session.add(nuevo)
            session.commit()

    def actualizar(self, kw_id: int, keyword: str, p_nom: int, p_desc: int, p_prod: int, categoria: str):
        with self.session_factory() as session:
            kw = session.get(CaPalabraClave, kw_id)
            if kw:
                kw.keyword = keyword.lower().strip()
                kw.puntos_nombre = p_nom
                kw.puntos_descripcion = p_desc
                kw.puntos_productos = p_prod
                kw.categoria = categoria
                session.commit()

    def eliminar(self, keyword_id: int):
        with self.session_factory() as session: 
            session.query(CaPalabraClave).filter_by(keyword_id=keyword_id).delete()
            session.commit()

    def renombrar_categoria(self, nombre_actual: str, nombre_nuevo: str):
        with self.session_factory() as session:
            stmt = update(CaPalabraClave).where(CaPalabraClave.categoria == nombre_actual).values(categoria=nombre_nuevo)
            session.execute(stmt)
            session.commit()

    def eliminar_categoria_completa(self, categoria: str):
        with self.session_factory() as session:
            stmt = delete(CaPalabraClave).where(CaPalabraClave.categoria == categoria)
            session.execute(stmt)
            session.commit()

    def exportar_config(self) -> List[dict]:
        with self.session_factory() as session:
            kws = session.scalars(select(CaPalabraClave).order_by(CaPalabraClave.keyword)).all()
            return [{
                "ID": k.keyword_id,
                "Palabra Clave": k.keyword,
                "Puntos Título": k.puntos_nombre,
                "Puntos Descripción": k.puntos_descripcion,
                "Puntos Productos": k.puntos_productos
            } for k in kws]
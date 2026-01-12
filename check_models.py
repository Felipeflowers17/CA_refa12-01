import sys
import os
from sqlalchemy import inspect

# Configurar ruta para encontrar tus archivos
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from src.db.db_models import CaOrganismoRegla
    
    print(f"\n🔍 Inspeccionando clase: {CaOrganismoRegla.__name__}")
    print(f"📄 Tabla en BD: {CaOrganismoRegla.__tablename__}")
    print("📋 COLUMNAS DISPONIBLES (Usa uno de estos nombres):")
    
    mapper = inspect(CaOrganismoRegla)
    for prop in mapper.attrs:
        # Filtramos solo las columnas, no las relaciones
        if hasattr(prop, 'columns'):
            print(f"   👉 {prop.key}")
            
except ImportError as e:
    print(f"❌ Error importando: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
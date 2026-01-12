import sys
import logging
import time

# Configuración de logs para ver TODO lo que pasa
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

print("=== INICIANDO DIAGNÓSTICO DE ACTUALIZACIÓN ===")
print("1. Cargando componentes del Backend...")

try:
    from src.controllers.main_controller import MainController
    controller = MainController()
    print("   -> Controlador cargado correctamente.")
except Exception as e:
    print(f"   -> ERROR FATAL cargando controlador: {e}")
    sys.exit(1)

# --- DEFINICIÓN DE CALLBACKS SIMULADOS ---
# Esto imita lo que hace la GUI: recibir texto y barras de progreso
def mock_callback_texto(msg):
    print(f"[GUI MSG]: {msg}")

def mock_callback_progreso(val):
    if val is not None:
        print(f"[GUI BAR]: {val}%")

# --- PRUEBA 1: VERIFICAR LICITACIONES EN SEGUIMIENTO ---
print("\n2. Verificando datos en Base de Datos...")
try:
    seguimiento = controller.db_service.obtener_licitaciones_seguimiento()
    count = len(seguimiento)
    print(f"   -> Encontradas {count} licitaciones en 'Seguimiento'.")
    
    if count == 0:
        print("   -> ADVERTENCIA: No hay nada que actualizar. La prueba terminará rápido.")
except Exception as e:
    print(f"   -> ERROR leyendo base de datos: {e}")

# --- PRUEBA 2: PROBAR LA CONEXIÓN (EL PUNTO DONDE SE PEGA) ---
print("\n3. Probando conexión con Mercado Público (Playwright)...")
print("   (Esto debería tomar entre 5 y 20 segundos. Si pasa más tiempo, aquí está el error)")

try:
    # Llamamos directamente al método que usa Playwright
    controller.scraper_service.verificar_sesion(callback_progreso=mock_callback_texto)
    print("   -> ¡CONEXIÓN EXITOSA! Los headers se han capturado.")
except Exception as e:
    print(f"\n[!!!] ERROR CRÍTICO EN CONEXIÓN: {e}")
    print("Posibles causas:\n - Playwright no encuentra el navegador.\n - Internet inestable.\n - Mercado Público cambió su seguridad.")
    sys.exit(1)

# --- PRUEBA 3: EJECUTAR LA ACTUALIZACIÓN ---
print("\n4. Ejecutando lógica de actualización (Simulando botón)...")
try:
    # Ejecutamos la lógica síncronamente (sin hilos) para ver errores
    controller.etl_service.ejecutar_actualizacion_selectiva(
        callback_texto=mock_callback_texto,
        callback_porcentaje=mock_callback_progreso,
        alcances=['seguimiento']
    )
    print("\n=== PROCESO TERMINADO CON ÉXITO ===")
except Exception as e:
    print(f"\n[!!!] ERROR DURANTE LA ACTUALIZACIÓN: {e}")
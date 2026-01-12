# src/controllers/worker.py
from PySide6.QtCore import QThread, Signal

class WorkerSignals(QThread):
    """
    Clase base para workers que emiten señales estándar.
    """
    progress_text = Signal(str)
    progress_value = Signal(int)
    finished_success = Signal(object) # Retorna datos si es necesario
    finished_error = Signal(str)

class GenericWorker(WorkerSignals):
    """
    Ejecuta una función bloquante en un hilo separado.
    Útil para llamar al ETL o Scraper sin congelar la GUI.
    """
    def __init__(self, function_to_run, *args, **kwargs):
        super().__init__()
        self.function = function_to_run
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            # Inyectamos callbacks de progreso si la función los acepta
            # Esto asume que tus servicios ETL aceptan 'callback_texto' y 'callback_porcentaje'
            if 'callback_texto' not in self.kwargs:
                self.kwargs['callback_texto'] = self.progress_text.emit
            if 'callback_porcentaje' not in self.kwargs:
                self.kwargs['callback_porcentaje'] = self.progress_value.emit

            result = self.function(*self.args, **self.kwargs)
            self.finished_success.emit(result)
        except Exception as e:
            # Capturamos cualquier error del backend y lo enviamos a la GUI
            self.finished_error.emit(str(e))
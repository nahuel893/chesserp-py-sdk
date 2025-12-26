import logging
import os
import sys
from typing import Optional

class LoggerConfig:
    """
    Configuración centralizada de logging para la librería.
    Asegura que todos los módulos compartan el mismo formato y handlers.
    """
    _initialized = False
    _logger = None

    @classmethod
    def setup(cls, 
              log_file: str = "chesserp.log", 
              level: int = logging.DEBUG,
              console_output: bool = True) -> logging.Logger:
        """
        Configura el logger raíz. Debe llamarse una vez al inicio de la aplicación.
        Si no se llama explícitamente, get_logger() lo inicializará con valores por defecto.
        """
        if cls._initialized:
            return cls._logger

        # Configurar logger raíz
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # Limpiar handlers existentes para evitar duplicados
        if root_logger.hasHandlers():
            root_logger.handlers.clear()

        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(module)s | %(message)s'
        )

        # Handler Archivo
        try:
            log_path = os.path.join(os.getcwd(), log_file)
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except IOError as e:
            print(f"Warning: Could not create log file {log_file}: {e}")

        # Handler Consola
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        cls._initialized = True
        cls._logger = root_logger
        return root_logger

    @classmethod
    def get_logger(cls, name: Optional[str] = None) -> logging.Logger:
        """
        Obtiene un logger. Si el sistema no está configurado, lo inicializa con defaults.
        """
        if not cls._initialized:
            cls.setup()
        
        return logging.getLogger(name)

# Instancia global o alias para facilitar uso
get_logger = LoggerConfig.get_logger
setup_logger = LoggerConfig.setup

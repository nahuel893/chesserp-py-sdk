import logging
import os

def get_logger(name: str = "chesserp", log_file: str = "app.log", level: int = logging.INFO) -> logging.Logger:
    """
    Configura y retorna un logger.
    Args:
        name (str): Nombre del logger.
        log_file (str): Archivo donde se guardarán los logs.
        level (int): Nivel de logging.
    Returns:
        logging.Logger: Logger configurado.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Evita agregar múltiples handlers si ya existen
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(module)s | %(message)s'
        )

        # Handler para consola
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # Handler para archivo
        fh = logging.FileHandler(os.path.join(os.getcwd(), log_file))
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
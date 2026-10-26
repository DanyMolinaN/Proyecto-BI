"""
Configuracion del sistema de registro (logging) para el proyecto.

Provee formateo consistente para salidas por consola y almacenamiento
persistente en archivos de log, sin uso de caracteres graficos ni emojis.
"""

import logging
import sys
from pathlib import Path
from src.config import settings


def setup_logger(name: str = "epn_scraper") -> logging.Logger:
    """Configura y retorna una instancia de logger con manejadores de consola y archivo.

    Args:
        name (str): Identificador del modulo o subsistema.

    Returns:
        logging.Logger: Instancia configurada para emision de eventos.
    """
    logger = logging.getLogger(name)
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(level)

    # Evitar duplicacion de manejadores si la funcion es invocada varias veces
    if not logger.handlers:
        formatter = logging.Formatter(settings.log_format)

        # Manejador de consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Manejador de archivo persistente
        log_file: Path = settings.log_file
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        logger.propagate = False

    return logger

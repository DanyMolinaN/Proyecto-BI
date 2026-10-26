"""
Paquete de modulos extractores especializados para el portal institucional de la EPN.
"""

from src.scrapers.base_scraper import BaseScraper
from src.scrapers.facultades_scraper import FacultadesScraper
from src.scrapers.carreras_scraper import CarrerasScraper
from src.scrapers.autoridades_scraper import AutoridadesScraper
from src.scrapers.institucional_scraper import InstitucionalScraper
from src.scrapers.noticias_scraper import NoticiasScraper

__all__ = [
    "BaseScraper",
    "FacultadesScraper",
    "CarrerasScraper",
    "AutoridadesScraper",
    "InstitucionalScraper",
    "NoticiasScraper",
]

"""
Clase base abstracta para los modulos extractores (scrapers).

Define el contrato comun de ejecucion, inyeccion del cliente HTTP,
gestion de logs y persistencia intermedia de datos sin limpiar.
"""

from abc import ABC, abstractmethod
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from src.config import settings
from src.utils.http_client import HttpClient
from src.utils.logger import setup_logger


class ExtractionError(RuntimeError):
    """Se lanza cuando un extractor obtiene menos registros de los esperados."""


class BaseScraper(ABC):
    """Contrato base y operaciones comunes para todos los scrapers del proyecto."""

    def __init__(self, http_client: Optional[HttpClient] = None) -> None:
        """Inicializa el extractor con cliente HTTP y logger especializado.

        Args:
            http_client (Optional[HttpClient]): Instancia inyectable del cliente HTTP.
        """
        self.http_client = http_client or HttpClient()
        self.logger = setup_logger(self.__class__.__name__)
        self.interim_dir = settings.data_interim_dir

    @abstractmethod
    def extract(self) -> List[Dict[str, Any]]:
        """Metodo abstracto que implementa la logica especifica de extraccion.

        Returns:
            List[Dict[str, Any]]: Lista de diccionarios con los registros parseados.
        """
        pass

    def save_interim(self, data: List[Dict[str, Any]], filename: str) -> Path:
        """Almacena los datos extraidos en la capa intermedia (interim) en JSON y CSV.

        Args:
            data (List[Dict[str, Any]]): Conjunto de registros crudos.
            filename (str): Nombre base del archivo sin extension.

        Returns:
            Path: Ruta del archivo JSON guardado.
        """
        if not data:
            self.logger.warning(f"No hay datos para persistir en la etapa interim para {filename}")
            return self.interim_dir / f"{filename}.json"

        # Guardar en formato JSON (fiel a la jerarquia parseada)
        json_path = self.interim_dir / f"{filename}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Guardar tambien una version preliminar en CSV para inspeccion rapida
        csv_path = self.interim_dir / f"{filename}.csv"
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False, encoding="utf-8")

        self.logger.info(f"Persistidos {len(data)} registros en capa interim: {json_path.name}")
        return json_path

    def run(self) -> List[Dict[str, Any]]:
        """Ejecuta el ciclo de vida completo de extraccion y persistencia intermedia.

        Returns:
            List[Dict[str, Any]]: Datos parseados en bruto.
        """
        self.logger.info(f"Iniciando ejecucion de extractor: {self.__class__.__name__}")
        try:
            records = self.extract()
            key = self.__class__.__name__.lower().replace("scraper", "")
            minimum = settings.min_records.get(key, 1)
            if len(records) < minimum:
                raise ExtractionError(
                    f"{self.__class__.__name__} extrajo {len(records)} registros (minimo esperado: {minimum}). "
                    "Posible cambio en el sitio, bloqueo o falla de red; no se persistieron datos."
                )
            self.logger.info(f"Extraccion completada con {len(records)} registros.")
            self.save_interim(records, self.__class__.__name__.lower())
            return records
        except Exception as exc:
            self.logger.error(f"Error critico durante ejecucion de {self.__class__.__name__}: {exc}", exc_info=True)
            raise

"""
Cargador de tablas dimensionales a archivos planos delimitados por coma (CSV).

Garantiza idempotencia en la exportacion a data/processed/ preservando
la codificacion UTF-8 y formatos estandar para alimentacion de herramientas BI
como Power BI, Tableau o Metabase.
"""

from pathlib import Path
from typing import Dict
import pandas as pd

from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger("load_csv")


class CsvLoader:
    """Exporta DataFrames dimensionales al directorio de datos procesados."""

    def __init__(self, target_dir: Path = None) -> None:
        """Inicializa el cargador con el directorio de destino configurado.

        Args:
            target_dir (Path, optional): Carpeta de salida para los CSV procesados.
        """
        self.target_dir = target_dir or settings.data_processed_dir
        self.target_dir.mkdir(parents=True, exist_ok=True)

    def load_table(self, df: pd.DataFrame, table_name: str) -> Path:
        """Exporta un DataFrame individual a archivo CSV de forma idempotente.

        Args:
            df (pd.DataFrame): Datos procesados.
            table_name (str): Nombre logico del archivo destino.

        Returns:
            Path: Ruta del archivo generado.
        """
        if df is None or df.empty:
            logger.warning(f"No hay registros que exportar a CSV para la tabla: {table_name}")
            csv_path = self.target_dir / f"{table_name}.csv"
            # Crear cabecera vacia si existe definicion de columnas
            if df is not None:
                df.to_csv(csv_path, index=False, encoding="utf-8")
            return csv_path

        csv_path = self.target_dir / f"{table_name}.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8")
        logger.info(f"Tabla {table_name} exportada exitosamente a CSV: {csv_path.name} ({len(df)} filas)")
        return csv_path

    def load_all(self, tables_dict: Dict[str, pd.DataFrame]) -> Dict[str, Path]:
        """Exporta el conjunto completo de dimensiones y tablas de hechos a CSV.

        Args:
            tables_dict (Dict[str, pd.DataFrame]): Mapeo de nombre de tabla a DataFrame.

        Returns:
            Dict[str, Path]: Mapeo de nombre de tabla a ruta de archivo generado.
        """
        results = {}
        for table_name, df in tables_dict.items():
            results[table_name] = self.load_table(df, table_name)
        return results

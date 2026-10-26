"""
Cargador de base de datos relacional para el Data Warehouse institucional.

Utiliza SQLAlchemy para soportar SQLite (por defecto) y PostgreSQL de manera transparente,
permitiendo la ejecucion de scripts DDL, carga masiva de DataFrames y validacion
de integridad tras la insercion.
"""

from pathlib import Path
from typing import Dict, Optional
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger("load_database")


class DatabaseLoader:
    """Administra la conexion y carga de tablas del modelo dimensional en SQL."""

    def __init__(self, connection_url: Optional[str] = None) -> None:
        """Inicializa el motor de base de datos con la cadena de conexion.

        Args:
            connection_url (Optional[str]): URI de conexion (ej: sqlite:///data/epn_dwh.db).
        """
        self.connection_url = connection_url or settings.database_url
        self.engine: Engine = create_engine(self.connection_url, echo=False)
        logger.info(f"Conexion inicializada a base de datos: {self.engine.url.drivername}")

    def execute_sql_file(self, sql_file_path: Path) -> None:
        """Ejecuta un script SQL externo (DDL o DML).

        Args:
            sql_file_path (Path): Ruta al archivo .sql.
        """
        if not sql_file_path.exists():
            logger.warning(f"No se encontro el archivo SQL: {sql_file_path}")
            return

        sql_content = sql_file_path.read_text(encoding="utf-8")
        # Separar por punto y coma respetando bloques
        statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]

        with self.engine.begin() as conn:
            for statement in statements:
                # Omitir comentarios completos
                lines = [line for line in statement.splitlines() if not line.strip().startswith("--")]
                clean_stmt = "\n".join(lines).strip()
                if clean_stmt:
                    conn.execute(text(clean_stmt))

        logger.info(f"Ejecutado satisfactoriamente el script SQL: {sql_file_path.name}")

    def load_table(self, df: pd.DataFrame, table_name: str, if_exists: str = "replace") -> int:
        """Inserta o reemplaza una tabla en la base de datos de manera idempotente.

        Args:
            df (pd.DataFrame): Datos estructurados.
            table_name (str): Nombre de la tabla destino.
            if_exists (str): Politica ante existencia previa ('replace', 'append', 'fail').

        Returns:
            int: Cantidad de registros insertados.
        """
        if df is None or df.empty:
            logger.warning(f"Omitiendo carga a BD para tabla vacia: {table_name}")
            return 0

        # Cargar con SQLAlchemy optimizado
        df.to_sql(name=table_name, con=self.engine, if_exists=if_exists, index=False)
        logger.info(f"Cargados {len(df)} registros en la base de datos: tabla '{table_name}'")
        return len(df)

    def load_all(self, tables_dict: Dict[str, pd.DataFrame]) -> Dict[str, int]:
        """Carga en lote todas las dimensiones y tablas de hechos.

        Args:
            tables_dict (Dict[str, pd.DataFrame]): Coleccion de DataFrames del modelo.

        Returns:
            Dict[str, int]: Conteo de registros cargados por tabla.
        """
        summary = {}
        # Primero cargar dimensiones, luego hechos
        dim_keys = [k for k in tables_dict.keys() if k.startswith("dim_")]
        fact_keys = [k for k in tables_dict.keys() if k.startswith("fact_")]
        other_keys = [k for k in tables_dict.keys() if k not in dim_keys and k not in fact_keys]

        ordered_keys = dim_keys + other_keys + fact_keys

        for table_name in ordered_keys:
            df = tables_dict[table_name]
            count = self.load_table(df, table_name, if_exists="replace")
            summary[table_name] = count

        return summary

    def get_table_counts(self) -> Dict[str, int]:
        """Consulta el numero real de filas en cada tabla registrada en la BD.

        Returns:
            Dict[str, int]: Tabla y conteo de filas actual.
        """
        counts = {}
        with self.engine.connect() as conn:
            # Inspeccionar tablas existentes segun dialecto
            if "sqlite" in self.engine.url.drivername:
                res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
                tables = [r[0] for r in res]
            else:
                res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';"))
                tables = [r[0] for r in res]

            for t in tables:
                if not t.startswith("sqlite_"):
                    c_res = conn.execute(text(f"SELECT COUNT(*) FROM {t};"))
                    counts[t] = c_res.scalar()

        return counts

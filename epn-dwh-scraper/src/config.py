"""
Modulo de configuracion del proyecto.

Carga y valida los parametros de ejecucion desde el archivo YAML de configuracion
y variables de entorno (.env).
"""

import os
from pathlib import Path
from typing import Any, Dict
import yaml
from dotenv import load_dotenv

# Determinacion de la raiz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno desde .env si existe
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class Settings:
    """Clase singleton para la configuracion centralizada del sistema."""

    def __init__(self, config_path: Path = None) -> None:
        """Inicializa los ajustes leyendo el archivo YAML y variables de entorno.

        Args:
            config_path (Path, optional): Ruta al archivo settings.yaml.
        """
        if config_path is None:
            config_path = BASE_DIR / "config" / "settings.yaml"

        self.config_path = config_path
        self._raw_config = self._load_yaml()

        # Configuracion general del proyecto
        self.project_name: str = self._raw_config.get("project", {}).get("name", "epn-dwh-scraper")
        self.project_version: str = self._raw_config.get("project", {}).get("version", "1.0.0")

        # Parametros de red
        net_cfg = self._raw_config.get("network", {})
        self.base_url: str = net_cfg.get("base_url", "https://www.epn.edu.ec")
        self.user_agent: str = os.getenv("SCRAPER_USER_AGENT", net_cfg.get("user_agent"))
        self.timeout_seconds: int = int(os.getenv("SCRAPER_TIMEOUT", net_cfg.get("timeout_seconds", 15)))
        self.rate_limit_seconds: float = float(os.getenv("SCRAPER_RATE_LIMIT", net_cfg.get("rate_limit_seconds", 1.0)))
        self.max_retries: int = int(os.getenv("SCRAPER_MAX_RETRIES", net_cfg.get("max_retries", 4)))
        self.backoff_factor: float = float(os.getenv("SCRAPER_BACKOFF_FACTOR", net_cfg.get("backoff_factor", 1.5)))
        
        env_cache = os.getenv("SCRAPER_USE_CACHE")
        self.use_cache: bool = (env_cache.lower() == "true") if env_cache is not None else bool(net_cfg.get("use_cache", True))
        
        env_ssl = os.getenv("SCRAPER_VERIFY_SSL")
        self.verify_ssl: bool = (env_ssl.lower() == "true") if env_ssl is not None else bool(net_cfg.get("verify_ssl", False))

        # Endpoints
        self.endpoints: Dict[str, str] = self._raw_config.get("endpoints", {})

        # Rutas de directorios
        paths_cfg = self._raw_config.get("paths", {})
        self.data_raw_dir: Path = BASE_DIR / paths_cfg.get("data_raw", "data/raw")
        self.data_interim_dir: Path = BASE_DIR / paths_cfg.get("data_interim", "data/interim")
        self.data_processed_dir: Path = BASE_DIR / paths_cfg.get("data_processed", "data/processed")
        self.logs_dir: Path = BASE_DIR / paths_cfg.get("logs", "logs")

        # Asegurar existencia de carpetas criticas
        self.data_raw_dir.mkdir(parents=True, exist_ok=True)
        self.data_interim_dir.mkdir(parents=True, exist_ok=True)
        self.data_processed_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Base de datos
        db_env = os.getenv("DATABASE_URL")
        if db_env:
            self.database_url: str = db_env
        else:
            default_db = self._raw_config.get("storage", {}).get("database_url", "sqlite:///data/epn_dwh.db")
            # Ajustar ruta relativa a la raiz del proyecto
            if default_db.startswith("sqlite:///data/"):
                db_file = BASE_DIR / "data" / "epn_dwh.db"
                self.database_url = f"sqlite:///{db_file.as_posix()}"
            else:
                self.database_url = default_db

        # Registro (Logging)
        log_cfg = self._raw_config.get("logging", {})
        self.log_level: str = os.getenv("LOG_LEVEL", log_cfg.get("level", "INFO"))
        self.log_format: str = log_cfg.get("format", "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        self.log_file: Path = BASE_DIR / log_cfg.get("file_name", "logs/scraper_execution.log")

    def _load_yaml(self) -> Dict[str, Any]:
        """Carga el contenido del archivo YAML de configuracion.

        Returns:
            Dict[str, Any]: Estructura jerarquica con las directivas.
        """
        if not self.config_path.exists():
            return {}
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}


# Instancia global accesible
settings = Settings()

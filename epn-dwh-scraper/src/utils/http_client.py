"""
Cliente HTTP con soporte para politicas eticas de web scraping.

Incluye cumplimiento de robots.txt, gestion de rate limiting, almacenamiento
en cache local (data/raw), reintentos con retroceso exponencial (backoff) y
cabeceras identificables para fines academicos.
"""

import hashlib
import re
import time
import urllib.robotparser
from pathlib import Path
from typing import Optional
import requests
import urllib3

from src.config import settings
from src.utils.logger import setup_logger

# Desactivar advertencias de certificados no verificados si SSL verify es falso
if not settings.verify_ssl:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = setup_logger("http_client")


class HttpClient:
    """Gestiona las peticiones web respetando directivas eticas y tecnicas."""

    def __init__(self) -> None:
        """Inicializa la sesion HTTP, el parser de robots.txt y el control de frecuencia."""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": settings.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8",
            "Accept-Language": "es-EC,es;q=0.9,en;q=0.8",
        })
        self.rate_limit_seconds = settings.rate_limit_seconds
        self.last_request_time = 0.0
        self.raw_dir = settings.data_raw_dir
        self.use_cache = settings.use_cache

        # Parser de robots.txt
        self._robot_parser: Optional[urllib.robotparser.RobotFileParser] = None
        self._init_robots_txt()

    def _init_robots_txt(self) -> None:
        """Carga y procesa el archivo robots.txt del dominio principal de la EPN."""
        robots_url = settings.endpoints.get("robots_txt", f"{settings.base_url}/robots.txt")
        try:
            response = self.session.get(
                robots_url,
                timeout=settings.timeout_seconds,
                verify=settings.verify_ssl
            )
            if response.status_code == 200:
                self._robot_parser = urllib.robotparser.RobotFileParser()
                self._robot_parser.parse(response.text.splitlines())
                logger.info(f"Archivo robots.txt procesado exitosamente desde: {robots_url}")
            else:
                logger.warning(f"No fue posible obtener robots.txt (Codigo HTTP: {response.status_code})")
        except Exception as exc:
            logger.warning(f"Error al inicializar robots.txt: {exc}. Se procedera con precaucion.")

    def is_allowed(self, url: str) -> bool:
        """Verifica si la URL esta permitida para rastreo segun robots.txt.

        Args:
            url (str): Direccion URL completa a evaluar.

        Returns:
            bool: True si esta permitida o si no se pudo cargar robots.txt, False si esta prohibida.
        """
        if self._robot_parser is None:
            return True
        return self._robot_parser.can_fetch(settings.user_agent, url)

    def _apply_rate_limit(self) -> None:
        """Aplica una pausa forzada entre solicitudes sucesivas para proteger el servidor."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_seconds:
            sleep_time = self.rate_limit_seconds - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _get_cache_path(self, url: str, extension: str = "html") -> Path:
        """Calcula la ruta del archivo de cache a partir del hash de la URL.

        Args:
            url (str): Direccion URL.
            extension (str): Extension del archivo de almacenamiento.

        Returns:
            Path: Ruta del archivo dentro de data/raw.
        """
        slug = re.sub(r"[^a-zA-Z0-9_-]", "_", url.replace("https://", "").replace("http://", ""))
        slug = slug[:50]
        url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()[:10]
        filename = f"{slug}_{url_hash}.{extension}"
        return self.raw_dir / filename

    def get(self, url: str, use_cache: Optional[bool] = None, force_refresh: bool = False) -> Optional[str]:
        """Realiza una peticion GET retornando el texto de la respuesta con manejo de cache y reintentos.

        Args:
            url (str): Direccion URL del recurso.
            use_cache (Optional[bool]): Si se debe consultar y guardar en cache local.
            force_refresh (bool): Si es True, ignora la cache existente y descarga nuevamente.

        Returns:
            Optional[str]: Contenido textual del recurso, o None si fallo la descarga.
        """
        if not self.is_allowed(url):
            logger.warning(f"Extraccion rechazada por politica de robots.txt para URL: {url}")
            return None

        should_cache = self.use_cache if use_cache is None else use_cache
        cache_path = self._get_cache_path(url, extension="html")

        if should_cache and not force_refresh and cache_path.exists():
            logger.debug(f"Cargando recurso desde cache local: {cache_path.name}")
            try:
                return cache_path.read_text(encoding="utf-8", errors="ignore")
            except Exception as read_err:
                logger.warning(f"Error al leer cache local {cache_path}: {read_err}. Se intentara via red.")

        retries = settings.max_retries
        backoff = settings.backoff_factor

        for attempt in range(1, retries + 1):
            self._apply_rate_limit()
            try:
                logger.debug(f"Solicitando URL (Intento {attempt}/{retries}): {url}")
                response = self.session.get(
                    url,
                    timeout=settings.timeout_seconds,
                    verify=settings.verify_ssl
                )

                if response.status_code == 200:
                    content = response.text
                    if should_cache:
                        try:
                            cache_path.write_text(content, encoding="utf-8", errors="ignore")
                        except Exception as write_err:
                            logger.warning(f"No fue posible escribir en cache {cache_path}: {write_err}")
                    return content

                if response.status_code in [404, 410]:
                    logger.warning(f"Recurso no encontrado (HTTP {response.status_code}) en {url}")
                    return None

                if response.status_code in [429, 500, 502, 503, 504]:
                    wait_time = backoff ** attempt
                    logger.warning(f"HTTP {response.status_code} en {url}. Reintentando en {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue

                logger.warning(f"Codigo de respuesta inesperado {response.status_code} para {url}")
                return None

            except requests.exceptions.RequestException as req_err:
                wait_time = backoff ** attempt
                logger.warning(f"Error de conexion en {url} ({req_err}). Reintentando en {wait_time:.1f}s...")
                time.sleep(wait_time)

        logger.error(f"Se agotaron los {retries} reintentos para la URL: {url}")
        return None

    def get_json(self, url: str, use_cache: Optional[bool] = None) -> Optional[dict]:
        """Obtiene y decodifica un payload JSON con soporte de cache local.

        Args:
            url (str): Direccion URL del endpoint JSON.
            use_cache (Optional[bool]): Control de uso de cache.

        Returns:
            Optional[dict]: Diccionario o lista decodificada, o None si hay error.
        """
        import json

        should_cache = self.use_cache if use_cache is None else use_cache
        cache_path = self._get_cache_path(url, extension="json")

        if should_cache and cache_path.exists():
            try:
                return json.loads(cache_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        text = self.get(url, use_cache=False)
        if text:
            try:
                data = json.loads(text)
                if should_cache:
                    cache_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
                return data
            except json.JSONDecodeError as json_err:
                logger.error(f"Fallo al decodificar JSON desde {url}: {json_err}")
        return None

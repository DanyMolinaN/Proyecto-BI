"""
Cliente HTTP con soporte para politicas eticas de web scraping.

Incluye cumplimiento de robots.txt, gestion de rate limiting, almacenamiento
en cache local (data/raw), reintentos con retroceso exponencial (backoff) y
cabeceras identificables para fines academicos.
"""

import hashlib
import json
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

    def __init__(self, use_cache: Optional[bool] = None, force_refresh: bool = False) -> None:
        """Inicializa la sesion HTTP, el parser de robots.txt y el control de frecuencia.

        Args:
            use_cache (Optional[bool]): Sobrescribe el uso de cache de la configuracion (--no-cache).
            force_refresh (bool): Si es True, ignora la cache existente y vuelve a descargar (--force-refresh).
        """
        self.force_refresh = force_refresh
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": settings.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8",
            "Accept-Language": "es-EC,es;q=0.9,en;q=0.8",
        })
        self.rate_limit_seconds = settings.rate_limit_seconds
        self.last_request_time = 0.0
        self.raw_dir = settings.data_raw_dir
        self.use_cache = settings.use_cache if use_cache is None else use_cache

        # Parser de robots.txt
        self._robot_parser: Optional[urllib.robotparser.RobotFileParser] = None
        self._robots_unreachable = False
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
            elif 400 <= response.status_code < 500:
                # RFC 9309: robots.txt inexistente equivale a sin restricciones
                logger.warning(f"robots.txt no disponible (HTTP {response.status_code}); se asume sin restricciones.")
            else:
                self._robots_unreachable = True
                logger.error(f"robots.txt devolvio HTTP {response.status_code}; se suspende el rastreo.")
        except Exception as exc:
            self._robots_unreachable = True
            logger.error(f"No fue posible leer robots.txt ({exc}); se suspende el rastreo por precaucion.")

    def is_allowed(self, url: str) -> bool:
        """Verifica si la URL esta permitida para rastreo segun robots.txt.

        Args:
            url (str): Direccion URL completa a evaluar.

        Returns:
            bool: True si esta permitida; False si esta prohibida o si robots.txt no pudo consultarse
            por error de red o de servidor.
        """
        if self._robots_unreachable:
            return False
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

    def _cache_is_fresh(self, cache_path: Path) -> bool:
        """Indica si existe una entrada de cache cuya antiguedad no supera el TTL configurado.

        Args:
            cache_path (Path): Ruta del archivo de cache.

        Returns:
            bool: True si el archivo existe y esta vigente.
        """
        if not cache_path.exists():
            return False
        ttl_hours = settings.cache_ttl_hours
        if ttl_hours <= 0:
            return True
        age_hours = (time.time() - cache_path.stat().st_mtime) / 3600
        return age_hours <= ttl_hours

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

        if should_cache and not (force_refresh or self.force_refresh) and self._cache_is_fresh(cache_path):
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
        should_cache = self.use_cache if use_cache is None else use_cache
        cache_path = self._get_cache_path(url, extension="json")

        if should_cache and not self.force_refresh and self._cache_is_fresh(cache_path):
            try:
                return json.loads(cache_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        text = self.get(url, use_cache=False, force_refresh=True)
        if text:
            try:
                data = json.loads(text)
                if should_cache:
                    cache_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
                return data
            except json.JSONDecodeError as json_err:
                logger.error(f"Fallo al decodificar JSON desde {url}: {json_err}")
        return None

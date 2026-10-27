# `src/utils/http_client.py`

**Estado:** estable · **Fase:** 1

## Propósito
Cliente HTTP único del proyecto. Todas las descargas pasan por aquí para cumplir las reglas éticas: respetar `robots.txt`, no saturar el servidor y no repetir peticiones innecesarias.

## Entradas y salidas
| | Detalle |
| :-- | :-- |
| Entrada | URL; opcionalmente `use_cache` y `force_refresh` |
| Salida | Texto de la respuesta (`get`) o JSON (`get_json`); `None` si falló |
| Efecto | Guarda las respuestas en `data/raw/` |

## Cómo funciona
1. Al crearse lee `robots.txt` (RFC 9309):
   - HTTP 200: se aplican sus reglas.
   - Respuesta 4xx: se asume sin restricciones.
   - Error de red o 5xx: **se suspende el rastreo** (`is_allowed` devuelve `False`).
2. `get(url)`: rechaza la URL si `robots.txt` la prohíbe; si hay caché vigente, la usa; si no, descarga con espera de 1 s entre peticiones.
3. Reintenta con espera creciente ante 429, 500, 502, 503, 504 o errores de conexión. En 404 y 410 devuelve `None` sin reintentar.
4. `get_json(url)`: igual, pero decodifica JSON y guarda el JSON formateado.

### Caché
El nombre del archivo es `slug + hash MD5 de la URL`. Una entrada **vence** a las `cache_ttl_hours` (24 h por defecto). `force_refresh=True` la ignora siempre.

## Reglas de datos
No modifica el contenido. Si algo falla devuelve `None`; nunca fabrica una respuesta.

## Configuración
`network.*` de `settings.yaml` y sus variables `SCRAPER_*` (ver [config.md](config.md)). El constructor acepta `HttpClient(use_cache=..., force_refresh=...)`; `main.py` le pasa `--no-cache` y `--force-refresh`.

## Pruebas
`tests/test_improvements.py`: vencimiento de caché, `robots.txt` inalcanzable, `force_refresh` y `no_cache`.

## Límites conocidos / pendientes (Fase 2)
- No procesa PDF (las mallas curriculares son PDF).
- La caché guarda texto; no guarda cabeceras ni códigos de estado.

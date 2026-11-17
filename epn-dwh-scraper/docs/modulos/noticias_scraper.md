# `src/scrapers/noticias_scraper.py`

**Estado:** estable · **Fase:** 1

## Propósito
Extrae noticias, convocatorias y comunicados oficiales de la EPN.

## Entradas y salidas
| | Detalle |
| :-- | :-- |
| Entrada | API de WordPress `/wp-json/wp/v2/posts` (principal) o `/noticias/` (respaldo HTML) |
| Salida | `data/interim/noticiasscraper.json` (30 noticias en la última corrida) |

## Cómo funciona
1. `_extract_via_api(limit=30)` pide los últimos 30 artículos y guarda `post_id`, fecha, título, resumen (máx. 400 caracteres) y URL.
2. Si la API no responde, `_extract_via_html()` lee los enlaces de la página de noticias.
3. **La categoría se asigna por palabras del título** (Convocatoria y Empleo, Investigación y Ciencia, Resoluciones y Gobierno, Vida Académica y Admisión, Institucional General). Es una clasificación aproximada, no un dato del portal.

## Reglas de datos
- **Sin noticias de ejemplo.** La versión 1 cargaba tres noticias inventadas (con fecha de octubre de 2026) si la API y el HTML fallaban. Ahora devuelve lista vacía y `run()` falla con `ExtractionError`.
- Fecha ilegible: `NULL` (antes se usaba la fecha de hoy).

## Configuración
`endpoints.noticias_api`, `endpoints.noticias_web`, `min_records.noticias`.

## Pruebas
`tests/test_improvements.py::TestInstitucionalYNoticiasSinRespaldo` (sin fuentes → vacío).

## Límites conocidos / pendientes (Fase 2)
- Solo los últimos 30 artículos; no hay histórico ni paginación.
- La clasificación por palabras puede equivocarse; conviene usar las categorías propias de WordPress.
- En el respaldo HTML no hay resumen: se repite el título.

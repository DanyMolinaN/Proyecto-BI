# `src/scrapers/autoridades_scraper.py`

**Estado:** parcial · **Fase:** 1 → 2

## Propósito
Extrae las autoridades de alta dirección (Rector, Vicerrectores) y los decanos y subdecanos de las facultades.

## Entradas y salidas
| | Detalle |
| :-- | :-- |
| Entrada | `https://www.epn.edu.ec/autoridades/` y las páginas de facultad |
| Salida | `data/interim/autoridadesscraper.json` (10 registros en la última corrida) |

## Cómo funciona
1. `_extract_authorities_from_main_page()` recorre `h2`, `h3` y `p`: un encabezado con título académico (`Dr.`, `Dra.`, `Ing.`…) abre una autoridad; el párrafo siguiente es el cargo y los demás forman la biografía.
2. `_extract_deans_from_faculties()` busca `Subdecano:` en las páginas de cada facultad.
3. `extract()` une ambas listas sin duplicados por nombre.
4. `_build_record()` normaliza: título académico, tipo de cargo (Alta Dirección / Decanal), `es_titular` (0 si el cargo contiene "(E)" o "subrogante") y correo.

## Reglas de datos
- Correo y biografía: solo si aparecen en la fuente; si no, `NULL`. La versión 1 inventaba correos (`rectorado@epn.edu.ec`) y biografías.
- Título académico sin prefijo reconocido: `NULL` (antes "Especialista").
- `periodo_gestion`: `NULL`; el portal no lo publica.
- **Sin autoridades de respaldo.** La versión 1 inyectaba una lista fija de seis personas si se extraían menos de tres.

## Configuración
`endpoints.autoridades`, `min_records.autoridades`.

## Pruebas
`tests/test_scrapers.py::test_autoridades_scraper_build_record`.

## Límites conocidos / pendientes (Fase 2)
- Correo y biografía quedan vacíos en las 10 autoridades.
- Las URLs de facultad de `_extract_deans_from_faculties` están escritas a mano; conviene usar las que descubre `FacultadesScraper`.
- Las autoridades (E) se distinguen por texto del cargo; no hay fecha de designación.

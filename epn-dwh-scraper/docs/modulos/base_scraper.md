# `src/scrapers/base_scraper.py`

**Estado:** estable · **Fase:** 1

## Propósito
Clase base de todos los scrapers. Define el contrato común y garantiza que una extracción incompleta **falle** en lugar de cargarse.

## Entradas y salidas
| | Detalle |
| :-- | :-- |
| Entrada | Un `HttpClient` inyectable |
| Salida | Lista de diccionarios; guarda `data/interim/<nombre>.json` y `.csv` |

## Cómo funciona
- Cada scraper implementa `extract()` y devuelve una lista de registros.
- `run()` llama a `extract()`, **verifica el mínimo de registros** y persiste en `data/interim/`.
- El nombre del archivo es el de la clase en minúsculas (`carrerasscraper.json`).
- `ExtractionError` se lanza si se extrajeron menos registros que `min_records.<scraper>` (en `settings.yaml`). No se escribe nada en ese caso.

## Reglas de datos
Un scraper nunca debe devolver registros inventados ni listas de respaldo. Si no puede extraer, devuelve lista vacía y `run()` lo convierte en error.

## Configuración
`min_records` en `config/settings.yaml`: facultades 5, carreras 20, autoridades 5, institucional 2, noticias 5.

## Pruebas
`tests/test_improvements.py::TestMinimoDeRegistros`.

## Límites conocidos / pendientes (Fase 2)
- Los mínimos son valores fijos; conviene revisarlos si el portal cambia de tamaño.

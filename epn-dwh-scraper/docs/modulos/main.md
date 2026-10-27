# `src/main.py`

**Estado:** estable · **Fase:** 1

## Propósito
Punto de entrada. Orquesta el flujo completo: extraer del portal, transformar y validar, y cargar a CSV y base de datos. Se puede ejecutar completo o por etapas.

## Entradas y salidas
| | Detalle |
| :-- | :-- |
| Entrada | Banderas de línea de comandos; configuración de `config/settings.yaml` y `.env` |
| Salida | `data/interim/*.json`, `data/processed/*.csv`, `data/epn_dwh.db`, `logs/reporte_calidad_datos.md` |

## Cómo funciona
`ETLPipeline` tiene cinco métodos:

1. `run_scrapers(modules)`: ejecuta los scrapers pedidos y guarda cada resultado en `data/interim/`.
2. `load_interim_from_disk()`: recupera lo ya extraído, para reprocesar sin volver a descargar.
3. `transform(raw)`: construye dimensiones y hechos con `DataCleaner`, aplica el SCD2 de autoridades contra lo ya cargado en la base y perfila cada tabla con `DataValidator`.
4. `load_data(tables, to_csv, to_db)`: escribe CSV y/o base de datos.
5. `run_all()`: encadena los cuatro pasos anteriores.

### Banderas
| Bandera | Efecto |
| :-- | :-- |
| `--all` (o sin banderas) | Pipeline completo |
| `--facultades` `--carreras` `--autoridades` `--institucional` `--noticias` | Solo ese extractor |
| `--transform` | Transforma y valida los datos de `data/interim/` |
| `--load-csv` / `--load-db` | Carga solo a CSV / solo a la base |
| `--no-cache` | No usa la caché local |
| `--force-refresh` | Ignora la caché y vuelve a descargar |

`--no-cache` y `--force-refresh` se pasan a `HttpClient` (en la versión 1 se ignoraban).

## Reglas de datos
No transforma datos por sí mismo. Si un scraper falla o extrae menos del mínimo (`ExtractionError`), el pipeline se detiene y no carga nada.

## Configuración
Ver [config.md](config.md). La tabla `dim_tiempo` se genera con `build_dim_tiempo()` (2015–2035 por defecto).

## Pruebas
No hay prueba directa de la CLI. Se verifica ejecutando `python -m src.main --all`.

## Límites conocidos / pendientes (Fase 2)
- `transform` lee la base de datos para el SCD2 aunque no se vaya a cargar en ella.
- No hay prueba automática de extremo a extremo con HTML guardado.

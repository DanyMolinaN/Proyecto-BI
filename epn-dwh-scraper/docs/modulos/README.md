# Documentación por módulo

Cada módulo del código tiene su propio `.md` en esta carpeta. **Regla del proyecto:** si se crea o cambia un módulo, se crea o actualiza su documento en el mismo commit.

## Principio de datos (aplica a todos los módulos)

> Si el portal no publica un dato, queda `NULL` y el reporte de calidad lo muestra. Nunca se rellena con un valor plausible, y no existen listas "de respaldo" escritas a mano.

Lo que sí se permite es **inferir** un dato cuando se marca como inferido (por ejemplo `dim_carrera.campos_inferidos`).

## Índice

| Capa | Módulo | Documento | Qué hace en una línea |
| :-- | :-- | :-- | :-- |
| Orquestación | `src/main.py` | [main.md](main.md) | CLI que ejecuta extracción, transformación y carga |
| Configuración | `src/config.py` | [config.md](config.md) | Lee `settings.yaml` y variables de entorno |
| Utilidades | `src/utils/http_client.py` | [http_client.md](http_client.md) | Peticiones HTTP éticas con caché, reintentos y `robots.txt` |
| Utilidades | `src/utils/helpers.py`, `src/utils/logger.py` | [helpers.md](helpers.md) | Limpieza de texto, extracción por etiqueta, claves sustitutas, logging |
| Extracción | `src/scrapers/base_scraper.py` | [base_scraper.md](base_scraper.md) | Contrato común y mínimo de registros |
| Extracción | `src/scrapers/facultades_scraper.py` | [facultades_scraper.md](facultades_scraper.md) | Facultades y unidades académicas |
| Extracción | `src/scrapers/carreras_scraper.py` | [carreras_scraper.md](carreras_scraper.md) | Carreras de grado y posgrado |
| Extracción | `src/scrapers/autoridades_scraper.py` | [autoridades_scraper.md](autoridades_scraper.md) | Autoridades centrales y de facultad |
| Extracción | `src/scrapers/institucional_scraper.py` | [institucional_scraper.md](institucional_scraper.md) | Misión, visión, historia y centros de investigación |
| Extracción | `src/scrapers/noticias_scraper.py` | [noticias_scraper.md](noticias_scraper.md) | Noticias vía API de WordPress |
| Transformación | `src/transform/cleaning.py` | [cleaning.md](cleaning.md) | Construye dimensiones y hechos |
| Transformación | `src/transform/scd2.py` | [scd2.md](scd2.md) | Historial de autoridades (SCD Tipo 2) |
| Transformación | `src/transform/validation.py` | [validation.md](validation.md) | Calidad de datos y reporte |
| Carga | `src/load/to_csv.py` | [to_csv.md](to_csv.md) | Exporta tablas a CSV |
| Carga | `src/load/to_database.py` | [to_database.md](to_database.md) | Carga a SQLite/PostgreSQL |

Documentos generales: [revision_y_mejoras.md](../revision_y_mejoras.md) (qué se cambió respecto a la versión 1), [modelo_dimensional.md](../modelo_dimensional.md), [diccionario_datos.md](../diccionario_datos.md), [consideraciones_eticas.md](../consideraciones_eticas.md).

## Estructura de cada documento

1. **Propósito** · 2. **Entradas y salidas** · 3. **Cómo funciona** · 4. **Reglas de datos** · 5. **Configuración** · 6. **Pruebas** · 7. **Límites conocidos / pendientes (Fase 2)**.

Usa [_plantilla.md](_plantilla.md) para un módulo nuevo.

## Flujo de datos

```
Portal EPN → [scrapers] → data/interim/*.json → [cleaning + scd2 + validation] → [to_csv / to_database]
                ↑ http_client (caché en data/raw)                                   data/processed/*.csv · data/epn_dwh.db
```

## Qué NO se sube al repositorio

`.env` (variables y secretos locales), `data/` (descargas, CSV y base de datos), `logs/*.log`, `venv/`. Solo se versiona `.env.example`, con valores de ejemplo y **sin credenciales**. Si el proyecto pasa a PostgreSQL, la contraseña va en `.env` (`DATABASE_URL`), nunca en `settings.yaml`.

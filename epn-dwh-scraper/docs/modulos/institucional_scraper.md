# `src/scrapers/institucional_scraper.py`

**Estado:** estable · **Fase:** 1

## Propósito
Extrae la identidad institucional (misión, visión, valores, principios), la cronología histórica y los centros de investigación.

## Entradas y salidas
| | Detalle |
| :-- | :-- |
| Entrada | `/nosotros/`, `/historia/`, `/laboratorios_institucionales/` |
| Salida | `data/interim/institucionalscraper.json` (28 registros: 2 de identidad, 18 hitos, 8 centros) |

## Cómo funciona
### Nosotros
Convierte la página en líneas. `MISIÓN` y `VISIÓN` son encabezados y el texto está en la línea siguiente. Los **principios** son los párrafos entre `Principios` y `MISIÓN`. Los **valores** son los nombres cortos que aparecen entre `Institucionales` y `Plan Estratégico`.

### Historia
Estructura real de la página: una línea con el año, una con el día (`30 de agosto`), un título corto y la descripción. Cada año abre un hito.

### Laboratorios
Recorre los encabezados de centros e institutos y toma el siguiente texto como descripción y ubicación.

Cada resultado se normaliza a `categoria`, `clave`, `contenido`, `metadato`, `url`.

## Reglas de datos
- **Sin textos de respaldo.** La versión 1 tenía una misión, visión, valores y principios por defecto, tres hitos y tres centros escritos a mano.
- **Sin año por defecto.** La versión 1 asignaba 1869 a 19 de 21 hitos; ahora el año sale de la página, o la clave es `Sin anio`.
- Misión o visión ausentes: no se crea el registro.
- Descripción o ubicación de un centro ausentes: `NULL`.

## Configuración
`endpoints.nosotros`, `endpoints.historia`, `endpoints.laboratorios_institucionales`, `min_records.institucional`.

## Pruebas
`tests/test_improvements.py::TestInstitucionalYNoticiasSinRespaldo`.

## Límites conocidos / pendientes (Fase 2)
- Los valores se detectan por longitud (≤ 22 caracteres); un cambio de diseño puede romperlo.
- Algunos centros muestran la facultad como descripción ("Facultad: …") cuando la página no trae texto propio.
- Nombres de facultad con variaciones ("Agroindustria" / "Agroindustrial") sin normalizar.

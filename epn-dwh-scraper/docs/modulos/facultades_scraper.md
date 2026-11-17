# `src/scrapers/facultades_scraper.py`

**Estado:** estable · **Fase:** 1

## Propósito
Extrae las facultades y la Escuela de Formación de Tecnólogos (ESFOT): nombre, sigla, decano, subdecano, misión, visión, departamentos y contacto.

## Entradas y salidas
| | Detalle |
| :-- | :-- |
| Entrada | `https://www.epn.edu.ec/facultades/` y la página de cada facultad |
| Salida | `data/interim/facultadesscraper.json` (9 registros en la última corrida) |

## Cómo funciona
1. `_get_faculty_urls()` descubre los enlaces `facultad-*` y `/esfot` en el directorio.
2. `_parse_faculty_page(url)` lee cada página: `h1` para el nombre, `Decano:` y `Subdecano:` por expresión regular, párrafos con "misión" y "visión", encabezados de departamentos, correo y teléfono.
3. `_infer_acronym(nombre)` asigna la sigla (FIS, FIEE, FICA…) con un mapa fijo de nombres oficiales; si no coincide, usa las iniciales.

El texto se lee con separador de línea (`get_text("\n")`) para que decano y subdecano no se peguen.

## Reglas de datos
- Decano, subdecano, misión, visión, departamentos, correo, teléfono y ubicación: si la página no los publica, `NULL`.
- Un nombre de decano o subdecano que sea un correo se descarta.
- Una página que no responde se omite (no se crea un registro con el nombre sacado de la URL).
- **Dato inferido:** la sigla (mapa fijo en el código).

## Configuración
`endpoints.facultades`, `min_records.facultades`.

## Pruebas
`tests/test_scrapers.py::test_facultades_scraper_parse_page`; `tests/test_improvements.py` (sin lista canónica, texto pegado).

## Límites conocidos / pendientes (Fase 2)
- `ubicacion_campus` queda vacío en todas las facultades.
- Algunos correos de contacto son de personas (por ejemplo el de FIM) y no de la facultad.
- Hay un caso especial que reescribe la URL de Ingeniería Civil y Ambiental.

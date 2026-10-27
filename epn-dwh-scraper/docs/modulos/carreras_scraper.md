# `src/scrapers/carreras_scraper.py`

**Estado:** estable (grado) / parcial (posgrado) · **Fase:** 1 → 2

## Propósito
Extrae las carreras de grado y los programas de posgrado (maestrías y doctorados) con su ficha: facultad, título, duración, modalidad, resolución CES y perfiles.

## Entradas y salidas
| | Detalle |
| :-- | :-- |
| Entrada | `oferta-de-grado/`, `oferta-de-posgrado/` y la página de cada programa |
| Salida | `data/interim/carrerasscraper.json` (46 registros: 18 de grado, 28 de posgrado) |

## Cómo funciona
1. `_discover_program_urls()` descubre los programas y asigna un nivel sugerido (Grado, Maestría, Doctorado).
2. `_parse_program_page(url, nivel)` convierte la página en líneas (`page_lines`) y lee la ficha.

### La ficha de grado
El portal la publica como pares "etiqueta / valor" **sin dos puntos**, en elementos consecutivos:

```
Unidad Académica        → Facultad de Ingeniería Mecánica
Título que otorga       → Ingeniera/o en Mecánica
Duración                → Nueve (9) períodos académicos
Modalidad               → Presencial
Resolución de aprobación CES: → RPC-SO-24-No.476-2017
```
Se leen con `extract_labeled_value`. Los años se derivan de los períodos (1 período = 1 semestre).

### Perfiles
`_extract_profiles()` toma solo la **zona de contenido** que sigue a las pestañas `PERFIL DE INGRESO … CONTACTO`:
- `perfil_ingreso`: los párrafos hasta el primer encabezado o viñeta.
- `perfil_egreso`: bloque "Resultados Generales" (solo grado).
- `campo_ocupacional`: solo si existe un encabezado explícito.

## Reglas de datos
| Campo | Regla |
| :-- | :-- |
| duración, modalidad, título, resolución | Solo si la ficha los publica; si no, `NULL` |
| créditos | **Siempre `NULL`**: ninguna página los publica |
| facultad | De `Unidad Académica`; si falta (posgrados), se infiere por palabras del nombre y se marca `campos_inferidos = "facultad"`; si no hay coincidencia, `NULL` |
| perfiles | Solo de la zona de contenido; nunca del menú |
| página sin respuesta | Se omite el programa |

## Configuración
`endpoints.oferta_grado`, `endpoints.oferta_posgrado`, `min_records.carreras`.

## Pruebas
`tests/test_improvements.py`: ficha real (`TestFichaDeCarreraReal`), perfiles sin menú (`TestPerfilesSinMenu`), números en palabras, posgrado sin ficha.

## Límites conocidos / pendientes (Fase 2)
- **Posgrados:** duración, modalidad y facultad no están en la ficha HTML (28 programas). Habría que leer los PDF de la malla u otra fuente. 16 quedan sin facultad.
- **Créditos totales:** sin fuente.
- `perfil_egreso` solo existe para grado; `campo_ocupacional` queda vacío en todos.
- La inferencia de facultad por nombre (solo posgrados) es una aproximación basada en palabras clave.
- "Doctorados" es una sola página que agrupa varios programas.

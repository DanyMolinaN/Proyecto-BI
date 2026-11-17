# `src/utils/helpers.py` y `src/utils/logger.py`

**Estado:** estable · **Fase:** 1

## Propósito
Funciones pequeñas y reutilizables para limpiar texto, leer las fichas del portal y generar claves. `logger.py` configura el registro de eventos.

## Funciones de `helpers.py`
| Función | Qué hace |
| :-- | :-- |
| `clean_text(texto)` | Decodifica entidades HTML, colapsa espacios y saltos de línea. `None` → `""` |
| `remove_accents(texto)` | Quita tildes (para comparar nombres) |
| `extract_email(texto)` / `extract_phone(texto)` | Primer correo / teléfono encontrado, o `None` |
| `page_lines(soup)` | Líneas de texto visibles de una página (sin scripts ni estilos), una por elemento. Evita que textos vecinos queden pegados |
| `extract_labeled_value(lineas, *etiquetas)` | Lee fichas "etiqueta / valor": acepta el valor en la línea siguiente (`Duración` / `Nueve períodos`) o con dos puntos (`Duración: 9`) |
| `extract_duration_periods(texto)` | Número de períodos; entiende dígitos y palabras ("Nueve") |
| `extract_degree_level(nombre, nivel)` | Tecnología, Grado, Maestría o Doctorado |
| `extract_modality(texto)` | Presencial, Dual, En Línea, Semipresencial, Híbrida; **`None` si el texto no la menciona** |
| `generate_surrogate_key(*partes)` | Clave entera determinista (SHA-256, 56 bits). Los nulos cuentan como cadena vacía |

## Reglas de datos
- Ninguna función devuelve un valor por defecto cuando no encuentra el dato: devuelven `None`.
- Las claves de 56 bits se mantienen como enteros; convertirlas a `float` pierde precisión (por eso `cleaning.py` usa `Int64`).

## `logger.py`
`setup_logger(nombre)` devuelve un logger con salida a consola y al archivo `logs/scraper_execution.log` (ignorado por git). Nivel configurable con `LOG_LEVEL`.

## Pruebas
`tests/test_cleaning.py` (clase `TestHelpers`) y `tests/test_improvements.py`.

## Límites conocidos / pendientes (Fase 2)
- `extract_degree_level` clasifica "Ingeniería en tecnologías de la Información" como Tecnología; conviene revisarlo.
- `extract_phone` toma el primer teléfono de la página, que suele ser el institucional.

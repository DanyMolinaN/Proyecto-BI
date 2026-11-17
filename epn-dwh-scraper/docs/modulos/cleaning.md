# `src/transform/cleaning.py`

**Estado:** estable · **Fase:** 1

## Propósito
Convierte los registros de `data/interim/` en las tablas del modelo dimensional (dimensiones y hechos) con claves sustitutas deterministas.

## Entradas y salidas
| | Detalle |
| :-- | :-- |
| Entrada | Listas de diccionarios de cada scraper |
| Salida | DataFrames: `dim_tiempo`, `dim_facultad`, `dim_carrera`, `dim_nivel_formacion`, `dim_modalidad`, `fact_oferta_academica`, `dim_autoridad`, `dim_cargo`, `fact_designacion_autoridades`, `dim_categoria_noticia`, `fact_comunicacion_institucional` |

## Cómo funciona
`DataCleaner` tiene un método por entidad: `build_dim_tiempo`, `clean_facultades`, `clean_carreras`, `clean_autoridades`, `clean_noticias`. En todos:

1. Normaliza texto (`clean_text`); lo vacío pasa a `NULL`.
2. Elimina duplicados por nombre normalizado.
3. Genera claves con `generate_surrogate_key`.
4. Resuelve claves foráneas (por ejemplo carrera → facultad con `_match_facultad_key`).

### Emparejamiento de facultades
`_match_facultad_key` compara ignorando tildes y mayúsculas, en este orden: nombre contenido, sigla, y similitud ≥ 0.8. Así "Facultad de Geología y Petróleos" encuentra "Facultad de Ingeniería Geología y Petróleos". Sin coincidencia devuelve `None`.

### Claves
Las claves foráneas se construyen como `Int64` nullable (`_to_int64`): pasar por `float64` corrompe las claves de 56 bits.

## Reglas de datos
- Métricas (`duracion_periodos`, `duracion_anios`, `creditos`): numéricas o `NULL`. Sin valores por defecto.
- `es_acreditada`: `NULL` (no hay fuente).
- Carrera sin facultad: `facultad_key` `NULL`; **no** se asigna a la primera facultad.
- Autoridades centrales (Rectorado) no tienen facultad: `facultad_key` `NULL`.
- `nivel` y `modalidad` faltantes pasan al miembro explícito `"No especificado"`, porque son claves de dimensión.
- Fecha de noticia ilegible: `tiempo_publicacion_key` `NULL`.
- Fecha de designación y de inicio de vigencia de autoridades: la **fecha de captura**.
- `dim_tiempo`: 2015–2035, un registro por día.

## Pruebas
`tests/test_cleaning.py` y `tests/test_improvements.py` (sin valores inventados, emparejamiento de facultad, precisión de claves).

## Límites conocidos / pendientes (Fase 2)
- La fecha de posesión real de las autoridades no existe en el portal.
- `dim_informacion_institucional` no pasa por limpieza; se carga tal como la extrae el scraper.

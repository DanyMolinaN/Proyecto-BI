# `src/transform/scd2.py`

**Estado:** nuevo en la versión 2 · **Fase:** 1

## Propósito
Mantener el historial de autoridades (Dimensión de Cambio Lento Tipo 2). Cuando un decano o rector cambia, no se sobrescribe: la fila anterior se cierra y se abre una nueva.

## Entradas y salidas
| | Detalle |
| :-- | :-- |
| Entrada | `dim_autoridad` y hechos de la captura actual, más lo ya cargado en la base (o `None` en la primera corrida) |
| Salida | `dim_autoridad` y `fact_designacion_autoridades` completas, con historial |

## Cómo funciona
`apply_scd2(new_dim, new_fact, existing_dim, existing_fact, today)`:

| Situación | Resultado |
| :-- | :-- |
| Primera corrida | Se devuelve la captura tal cual |
| Autoridad sin cambios | Se conserva la fila vigente; los hechos se reasignan a su clave |
| Cambió `titulo_academico`, `correo_contacto` o `biografia` | La fila vigente se cierra (`es_vigente = 0`, `fecha_fin_vigencia = hoy`) y se crea una nueva con clave nueva y `es_vigente = 1` |
| Ya no aparece en el portal | Se cierra su vigencia |
| Persona nueva | Se inserta como vigente |

Clave de negocio: `nombre_completo`. La clave de una versión nueva es `generate_surrogate_key("autoridad", nombre, fecha)`.

Los hechos conservan las filas históricas y se les agregan las de la versión vigente; se deduplica por `designacion_key`.

## Reglas de datos
- **Idempotente:** si nada cambia, correr el pipeline varias veces deja el mismo número de filas.
- `fecha_inicio_vigencia` es la **fecha de la primera captura**, no la de posesión (el portal no la publica).

## Configuración
Ninguna.

## Pruebas
`tests/test_improvements.py::TestScd2`: sin cambios, cambio de atributos, autoridad ausente y ida y vuelta con la base de datos.

## Límites conocidos / pendientes (Fase 2)
- Solo se aplica a `dim_autoridad`; otras dimensiones son Tipo 1 (se reemplazan).
- Dos personas homónimas se tratarían como una.
- Un cambio de cargo de la misma persona genera un hecho nuevo, pero no una versión nueva de la dimensión.

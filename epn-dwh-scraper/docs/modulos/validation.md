# `src/transform/validation.py`

**Estado:** estable · **Fase:** 1

## Propósito
Auditar la calidad de cada tabla y generar `logs/reporte_calidad_datos.md`.

## Entradas y salidas
| | Detalle |
| :-- | :-- |
| Entrada | Un DataFrame, su columna clave, las columnas obligatorias y las claves foráneas |
| Salida | Un perfil por tabla y el reporte en Markdown |

## Cómo funciona
`DataValidator.profile_dataframe(df, tabla, clave, obligatorias, foreign_keys=None)` revisa:

1. **Unicidad** de la clave.
2. **Nulos** por columna.
3. **Columnas obligatorias** sin vacíos.
4. **Integridad referencial:** una FK nula o sin registro padre se cuenta como huérfana.
5. **Valores atípicos:** duración fuera de 2–16 períodos, créditos fuera de 30–400.
6. **Formato de correo.**

`generate_markdown_report()` arma el reporte.

## Reglas de datos
- Estado **CONFORME** u **OBSERVACIONES DETECTADAS** según duplicados, obligatorias vacías, huérfanas o atípicos.
- Las columnas no obligatorias con datos faltantes aparecen como líneas `Info:` con el conteo y porcentaje, **sin cambiar el estado**. Así se ve la realidad del portal sin marcar todo como error.

## Configuración
Ninguna.

## Pruebas
`tests/test_validation.py` y `tests/test_improvements.py::TestValidadorIntegridad`.

## Límites conocidos / pendientes (Fase 2)
- Los rangos de duración y créditos son fijos.
- `fact_oferta_academica` queda en OBSERVACIONES mientras haya carreras sin facultad (16 de 46).
- El reporte se reescribe en cada ejecución; no guarda historial de calidad.

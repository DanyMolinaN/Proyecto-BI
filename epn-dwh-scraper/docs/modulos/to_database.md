# `src/load/to_database.py`

**Estado:** funcional, con pendientes · **Fase:** 1 → 2

## Propósito
Cargar las tablas en una base relacional: SQLite por defecto (`data/epn_dwh.db`), compatible con PostgreSQL mediante SQLAlchemy.

## Entradas y salidas
| | Detalle |
| :-- | :-- |
| Entrada | Diccionario `{nombre_tabla: DataFrame}` |
| Salida | Tablas en la base; conteo de filas por tabla |

## Cómo funciona
- `load_all(tablas)` carga primero las dimensiones (`dim_*`), luego otras y al final los hechos (`fact_*`).
- `load_table(df, nombre, if_exists="replace")` usa `DataFrame.to_sql`.
- `read_table(nombre)` lee una tabla existente o devuelve `None` si no existe. Lo usa el SCD2 para conocer el historial.
- `get_table_counts()` cuenta filas usando el inspector de SQLAlchemy y escapa el nombre de la tabla.
- `execute_sql_file(ruta)` ejecuta un script `.sql` (hoy el pipeline no lo usa).

## Reglas de datos
Las tablas se **reemplazan** en cada carga. El historial de autoridades se conserva porque `scd2.py` entrega la tabla completa (histórico + vigente) antes de cargar.

## Configuración
`DATABASE_URL` en `.env`, o `storage.database_url` en `settings.yaml`. Una cadena con contraseña va **solo** en `.env`.

## Pruebas
`tests/test_improvements.py::TestScd2::test_round_trip_con_base_de_datos`.

## Límites conocidos / pendientes (Fase 2)
- **Los scripts de `sql/` (claves primarias y foráneas, índices) no se aplican** a la base real, porque `to_sql(replace)` recrea las tablas sin restricciones.
- `fact_oferta_academica` y `fact_comunicacion_institucional` son instantáneas: se pierde la evolución en el tiempo.
- Sin transacción global: si falla una tabla a mitad, las anteriores ya quedaron cargadas.

# `src/load/to_csv.py`

**Estado:** estable · **Fase:** 1

## Propósito
Exportar cada tabla a un CSV en UTF-8, para herramientas como Power BI, Tableau o Metabase.

## Entradas y salidas
| | Detalle |
| :-- | :-- |
| Entrada | Diccionario `{nombre_tabla: DataFrame}` |
| Salida | `data/processed/<tabla>.csv` |

## Cómo funciona
`CsvLoader.load_all(tablas)` llama a `load_table` por cada una. Es idempotente: sobrescribe el archivo. Una tabla vacía genera un CSV solo con la cabecera si el DataFrame tiene columnas.

## Reglas de datos
Los `NULL` se escriben como celdas vacías. No transforma datos.

## Configuración
`paths.data_processed`.

## Pruebas
Sin prueba directa.

## Límites conocidos / pendientes (Fase 2)
- Los CSV están en `.gitignore`; se regeneran con el pipeline.
- Falta una prueba que verifique el contenido de los archivos.

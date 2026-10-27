# Reporte de Calidad y Perfilamiento de Datos

## Resumen Ejecutivo de Auditoria
El presente reporte consolida los controles aplicados sobre el conjunto de dimensiones y tablas de hechos del Data Warehouse institucional de la EPN.

| Tabla | Registros | Claves Duplicadas | Nulos Totales | Estado |
| :--- | :--- | :--- | :--- | :--- |
| dim_tiempo | 7670 | 0 | 0 | CONFORME |
| dim_facultad | 9 | 0 | 15 | CONFORME |
| dim_carrera | 46 | 0 | 152 | CONFORME |
| dim_nivel_formacion | 4 | 0 | 0 | CONFORME |
| dim_modalidad | 2 | 0 | 0 | CONFORME |
| fact_oferta_academica | 46 | 0 | 164 | OBSERVACIONES DETECTADAS |
| dim_autoridad | 10 | 0 | 20 | CONFORME |
| dim_cargo | 10 | 0 | 0 | CONFORME |
| fact_designacion_autoridades | 10 | 0 | 1 | CONFORME |
| dim_categoria_noticia | 4 | 0 | 0 | CONFORME |
| fact_comunicacion_institucional | 30 | 0 | 0 | CONFORME |

## Detalle de Observaciones y Reglas Evaluadas
### dim_tiempo
- Todos los controles de integridad, tipo de dato y unicidad resultaron conformes.

### dim_facultad
- Info: decano sin dato en 1 de 9 registros (11%).
- Info: subdecano sin dato en 4 de 9 registros (44%).
- Info: departamentos_adscritos sin dato en 1 de 9 registros (11%).
- Info: ubicacion_campus sin dato en 9 de 9 registros (100%).

### dim_carrera
- Info: titulo_otorga sin dato en 28 de 46 registros (61%).
- Info: codigo_resolucion sin dato en 28 de 46 registros (61%).
- Info: perfil_ingreso sin dato en 1 de 46 registros (2%).
- Info: perfil_egreso sin dato en 31 de 46 registros (67%).
- Info: campo_ocupacional sin dato en 46 de 46 registros (100%).
- Info: campos_inferidos sin dato en 18 de 46 registros (39%).

### dim_nivel_formacion
- Todos los controles de integridad, tipo de dato y unicidad resultaron conformes.

### dim_modalidad
- Todos los controles de integridad, tipo de dato y unicidad resultaron conformes.

### fact_oferta_academica
- 16 registros con facultad_key nula o sin registro en la dimension referenciada.
- Info: facultad_key sin dato en 16 de 46 registros (35%).
- Info: duracion_periodos sin dato en 28 de 46 registros (61%).
- Info: duracion_anios sin dato en 28 de 46 registros (61%).
- Info: creditos_totales sin dato en 46 de 46 registros (100%).
- Info: es_acreditada sin dato en 46 de 46 registros (100%).

### dim_autoridad
- Info: correo_contacto sin dato en 10 de 10 registros (100%).
- Info: biografia sin dato en 10 de 10 registros (100%).

### dim_cargo
- Todos los controles de integridad, tipo de dato y unicidad resultaron conformes.

### fact_designacion_autoridades
- Info: facultad_key sin dato en 1 de 10 registros (10%).

### dim_categoria_noticia
- Todos los controles de integridad, tipo de dato y unicidad resultaron conformes.

### fact_comunicacion_institucional
- Todos los controles de integridad, tipo de dato y unicidad resultaron conformes.

# Justificacion y Diseño del Modelo Dimensional para el Data Warehouse de la EPN

## 1. Fundamentacion Metodologica
El diseño del Data Warehouse institucional para la Escuela Politécnica Nacional (EPN) sigue la metodología dimensional de Ralph Kimball. En el contexto de Business Intelligence (BI) e ingeniería de datos universitarios, los modelos normalizados en Tercera Forma Normal (3NF) propios de los sistemas operacionales transaccionales (OLTP) resultan ineficientes para el análisis de toma de decisiones debido al exceso de combinaciones de tablas (JOINs), la complejidad en las consultas agregadas y el rendimiento degradado en tableros analíticos.

Se ha seleccionado un **Esquema de Constelacion de Hechos (Fact Constellation Schema)**, compuesto por tablas de hechos centradas en los tres procesos sustantivos identificados en el portal web institucional:
1. **Oferta y Planificacion Academica (`fact_oferta_academica`)**: Analiza la distribución de titulaciones de tercer nivel, tecnologías y programas de posgrado, contrastando duración, periodicidad y modalidad pedagógica.
2. **Gobernanza y Ejercicio del Poder Directivo (`fact_designacion_autoridades`)**: Audita la asignación de autoridades centrales y decanales, permitiendo monitorear la estabilidad institucional y la proporción de autoridades titulares frente a encargadas.
3. **Comunicacion, Investigacion y Eventos (`fact_comunicacion_institucional`)**: Mide el volumen, la periodicidad y los focos temáticos de la divulgación oficial politécnica (convocatorias, logros científicos, convenios).

Las dimensiones conformadas (`dim_facultad`, `dim_tiempo`) son compartidas entre las diferentes tablas de hechos, garantizando consistencia semántica en los tableros analíticos cruzados (Drill-Across).

---

## 2. Granularidad de las Tablas de Hechos

### 2.1 `fact_oferta_academica`
- **Granularidad**: Un registro atómico por cada carrera o programa formativo individual aprobado y ofertado por la EPN, categorizado por facultad, nivel formativo, modalidad y periodo de extracción.
- **Tipo de Métricas**:
  - `duracion_periodos`: Métrica aditiva (promediable por nivel o facultad).
  - `duracion_anios`: Métrica aditiva.
  - `creditos_totales`: Métrica semiaditiva (relevante para promedios curriculares).
  - `es_acreditada`: Indicador booleano (1 o 0) para agregaciones de conformidad de calidad.

### 2.2 `fact_designacion_autoridades`
- **Granularidad**: Un registro por cada nombramiento formal de una persona natural en una función directiva u órgano colegiado dentro de una unidad institucional específica.
- **Tipo de Métricas**:
  - `es_titular`: Indicador booleano (1 para designación titular, 0 para encargo o subrogación temporal "(E)").

### 2.3 `fact_comunicacion_institucional`
- **Granularidad**: Un registro por cada publicación, convocatoria o noticia institucional emitida por la EPN y registrada en el portal web o en su feed estructurado.
- **Tipo de Métricas**:
  - `longitud_caracteres`: Métrica cuantitativa aditiva.
  - `conteo_palabras`: Métrica cuantitativa aditiva.

---

## 3. Estrategia de Claves Sustitutas (Surrogate Keys)
En lugar de depender exclusivamente de claves naturales de los sistemas transaccionales (como nombres de personas o URLs que pueden sufrir modificaciones ortográficas o reestructuraciones de servidores web), se implementan **claves sustitutas deterministas** generadas mediante algoritmos de hashing seguro (SHA-256) acotados a enteros de 64 bits.

Ventajas para la arquitectura BI:
1. **Idempotencia total**: La ejecución repetida del proceso ETL sobre los mismos registros produce exactamente las mismas claves primarias y foráneas, evitando duplicados sin necesidad de secuencias de autoincremento que varíen entre motores.
2. **Independencia tecnológica**: Facilita la migración transparente entre motores relacionales (SQLite local, PostgreSQL en la nube, BigQuery o Snowflake).
3. **Aislamiento de fuentes**: Si una URL o un cargo cambia de redacción en el portal web, la integridad referencial histórica del Data Warehouse se preserva.

---

## 4. Estrategia de Dimensiones de Cambio Lento (SCD)

### 4.1 SCD Tipo 2 para `dim_autoridad`
La gobernanza universitaria presenta relevos periódicos de autoridades (elecciones de rector, designación de vicerrectores, decanos y subdecanos). Si un decano culmina su periodo y asume una nueva autoridad, sobrescribir el registro (SCD Tipo 1) provocaría la pérdida de la memoria institucional y distorsionaría las métricas históricas de gestión.

Por tanto, `dim_autoridad` implementa **SCD Tipo 2**:
- Atributo `es_vigente`: Bandera binaria (1 para la autoridad actualmente en funciones, 0 para directivos históricos).
- Atributo `fecha_inicio_vigencia`: Fecha de posesión del cargo.
- Atributo `fecha_fin_vigencia`: Fecha de cierre del mandato (por defecto '9999-12-31' para designaciones activas).

### 4.2 SCD Tipo 1 para `dim_facultad` y `dim_carrera`
Para atributos descriptivos de unidades académicas y carreras (misión, visión, teléfono, página web), se emplea **SCD Tipo 1** (sobrescritura controlada), manteniendo actualizada la ficha de contacto y presentación oficial sin duplicar registros de catálogo.

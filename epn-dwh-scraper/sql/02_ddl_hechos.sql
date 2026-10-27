-- ============================================================================
-- PROYECTO: DATA WAREHOUSE INSTITUCIONAL ESCUELA POLITECNICA NACIONAL (EPN)
-- SCRIPT: 02_ddl_hechos.sql
-- DESCRIPCION: Definicion del Esquema DDL para las Tablas de Hechos (Fact Tables)
-- ESTILO: Compatible con SQLite y PostgreSQL (ANSI SQL estandar)
-- ============================================================================

-- 1. TABLA DE HECHOS: OFERTA ACADEMICA INSTITUCIONAL
-- Granularidad: Un registro por carrera/programa ofertado formalmente por la EPN.
-- Proposito analitico: Analisis de cobertura de titulaciones, duracion, creditaje
-- y distribucion por facultad y modalidad.
CREATE TABLE IF NOT EXISTS fact_oferta_academica (
    oferta_key BIGINT PRIMARY KEY,
    carrera_key BIGINT NOT NULL,
    facultad_key BIGINT,
    nivel_key BIGINT NOT NULL,
    modalidad_key BIGINT NOT NULL,
    tiempo_extraccion_key INTEGER NOT NULL,
    duracion_periodos INTEGER,
    duracion_anios REAL,
    creditos_totales INTEGER,
    es_acreditada INTEGER,
    FOREIGN KEY (carrera_key) REFERENCES dim_carrera(carrera_key),
    FOREIGN KEY (facultad_key) REFERENCES dim_facultad(facultad_key),
    FOREIGN KEY (nivel_key) REFERENCES dim_nivel_formacion(nivel_key),
    FOREIGN KEY (modalidad_key) REFERENCES dim_modalidad(modalidad_key),
    FOREIGN KEY (tiempo_extraccion_key) REFERENCES dim_tiempo(tiempo_key)
);

-- Indices para optimizacion de consultas OLAP en oferta academica
CREATE INDEX IF NOT EXISTS idx_fact_oferta_facultad ON fact_oferta_academica(facultad_key);
CREATE INDEX IF NOT EXISTS idx_fact_oferta_nivel ON fact_oferta_academica(nivel_key);
CREATE INDEX IF NOT EXISTS idx_fact_oferta_modalidad ON fact_oferta_academica(modalidad_key);


-- 2. TABLA DE HECHOS: DESIGNACION Y GOBIERNO DE AUTORIDADES
-- Granularidad: Un nombramiento o designacion de una autoridad en un cargo y unidad academica.
-- Proposito analitico: Auditoria de gobernanza, estabilidad de cargos directivos
-- y seguimiento de autoridades titulares frente a encargadas.
CREATE TABLE IF NOT EXISTS fact_designacion_autoridades (
    designacion_key BIGINT PRIMARY KEY,
    autoridad_key BIGINT NOT NULL,
    cargo_key BIGINT NOT NULL,
    facultad_key BIGINT NOT NULL,
    es_titular INTEGER NOT NULL, -- 1 si titular, 0 si es encargado "(E)" o subrogante
    tiempo_designacion_key INTEGER NOT NULL,
    FOREIGN KEY (autoridad_key) REFERENCES dim_autoridad(autoridad_key),
    FOREIGN KEY (cargo_key) REFERENCES dim_cargo(cargo_key),
    FOREIGN KEY (facultad_key) REFERENCES dim_facultad(facultad_key),
    FOREIGN KEY (tiempo_designacion_key) REFERENCES dim_tiempo(tiempo_key)
);

-- Indices para optimizacion de consultas OLAP en autoridades
CREATE INDEX IF NOT EXISTS idx_fact_aut_cargo ON fact_designacion_autoridades(cargo_key);
CREATE INDEX IF NOT EXISTS idx_fact_aut_facultad ON fact_designacion_autoridades(facultad_key);


-- 3. TABLA DE HECHOS: COMUNICACION Y EVENTOS INSTITUCIONALES
-- Granularidad: Un articulo, convocatoria o noticia publicada en los portales oficiales.
-- Proposito analitico: Medicion del volumen informativo, areas tematicas de mayor difusion
-- y calendario de divulgacion institucional.
CREATE TABLE IF NOT EXISTS fact_comunicacion_institucional (
    noticia_key BIGINT PRIMARY KEY,
    categoria_key BIGINT NOT NULL,
    tiempo_publicacion_key INTEGER NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    longitud_caracteres INTEGER NOT NULL,
    conteo_palabras INTEGER NOT NULL,
    url VARCHAR(255) NOT NULL,
    FOREIGN KEY (categoria_key) REFERENCES dim_categoria_noticia(categoria_key),
    FOREIGN KEY (tiempo_publicacion_key) REFERENCES dim_tiempo(tiempo_key)
);

CREATE INDEX IF NOT EXISTS idx_fact_noticia_cat ON fact_comunicacion_institucional(categoria_key);
CREATE INDEX IF NOT EXISTS idx_fact_noticia_tiempo ON fact_comunicacion_institucional(tiempo_publicacion_key);

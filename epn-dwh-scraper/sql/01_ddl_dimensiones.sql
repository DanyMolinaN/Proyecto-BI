-- ============================================================================
-- PROYECTO: DATA WAREHOUSE INSTITUCIONAL ESCUELA POLITECNICA NACIONAL (EPN)
-- SCRIPT: 01_ddl_dimensiones.sql
-- DESCRIPCION: Definicion del Esquema DDL para las Tablas de Dimensiones
-- ESTILO: Compatible con SQLite y PostgreSQL (ANSI SQL estandar)
-- ============================================================================

-- 1. DIMENSION FACULTAD (Unidades Academicas y Escuelas)
-- Granularidad: Un registro por facultad o escuela adscrita a la EPN.
CREATE TABLE IF NOT EXISTS dim_facultad (
    facultad_key BIGINT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    sigla VARCHAR(20) NOT NULL,
    decano VARCHAR(120) DEFAULT 'No especificado',
    subdecano VARCHAR(120) DEFAULT 'No especificado',
    descripcion TEXT,
    mision TEXT,
    vision TEXT,
    url VARCHAR(255) NOT NULL,
    departamentos_adscritos TEXT,
    contacto_correo VARCHAR(100),
    contacto_telefono VARCHAR(50),
    ubicacion_campus VARCHAR(150)
);

-- 2. DIMENSION NIVEL DE FORMACION
-- Granularidad: Un registro por nivel formativo segun clasificacion LOES/CES.
CREATE TABLE IF NOT EXISTS dim_nivel_formacion (
    nivel_key BIGINT PRIMARY KEY,
    codigo_nivel VARCHAR(10) NOT NULL,
    nombre_nivel VARCHAR(50) NOT NULL,
    ciclo_academico VARCHAR(30) NOT NULL
);

-- 3. DIMENSION MODALIDAD DE ESTUDIO
-- Granularidad: Un registro por modalidad pedagogica autorizada.
CREATE TABLE IF NOT EXISTS dim_modalidad (
    modalidad_key BIGINT PRIMARY KEY,
    nombre_modalidad VARCHAR(50) NOT NULL,
    descripcion VARCHAR(255)
);

-- 4. DIMENSION CARRERA / PROGRAMA ACADEMICO
-- Granularidad: Un registro por programa curricular de tercer o cuarto nivel.
CREATE TABLE IF NOT EXISTS dim_carrera (
    carrera_key BIGINT PRIMARY KEY,
    nombre_carrera VARCHAR(180) NOT NULL,
    titulo_otorga VARCHAR(180) NOT NULL,
    codigo_resolucion VARCHAR(60),
    perfil_ingreso TEXT,
    perfil_egreso TEXT,
    campo_ocupacional TEXT,
    malla_curricular_url VARCHAR(255),
    url_carrera VARCHAR(255)
);

-- 5. DIMENSION CARGO DIRECTIVO
-- Granularidad: Un registro por cargo universitario o rol de gobierno institucional.
CREATE TABLE IF NOT EXISTS dim_cargo (
    cargo_key BIGINT PRIMARY KEY,
    nombre_cargo VARCHAR(100) NOT NULL,
    tipo_gobierno VARCHAR(50) NOT NULL
);

-- 6. DIMENSION AUTORIDAD (Dimension con Cambios Lentos - SCD Tipo 2)
-- Granularidad: Un registro por directivo con atributos de vigencia temporal.
CREATE TABLE IF NOT EXISTS dim_autoridad (
    autoridad_key BIGINT PRIMARY KEY,
    nombre_completo VARCHAR(150) NOT NULL,
    titulo_academico VARCHAR(50),
    correo_contacto VARCHAR(100),
    biografia TEXT,
    es_vigente INTEGER DEFAULT 1,
    fecha_inicio_vigencia VARCHAR(10) NOT NULL,
    fecha_fin_vigencia VARCHAR(10) DEFAULT '9999-12-31'
);

-- 7. DIMENSION CATEGORIA NOTICIA
-- Granularidad: Un registro por categoria temática de comunicacion institucional.
CREATE TABLE IF NOT EXISTS dim_categoria_noticia (
    categoria_key BIGINT PRIMARY KEY,
    nombre_categoria VARCHAR(100) NOT NULL
);

-- 8. DIMENSION TIEMPO (Calendario Analitico)
-- Granularidad: Un registro por dia calendario.
CREATE TABLE IF NOT EXISTS dim_tiempo (
    tiempo_key INTEGER PRIMARY KEY,
    fecha VARCHAR(10) NOT NULL,
    anio INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    mes_nombre VARCHAR(20) NOT NULL,
    trimestre INTEGER NOT NULL,
    semestre INTEGER NOT NULL,
    dia INTEGER NOT NULL,
    dia_semana VARCHAR(20) NOT NULL,
    es_fin_de_semana INTEGER NOT NULL
);

-- 9. TABLA AUXILIAR: INFORMACION FILOSOFICA E INFRAESTRUCTURA CIENTIFICA
-- Granularidad: Un registro por hito historico, centro de investigacion o directriz de identidad.
CREATE TABLE IF NOT EXISTS dim_informacion_institucional (
    id_registro INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria VARCHAR(50) NOT NULL,
    clave VARCHAR(100) NOT NULL,
    contenido TEXT NOT NULL,
    metadato TEXT,
    url VARCHAR(255)
);

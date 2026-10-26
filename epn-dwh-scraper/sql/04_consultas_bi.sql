-- ============================================================================
-- PROYECTO: DATA WAREHOUSE INSTITUCIONAL ESCUELA POLITECNICA NACIONAL (EPN)
-- SCRIPT: 04_consultas_bi.sql
-- DESCRIPCION: Consultas Analiticas OLAP para Soporte de Decisiones y Reporteria BI
-- ============================================================================

-- ----------------------------------------------------------------------------
-- CONSULTA 1: Oferta Academica Total por Facultad y Nivel de Formacion
-- PREGUNTA DE NEGOCIO: ¿Como se distribuyen los programas academicos entre grado,
-- maestria y doctorado a traves de las facultades de la EPN?
-- PROPOSITO ANALITICO: Identificar la diversificacion y especializacion de cada facultad.
-- ----------------------------------------------------------------------------
SELECT 
    f.sigla AS Sigla_Facultad,
    f.nombre AS Nombre_Facultad,
    n.nombre_nivel AS Nivel_Formacion,
    COUNT(fo.oferta_key) AS Cantidad_Programas,
    ROUND(AVG(fo.duracion_periodos), 1) AS Promedio_Periodos,
    ROUND(AVG(fo.creditos_totales), 1) AS Promedio_Creditos
FROM fact_oferta_academica fo
JOIN dim_facultad f ON fo.facultad_key = f.facultad_key
JOIN dim_nivel_formacion n ON fo.nivel_key = n.nivel_key
GROUP BY f.sigla, f.nombre, n.nombre_nivel
ORDER BY f.sigla, Cantidad_Programas DESC;


-- ----------------------------------------------------------------------------
-- CONSULTA 2: Distribucion Porcentual de la Oferta Academica segun Modalidad
-- PREGUNTA DE NEGOCIO: ¿Que proporcion de la oferta academica corresponde a
-- modalidad presencial, dual o en linea?
-- PROPOSITO ANALITICO: Evaluar el grado de transformacion digital y adopcion de
-- modalidades no tradicionales en la universidad.
-- ----------------------------------------------------------------------------
SELECT 
    m.nombre_modalidad AS Modalidad,
    COUNT(fo.oferta_key) AS Total_Programas,
    ROUND(COUNT(fo.oferta_key) * 100.0 / (SELECT COUNT(*) FROM fact_oferta_academica), 2) AS Porcentaje_Total
FROM fact_oferta_academica fo
JOIN dim_modalidad m ON fo.modalidad_key = m.modalidad_key
GROUP BY m.nombre_modalidad
ORDER BY Total_Programas DESC;


-- ----------------------------------------------------------------------------
-- CONSULTA 3: Ranking de Carreras con Mayor Duracion Curricular y Carga de Creditos
-- PREGUNTA DE NEGOCIO: ¿Cuales son los 10 programas con mayor exigencia temporal
-- y creditaje academico en toda la institucion?
-- PROPOSITO ANALITICO: Planificacion docente, asignacion de aulas y dimensionamiento
-- de laboratorios para programas de larga duracion.
-- ----------------------------------------------------------------------------
SELECT 
    c.nombre_carrera AS Programa_Academico,
    f.sigla AS Facultad,
    n.nombre_nivel AS Nivel,
    m.nombre_modalidad AS Modalidad,
    fo.duracion_periodos AS Semestres_Periodos,
    fo.duracion_anios AS Anios_Estimados,
    fo.creditos_totales AS Creditos
FROM fact_oferta_academica fo
JOIN dim_carrera c ON fo.carrera_key = c.carrera_key
JOIN dim_facultad f ON fo.facultad_key = f.facultad_key
JOIN dim_nivel_formacion n ON fo.nivel_key = n.nivel_key
JOIN dim_modalidad m ON fo.modalidad_key = m.modalidad_key
ORDER BY fo.duracion_periodos DESC, fo.creditos_totales DESC
LIMIT 10;


-- ----------------------------------------------------------------------------
-- CONSULTA 4: Composicion de Autoridades por Tipo de Gobierno y Dependencia
-- PREGUNTA DE NEGOCIO: ¿Cuantas autoridades directivas se encuentran registradas
-- en cada nivel institucional (Gobierno Central vs. Facultades)?
-- PROPOSITO ANALITICO: Transparencia institucional y control del organigrama directivo.
-- ----------------------------------------------------------------------------
SELECT 
    cg.tipo_gobierno AS Nivel_Gobierno,
    cg.nombre_cargo AS Cargo,
    COUNT(fda.autoridad_key) AS Cantidad_Autoridades
FROM fact_designacion_autoridades fda
JOIN dim_cargo cg ON fda.cargo_key = cg.cargo_key
GROUP BY cg.tipo_gobierno, cg.nombre_cargo
ORDER BY cg.tipo_gobierno, Cantidad_Autoridades DESC;


-- ----------------------------------------------------------------------------
-- CONSULTA 5: Deteccion de Cargos con Nombramiento Encargado "(E)" vs. Titular
-- PREGUNTA DE NEGOCIO: ¿Que porcentaje de directivos y vicerrectores operan bajo
-- figura de encargo o subrogacion frente a nombramientos titulares definitivos?
-- PROPOSITO ANALITICO: Auditoria y seguimiento de gobernanza para comite electoral
-- y acreditacion institucional del CACES.
-- ----------------------------------------------------------------------------
SELECT 
    CASE WHEN fda.es_titular = 1 THEN 'Nombramiento Titular' ELSE 'Encargo / Subrogante (E)' END AS Condicion_Designacion,
    COUNT(*) AS Conteo_Cargos,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM fact_designacion_autoridades), 2) AS Porcentaje
FROM fact_designacion_autoridades fda
GROUP BY fda.es_titular;


-- ----------------------------------------------------------------------------
-- CONSULTA 6: Relacion de Autoridades Decanales por Unidad Academica y Contacto Oficial
-- PREGUNTA DE NEGOCIO: ¿Quienes son las maximas autoridades en cada facultad y cuales
-- son sus canales de contacto institucional para gestion ciudadana o estudiantil?
-- PROPOSITO ANALITICO: Generacion de directorios analiticos de atencion ciudadana.
-- ----------------------------------------------------------------------------
SELECT 
    f.sigla AS Sigla_Facultad,
    f.nombre AS Unidad_Academica,
    a.nombre_completo AS Autoridad,
    cg.nombre_cargo AS Cargo,
    a.correo_contacto AS Correo_Institucional,
    f.contacto_telefono AS Telefono_Campus,
    f.ubicacion_campus AS Ubicacion_Fisica
FROM fact_designacion_autoridades fda
JOIN dim_facultad f ON fda.facultad_key = f.facultad_key
JOIN dim_autoridad a ON fda.autoridad_key = a.autoridad_key
JOIN dim_cargo cg ON fda.cargo_key = cg.cargo_key
WHERE a.es_vigente = 1
ORDER BY f.sigla;


-- ----------------------------------------------------------------------------
-- CONSULTA 7: Volumen y Tipologia de Comunicaciones Institucionales y Noticias
-- PREGUNTA DE NEGOCIO: ¿Cuales son las areas tematicas mas activas en difusion
-- oficial (investigacion, convocatorias laborales, resoluciones de gobierno)?
-- PROPOSITO ANALITICO: Evaluacion del impacto mediatico y transparencia institucional.
-- ----------------------------------------------------------------------------
SELECT 
    cat.nombre_categoria AS Categoria_Noticia,
    COUNT(fc.noticia_key) AS Total_Publicaciones,
    ROUND(AVG(fc.longitud_caracteres), 0) AS Longitud_Promedio_Caracteres,
    ROUND(AVG(fc.conteo_palabras), 0) AS Palabras_Promedio
FROM fact_comunicacion_institucional fc
JOIN dim_categoria_noticia cat ON fc.categoria_key = cat.categoria_key
GROUP BY cat.nombre_categoria
ORDER BY Total_Publicaciones DESC;


-- ----------------------------------------------------------------------------
-- CONSULTA 8: Matriz de Cobertura Integral de Facultades (Tercer Nivel vs Cuarto Nivel)
-- PREGUNTA DE NEGOCIO: ¿Cuales facultades ofrecen formacion completa desde grado
-- hasta posgrado (maestria o doctorado) y cuantas carreras tienen en cada ciclo?
-- PROPOSITO ANALITICO: Fomentar el desarrollo de oferta doctoral en unidades que
-- solo poseen programas de tercer nivel.
-- ----------------------------------------------------------------------------
SELECT 
    f.sigla AS Sigla,
    f.nombre AS Facultad,
    SUM(CASE WHEN n.nombre_nivel IN ('Grado', 'Tecnologia') THEN 1 ELSE 0 END) AS Carreras_Pregrado_Tecnologia,
    SUM(CASE WHEN n.nombre_nivel IN ('Maestria', 'Doctorado') THEN 1 ELSE 0 END) AS Programas_Posgrado,
    COUNT(fo.oferta_key) AS Total_Programas_Unidad,
    CASE 
        WHEN SUM(CASE WHEN n.nombre_nivel IN ('Maestria', 'Doctorado') THEN 1 ELSE 0 END) > 0 
             AND SUM(CASE WHEN n.nombre_nivel IN ('Grado', 'Tecnologia') THEN 1 ELSE 0 END) > 0 
        THEN 'Cobertura Integral (Pregrado y Posgrado)'
        WHEN SUM(CASE WHEN n.nombre_nivel IN ('Maestria', 'Doctorado') THEN 1 ELSE 0 END) > 0 
        THEN 'Solo Posgrado'
        ELSE 'Solo Pregrado/Tecnologia'
    END AS Estado_Cobertura
FROM fact_oferta_academica fo
JOIN dim_facultad f ON fo.facultad_key = f.facultad_key
JOIN dim_nivel_formacion n ON fo.nivel_key = n.nivel_key
GROUP BY f.sigla, f.nombre
ORDER BY Total_Programas_Unidad DESC;

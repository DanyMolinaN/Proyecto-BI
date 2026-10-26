-- ============================================================================
-- PROYECTO: DATA WAREHOUSE INSTITUCIONAL ESCUELA POLITECNICA NACIONAL (EPN)
-- SCRIPT: 03_carga_ejemplo.sql
-- DESCRIPCION: Insercion de datos sinteticos representativos para pruebas del DWH
-- ============================================================================

-- 1. CARGA EN DIM_TIEMPO
INSERT OR REPLACE INTO dim_tiempo (tiempo_key, fecha, anio, mes, mes_nombre, trimestre, semestre, dia, dia_semana, es_fin_de_semana)
VALUES 
(20261025, '2026-10-25', 2026, 10, 'Octubre', 4, 2, 25, 'Sunday', 1),
(20261026, '2026-10-26', 2026, 10, 'Octubre', 4, 2, 26, 'Monday', 0),
(20231101, '2023-11-01', 2023, 11, 'Noviembre', 4, 2, 1, 'Wednesday', 0);

-- 2. CARGA EN DIM_FACULTAD
INSERT OR REPLACE INTO dim_facultad (facultad_key, nombre, sigla, decano, subdecano, descripcion, mision, vision, url, departamentos_adscritos, contacto_correo, contacto_telefono, ubicacion_campus)
VALUES 
(1001, 'Facultad de Ingenieria de Sistemas', 'FIS', 'Dra. Rosa Navarrete', 'Dr. Denys Flores', 'Referente en ciencias de la computacion y software.', 'Formar profesionales lideres en TIC.', 'Liderazgo regional en innovacion digital.', 'https://www.epn.edu.ec/facultad-ingenieria-de-sistemas/', 'Departamento de Informatica y Ciencias de la Computacion (DICC)', 'fis@epn.edu.ec', '(+593) 2 2976 300', 'Edificio de Sistemas, Campus Politecnico'),
(1002, 'Facultad de Ingenieria Civil y Ambiental', 'FICA', 'Dr. Jorge Toapaxi', 'No especificado', 'Lider en infraestructura y gestion ambiental.', 'Excelencia en desarrollo de infraestructura sostenible.', 'Pilar del desarrollo territorial del pais.', 'https://www.epn.edu.ec/facultad-ingenieria-civil-ambiental/', 'Departamento de Ingenieria Civil; Departamento de Ingenieria Ambiental', 'fica@epn.edu.ec', '(+593) 2 2976 300', 'Edificio Nro. 11, Campus Politecnico'),
(1003, 'Facultad de Ciencias', 'FC', 'Dr. Juan Pablo Diaz', 'No especificado', 'Unidad rectora en matematicas, fisica y economia.', 'Impulsar las ciencias basicas y cuantitativas.', 'Excelencia investigativa de trascendencia mundial.', 'https://www.epn.edu.ec/facultad-ciencias/', 'Departamento de Matematica; Departamento de Fisica', 'ciencias@epn.edu.ec', '(+593) 2 2976 300', 'Edificio Nro. 12, Campus Politecnico');

-- 3. CARGA EN DIM_NIVEL_FORMACION
INSERT OR REPLACE INTO dim_nivel_formacion (nivel_key, codigo_nivel, nombre_nivel, ciclo_academico)
VALUES 
(201, 'GRA', 'Grado', 'Tercer Nivel'),
(202, 'POS', 'Maestria', 'Cuarto Nivel'),
(203, 'DOC', 'Doctorado', 'Cuarto Nivel'),
(204, 'TEC', 'Tecnologia', 'Tercer Nivel');

-- 4. CARGA EN DIM_MODALIDAD
INSERT OR REPLACE INTO dim_modalidad (modalidad_key, nombre_modalidad, descripcion)
VALUES 
(301, 'Presencial', 'Regimen regular en campus universitario con asistencia a laboratorios.'),
(302, 'Dual', 'Formacion teorica combinada con practica empresarial intensiva.'),
(303, 'En Linea', 'Modalidad mediada enteramente por entornos virtuales de aprendizaje.');

-- 5. CARGA EN DIM_CARRERA
INSERT OR REPLACE INTO dim_carrera (carrera_key, nombre_carrera, titulo_otorga, codigo_resolucion, perfil_ingreso, perfil_egreso, campo_ocupacional, malla_curricular_url, url_carrera)
VALUES 
(401, 'Ingenieria en Software', 'Ingeniero/a en Software', 'RPC-SO-33-No.639-2016', 'Aptitud logico-matematica y vocacion tecnologica.', 'Capacidad para diseñar y liderar sistemas de software complejos.', 'Arquitectura de software, DevOps, gestion tecnologica.', 'https://www.epn.edu.ec/ingenieria-en-software/', 'https://www.epn.edu.ec/ingenieria-en-software/'),
(402, 'Ingenieria Civil', 'Ingeniero/a Civil', 'RPC-SO-12-No.220-2017', 'Vocacion por el diseño y calculo estructural.', 'Diseño, construccion y fiscalizacion de megaproyectos.', 'Obras civiles, hidraulica, sismorresistencia.', 'https://www.epn.edu.ec/ingenieria-civil/', 'https://www.epn.edu.ec/ingenieria-civil/'),
(403, 'Maestria en Inteligencia Artificial', 'Magister en Inteligencia Artificial', 'RPC-SO-05-No.105-2022', 'Grado en computacion, ingenieria o ciencias exactas.', 'Especialista en machine learning, NLP y vision por computador.', 'Centros de I+D, industria de software avanzado.', 'https://www.epn.edu.ec/maestria-en-inteligencia-artificial/', 'https://www.epn.edu.ec/maestria-en-inteligencia-artificial/');

-- 6. CARGA EN DIM_CARGO
INSERT OR REPLACE INTO dim_cargo (cargo_key, nombre_cargo, tipo_gobierno)
VALUES 
(501, 'Rector', 'Gobierno Central'),
(502, 'Vicerrectora de Docencia (E)', 'Gobierno Central'),
(503, 'Decano(a)', 'Direccion de Facultad'),
(504, 'Subdecano(a)', 'Direccion de Facultad');

-- 7. CARGA EN DIM_AUTORIDAD
INSERT OR REPLACE INTO dim_autoridad (autoridad_key, nombre_completo, titulo_academico, correo_contacto, biografia, es_vigente, fecha_inicio_vigencia, fecha_fin_vigencia)
VALUES 
(601, 'Dr. Tarquino Sanchez Almeida', 'Dr.', 'rectorado@epn.edu.ec', 'Doctor en Investigacion Educativa y directivo academico.', 1, '2023-11-01', '9999-12-31'),
(602, 'Dra. Rosa Navarrete', 'Dra.', 'vicerrectorado.docencia@epn.edu.ec', 'Doctora en Computacion e investigadora titular.', 1, '2023-11-01', '9999-12-31'),
(603, 'Dr. Jorge Toapaxi', 'Dr.', 'decanato.fica@epn.edu.ec', 'Investigador en estructuras y geotecnia.', 1, '2023-11-01', '9999-12-31');

-- 8. CARGA EN DIM_CATEGORIA_NOTICIA
INSERT OR REPLACE INTO dim_categoria_noticia (categoria_key, nombre_categoria)
VALUES 
(701, 'Investigacion y Ciencia'),
(702, 'Convocatoria y Empleo'),
(703, 'Resoluciones y Gobierno');

-- 9. CARGA EN FACT_OFERTA_ACADEMICA
INSERT OR REPLACE INTO fact_oferta_academica (oferta_key, carrera_key, facultad_key, nivel_key, modalidad_key, tiempo_extraccion_key, duracion_periodos, duracion_anios, creditos_totales, es_acreditada)
VALUES 
(8001, 401, 1001, 201, 301, 20261025, 9, 4.5, 120, 1),
(8002, 402, 1002, 201, 301, 20261025, 10, 5.0, 130, 1),
(8003, 403, 1001, 202, 301, 20261025, 4, 2.0, 60, 1);

-- 10. CARGA EN FACT_DESIGNACION_AUTORIDADES
INSERT OR REPLACE INTO fact_designacion_autoridades (designacion_key, autoridad_key, cargo_key, facultad_key, es_titular, tiempo_designacion_key)
VALUES 
(9001, 601, 501, 1001, 1, 20231101),
(9002, 602, 502, 1001, 0, 20231101),
(9003, 603, 503, 1002, 1, 20231101);

-- 11. CARGA EN FACT_COMUNICACION_INSTITUCIONAL
INSERT OR REPLACE INTO fact_comunicacion_institucional (noticia_key, categoria_key, tiempo_publicacion_key, titulo, longitud_caracteres, conteo_palabras, url)
VALUES 
(9501, 701, 20261025, 'EPN presenta avances en inteligencia artificial aplicada', 350, 48, 'https://www.epn.edu.ec/noticias/avance-ia'),
(9502, 702, 20261026, 'Convocatoria para seleccion docente en la Facultad de Sistemas', 280, 40, 'https://www.epn.edu.ec/noticias/convocatoria-sistemas');

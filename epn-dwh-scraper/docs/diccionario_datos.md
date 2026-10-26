# Diccionario de Datos del Data Warehouse Institucional de la EPN

El presente documento define la estructura técnica, semántica y analítica de cada una de las entidades que componen el modelo dimensional del Data Warehouse institucional de la Escuela Politécnica Nacional (EPN).

---

## 1. Tablas de Dimensiones

### 1.1 `dim_facultad`
Almacena las unidades académicas mayores y escuelas adscritas a la universidad.
- **Granularidad**: Un registro por facultad o escuela politécnica.
- **Clave Primaria (SK)**: `facultad_key` (Entero determinista generado vía hash).
- **Clave de Negocio (NK)**: `sigla` o `nombre`.

| Columna | Tipo de Dato | Nulable | Clave | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `facultad_key` | BIGINT | No | PK | Clave sustituta determinista | `18472910482910` |
| `nombre` | VARCHAR(150) | No | - | Nombre oficial de la facultad | `Facultad de Ingenieria de Sistemas` |
| `sigla` | VARCHAR(20) | No | NK | Sigla institucional estandarizada | `FIS` |
| `decano` | VARCHAR(120) | Sí | - | Nombre de la máxima autoridad de decanato | `Dra. Rosa Navarrete` |
| `subdecano` | VARCHAR(120) | Sí | - | Nombre del subdecano o subdirectora | `Dr. Denys Flores` |
| `descripcion` | TEXT | Sí | - | Reseña o trayectoria de la facultad | `Referente en computacion e informatica...` |
| `mision` | TEXT | Sí | - | Misión específica de la facultad | `Formar ingenieros e investigadores...` |
| `vision` | TEXT | Sí | - | Visión estratégica de la facultad | `Liderazgo nacional en tecnologias...` |
| `url` | VARCHAR(255) | No | - | Enlace web del portal de la facultad | `https://www.epn.edu.ec/facultad-ingenieria-de-sistemas/` |
| `departamentos_adscritos` | TEXT | Sí | - | Departamentos o laboratorios adscritos | `Departamento de Informatica (DICC)` |
| `contacto_correo` | VARCHAR(100) | Sí | - | Correo electrónico de secretaría o decanato | `fis@epn.edu.ec` |
| `contacto_telefono` | VARCHAR(50) | Sí | - | Teléfono o extensión de contacto | `(+593) 2 2976 300` |
| `ubicacion_campus` | VARCHAR(150) | Sí | - | Edificio o pabellón en el campus | `Edificio de Sistemas, Campus Politecnico` |

---

### 1.2 `dim_nivel_formacion`
Clasifica los niveles de formación de educación superior según la normativa ecuatoriana (LOES/CES).
- **Granularidad**: Un registro por nivel académico regulado.

| Columna | Tipo de Dato | Nulable | Clave | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `nivel_key` | BIGINT | No | PK | Clave sustituta determinista | `82937401928374` |
| `codigo_nivel` | VARCHAR(10) | No | NK | Código alfabético del nivel | `GRA` |
| `nombre_nivel` | VARCHAR(50) | No | - | Nombre formal del nivel de formación | `Grado` |
| `ciclo_academico` | VARCHAR(30) | No | - | Clasificación de ciclo universitario | `Tercer Nivel` |

---

### 1.3 `dim_modalidad`
Define los regímenes de impartición académica autorizados.
- **Granularidad**: Un registro por modalidad de estudio.

| Columna | Tipo de Dato | Nulable | Clave | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `modalidad_key` | BIGINT | No | PK | Clave sustituta determinista | `93847291827364` |
| `nombre_modalidad` | VARCHAR(50) | No | NK | Denominación de la modalidad | `Presencial` |
| `descripcion` | VARCHAR(255) | Sí | - | Explicación pedagógica del régimen | `Estudios regulares en aulas y laboratorios` |

---

### 1.4 `dim_carrera`
Catálogo de titulaciones de pregrado, posgrado y tecnologías impartidas en la universidad.
- **Granularidad**: Un registro por programa de estudios específico.

| Columna | Tipo de Dato | Nulable | Clave | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `carrera_key` | BIGINT | No | PK | Clave sustituta determinista | `34857201928374` |
| `nombre_carrera` | VARCHAR(180) | No | NK | Título del programa académico | `Ingenieria en Software` |
| `titulo_otorga` | VARCHAR(180) | No | - | Título terminal conferido por la EPN | `Ingeniera/o en Software` |
| `codigo_resolucion` | VARCHAR(60) | Sí | - | Número de resolución oficial CES | `RPC-SO-33-No.639-2016` |
| `perfil_ingreso` | TEXT | Sí | - | Competencias mínimas requeridas al postulante | `Aptitud logica y conocimientos matematicos` |
| `perfil_egreso` | TEXT | Sí | - | Competencias y destrezas alcanzadas al graduarse | `Liderar proyectos de desarrollo de software` |
| `campo_ocupacional` | TEXT | Sí | - | Sectores productivos de inserción laboral | `Empresas de tecnologia, banca, industria` |
| `malla_curricular_url` | VARCHAR(255) | Sí | - | Enlace a la malla curricular o PDF oficial | `https://www.epn.edu.ec/malla-software.pdf` |
| `url_carrera` | VARCHAR(255) | No | - | Enlace a la página informativa de la carrera | `https://www.epn.edu.ec/ingenieria-en-software/` |

---

### 1.5 `dim_cargo`
Clasificación de funciones administrativas y cargos directivos institucionales.
- **Granularidad**: Un registro por cargo universitario.

| Columna | Tipo de Dato | Nulable | Clave | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `cargo_key` | BIGINT | No | PK | Clave sustituta determinista | `12938475839201` |
| `nombre_cargo` | VARCHAR(100) | No | NK | Denominación del rol de gestión | `Rector` |
| `tipo_gobierno` | VARCHAR(50) | No | - | Nivel orgánico de la responsabilidad | `Gobierno Central` |

---

### 1.6 `dim_autoridad` (SCD Tipo 2)
Directorio de personas naturales que ejercen o ejercieron cargos directivos, con trazabilidad histórica.
- **Granularidad**: Un registro por autoridad y periodo de vigencia.

| Columna | Tipo de Dato | Nulable | Clave | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `autoridad_key` | BIGINT | No | PK | Clave sustituta determinista | `47382910492837` |
| `nombre_completo` | VARCHAR(150) | No | NK | Nombre y apellidos de la autoridad | `Dr. Tarquino Sanchez Almeida` |
| `titulo_academico` | VARCHAR(50) | Sí | - | Máximo grado o tratamiento académico | `Dr.` |
| `correo_contacto` | VARCHAR(100) | Sí | - | Correo electrónico de función pública | `rectorado@epn.edu.ec` |
| `biografia` | TEXT | Sí | - | Trayectoria académica y profesional | `Doctor en Investigacion Educativa...` |
| `es_vigente` | INTEGER | No | - | Indicador de registro activo (1: Sí, 0: Histórico) | `1` |
| `fecha_inicio_vigencia` | VARCHAR(10) | No | - | Fecha de inicio del mandato (YYYY-MM-DD) | `2023-11-01` |
| `fecha_fin_vigencia` | VARCHAR(10) | No | - | Fecha de conclusión (9999-12-31 si activo) | `9999-12-31` |

---

### 1.7 `dim_categoria_noticia`
Categorización temática de las publicaciones, comunicados y convocatorias institucionales.
- **Granularidad**: Un registro por categoría temática.

| Columna | Tipo de Dato | Nulable | Clave | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `categoria_key` | BIGINT | No | PK | Clave sustituta determinista | `58392019485720` |
| `nombre_categoria` | VARCHAR(100) | No | NK | Nombre de la categoría temática | `Investigacion y Ciencia` |

---

### 1.8 `dim_tiempo`
Dimensión temporal de calendario continuo para agregaciones en series de tiempo y cortes analíticos.
- **Granularidad**: Un registro por día calendario.

| Columna | Tipo de Dato | Nulable | Clave | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `tiempo_key` | INTEGER | No | PK | Clave en formato numérico YYYYMMDD | `20261025` |
| `fecha` | VARCHAR(10) | No | - | Fecha en formato ISO YYYY-MM-DD | `2026-10-25` |
| `anio` | INTEGER | No | - | Año calendario | `2026` |
| `mes` | INTEGER | No | - | Número de mes (1 al 12) | `10` |
| `mes_nombre` | VARCHAR(20) | No | - | Nombre en español del mes | `Octubre` |
| `trimestre` | INTEGER | No | - | Número de trimestre (1 al 4) | `4` |
| `semestre` | INTEGER | No | - | Número de semestre académico (1 o 2) | `2` |
| `dia` | INTEGER | No | - | Día del mes (1 al 31) | `25` |
| `dia_semana` | VARCHAR(20) | No | - | Nombre del día de la semana | `Sunday` |
| `es_fin_de_semana` | INTEGER | No | - | Indicador binario (1: Fin de semana, 0: Laborable) | `1` |

---

## 2. Tablas de Hechos (Fact Tables)

### 2.1 `fact_oferta_academica`
Métricas curriculares y de estructura formativa de la universidad.
- **Granularidad**: Un registro por programa académico activo impartido en una facultad y modalidad.

| Columna | Tipo de Dato | Nulable | Clave | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `oferta_key` | BIGINT | No | PK | Clave sustituta del hecho | `73849201948572` |
| `carrera_key` | BIGINT | No | FK | Referencia a `dim_carrera` | `34857201928374` |
| `facultad_key` | BIGINT | No | FK | Referencia a `dim_facultad` | `18472910482910` |
| `nivel_key` | BIGINT | No | FK | Referencia a `dim_nivel_formacion` | `82937401928374` |
| `modalidad_key` | BIGINT | No | FK | Referencia a `dim_modalidad` | `93847291827364` |
| `tiempo_extraccion_key` | INTEGER | No | FK | Referencia a `dim_tiempo` | `20261025` |
| `duracion_periodos` | INTEGER | No | Métrica | Semestres o periodos lectivos | `9` |
| `duracion_anios` | REAL | No | Métrica | Duración estimada en años lectivos | `4.5` |
| `creditos_totales` | INTEGER | No | Métrica | Créditos académicos acumulados | `120` |
| `es_acreditada` | INTEGER | No | Indicador | Estado de acreditación vigente (1: Sí, 0: No) | `1` |

---

### 2.2 `fact_designacion_autoridades`
Hechos de designación directiva y ejercicio del poder institucional en dependencias politécnicas.
- **Granularidad**: Un registro por nombramiento de una autoridad en un cargo y unidad.

| Columna | Tipo de Dato | Nulable | Clave | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `designacion_key` | BIGINT | No | PK | Clave sustituta del hecho | `64738291049283` |
| `autoridad_key` | BIGINT | No | FK | Referencia a `dim_autoridad` | `47382910492837` |
| `cargo_key` | BIGINT | No | FK | Referencia a `dim_cargo` | `12938475839201` |
| `facultad_key` | BIGINT | No | FK | Referencia a `dim_facultad` | `18472910482910` |
| `es_titular` | INTEGER | No | Indicador | Condición (1: Titular, 0: Encargado / Subrogante) | `1` |
| `tiempo_designacion_key` | INTEGER | No | FK | Referencia a `dim_tiempo` | `20231101` |

---

### 2.3 `fact_comunicacion_institucional`
Registro de la actividad divulgativa, convocatorias y producción de comunicados oficiales.
- **Granularidad**: Una noticia o publicación oficial emitida en los canales de la EPN.

| Columna | Tipo de Dato | Nulable | Clave | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `noticia_key` | BIGINT | No | PK | Clave sustituta del hecho | `84930284759302` |
| `categoria_key` | BIGINT | No | FK | Referencia a `dim_categoria_noticia` | `58392019485720` |
| `tiempo_publicacion_key` | INTEGER | No | FK | Referencia a `dim_tiempo` | `20261023` |
| `titulo` | VARCHAR(255) | No | - | Título de la nota periodística | `Convocatoria de Investigadores` |
| `longitud_caracteres` | INTEGER | No | Métrica | Extensión en caracteres del resumen | `420` |
| `conteo_palabras` | INTEGER | No | Métrica | Cantidad de palabras del extracto | `58` |
| `url` | VARCHAR(255) | No | - | Dirección web permanente del artículo | `https://www.epn.edu.ec/...` |

# Pipeline ETL y Data Warehouse Institucional de la EPN

## Informacion General
- **Proyecto**: Extraccion, Transformacion y Carga (ETL) de Datos Institucionales de la Escuela Politecnica Nacional para Data Warehouse Dimensional.
- **Institucion**: Escuela Politecnica Nacional (EPN), Quito, Ecuador.
- **Materia**: Business Intelligence / Ingenieria de Datos.
- **Nivel**: Superior Universitario / Pregrado y Posgrado.

---

## 1. Descripcion del Proyecto
Este proyecto implementa una solucion integral de ingenieria de datos y Business Intelligence que automatiza la extraccion (web scraping etico), limpieza, validacion de calidad, modelado dimensional y carga (ETL) de informacion publica del portal institucional de la Escuela Politecnica Nacional (https://www.epn.edu.ec y sus facultades adscritas).

El objetivo principal es poblar un Data Warehouse con un esquema de Constelacion de Hechos (Fact Constellation Schema) que soporte analisis OLAP, construccion de indicadores de gestion y reporteria estrategica para la toma de decisiones academicas y directivas en la universidad.

---

## 2. Objetivos
1. **Extraccion Etica y Modular**: Desarrollar extractores en Python que descubran y capturen informacion sobre unidades academicas, oferta de grado y posgrado, directivos, comunicacion institucional e investigacion, respetando robots.txt, politicas de retardo (rate limiting) y almacenamiento en cache local.
2. **Transformacion y Normalizacion Rigurosa**: Implementar reglas de limpieza textual, resolucion de codificacion de caracteres, eliminacion de duplicados y generacion determinista de claves sustitutas (Surrogate Keys).
3. **Aseguramiento de Calidad de Datos (Data Quality Profiling)**: Auditar la integridad referencial, verificar formatos de correo electronico, detectar valores atipicos y generar reportes de calidad reproducibles.
4. **Diseño Dimensional Justificado**: Construir un esquema de hechos y dimensiones que modele la oferta academica, la gobernanza institucional (con soporte SCD Tipo 2) y la divulgacion de eventos.
5. **Carga Idempotente y Consultas Analiticas**: Persistir los datos tanto en archivos planos normalizados (CSV) como en una base de datos relacional (SQLite por defecto, compatible con PostgreSQL), incluyendo consultas SQL analiticas orientadas a negocio.

---

## 3. Arquitectura General del Flujo de Datos

```
[ Fuentes Web EPN ]
  ├── /facultades/
  ├── /oferta-de-grado/
  ├── /oferta-de-posgrado/
  ├── /autoridades/
  ├── /nosotros/ & /historia/
  └── /wp-json/wp/v2/posts & /noticias/
          │
          ▼ (HTTP Client: Rate Limit 1.0s, Reintentos, Robots.txt)
[ Capa Raw: data/raw/ ] (Cache local de HTML y JSON)
          │
          ▼ (Scrapers especializados: BeautifulSoup, lxml, JSON parser)
[ Capa Interim: data/interim/ ] (Datos parseados en JSON y CSV preliminar)
          │
          ▼ (DataCleaner & DataValidator: Normalizacion, Deduplicacion, Hashing)
[ Capa Processed: data/processed/ ] (Archivos CSV limpios y Reporte de Calidad)
          │
          ├──► CsvLoader (data/processed/*.csv)
          └──► DatabaseLoader (SQLAlchemy -> data/epn_dwh.db o PostgreSQL)
                    │
                    ▼
          [ Modelo Dimensional OLAP ]
          (Consultas SQL BI, Power BI, Metabase, Notebooks)
```

---

## 4. Estructura del Repositorio

```
epn-dwh-scraper/
├── README.md                      # Documentacion integral del proyecto
├── requirements.txt               # Dependencias de Python fijadas
├── .env.example                   # Plantilla de variables de entorno
├── .gitignore                     # Exclusion de binarios, bases de datos y cache
├── config/
│   └── settings.yaml              # Parametros de red, rutas y endpoints oficiales
├── data/
│   ├── raw/                       # HTML y JSON cacheados de las solicitudes web
│   ├── interim/                   # Datos parseados estructurados antes de limpieza
│   └── processed/                 # CSV limpios modelados dimensionalmente
├── docs/
│   ├── diccionario_datos.md       # Catalogo detallado de atributos y tipos
│   ├── modelo_dimensional.md      # Justificacion academica del esquema estrella
│   ├── diagrama_modelo.md         # Diagrama de relaciones de entidad Mermaid
│   └── consideraciones_eticas.md  # Marco legal ecuatoriano (LOES, LOPDP, COIP)
├── logs/
│   ├── scraper_execution.log      # Trazabilidad completa de ejecucion
│   └── reporte_calidad_datos.md   # Auditoria cuantitativa de validacion
├── sql/
│   ├── 01_ddl_dimensiones.sql     # DDL de tablas dimensionales
│   ├── 02_ddl_hechos.sql          # DDL de tablas de hechos e indices
│   ├── 03_carga_ejemplo.sql       # Inserciones sinteticas de prueba
│   └── 04_consultas_bi.sql        # 8 consultas analiticas para soporte decisional
├── src/
│   ├── __init__.py
│   ├── main.py                    # Orquestador CLI con interfaz argparse
│   ├── config.py                  # Cargador de configuracion centralizada
│   ├── utils/
│   │   ├── http_client.py         # Cliente con rate limiting y politicas robots.txt
│   │   ├── logger.py              # Configuracion de logging a consola y disco
│   │   └── helpers.py             # Utilidades de texto, expresiones regulares y hash
│   ├── scrapers/
│   │   ├── base_scraper.py        # Clase base abstracta
│   │   ├── facultades_scraper.py  # Extractor de facultades y unidades
│   │   ├── carreras_scraper.py    # Extractor de carreras y posgrados
│   │   ├── autoridades_scraper.py # Extractor de directivos y decanos
│   │   ├── institucional_scraper.py # Extractor de mision, historia y laboratorios
│   │   └── noticias_scraper.py    # Extractor de notas de prensa y eventos
│   ├── transform/
│   │   ├── cleaning.py            # Normalizacion dimensional y resolucion de FKs
│   │   └── validation.py          # Reglas de negocio y perfilamiento de datos
│   └── load/
│       ├── to_csv.py              # Exportador idempotente a CSV
│       └── to_database.py         # Cargador relacional con SQLAlchemy
├── tests/
│   ├── test_scrapers.py           # Pruebas unitarias de parsing
│   ├── test_cleaning.py           # Pruebas de limpieza y generacion de claves
│   └── test_validation.py         # Pruebas de reglas de validacion
└── notebooks/
    └── exploracion_datos.ipynb    # Perfilamiento interactivo y graficos BI
```

---

## 5. Requisitos del Sistema e Instalacion

### 5.1 Requisitos Previos
- Python 3.10 o superior (verificado con Python 3.10 y Python 3.12).
- Gestor de paquetes pip.
- Conectividad a Internet (para la fase inicial de extraccion; las fases posteriores operan con cache local).

### 5.2 Instalacion Paso a Paso
1. Clonar o posicionarse en el directorio del proyecto:
   ```bash
   cd epn-dwh-scraper
   ```

2. Crear y activar un entorno virtual:
   - En Windows (PowerShell):
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - En Linux o macOS:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Instalar las dependencias requeridas:
   ```bash
   pip install -r requirements.txt
   ```

4. Configurar el archivo de entorno:
   ```bash
   cp .env.example .env
   ```

---

## 6. Modo de Ejecucion

El orquestador central (`src/main.py`) cuenta con una interfaz por linea de comandos (CLI) que permite ejecutar el pipeline de forma completa o por etapas especificas.

### 6.1 Ejecucion Integral (Extraccion, Transformacion y Carga)
Descarga la informacion institucional, limpia, valida, exporta a CSV e inserta en la base de datos SQLite:
```bash
python -m src.main --all
```

### 6.2 Ejecucion Modular por Extractor
- Solo facultades y decanatos:
  ```bash
  python -m src.main --facultades
  ```
- Solo carreras y posgrados:
  ```bash
  python -m src.main --carreras
  ```
- Solo autoridades universitarias:
  ```bash
  python -m src.main --autoridades
  ```
- Solo historia, principios y centros de investigacion:
  ```bash
  python -m src.main --institucional
  ```
- Solo noticias y eventos:
  ```bash
  python -m src.main --noticias
  ```

### 6.3 Ejecucion de Transformacion y Carga desde Datos Intermedios
Si los datos ya fueron extraidos a `data/interim/`, es posible reejecutar la transformacion y carga sin realizar peticiones web adicionales:
```bash
python -m src.main --transform --load-csv --load-db
```

### 6.4 Forzar Actualizacion Remota (Ignorar Cache)
Para omitir la cache local de `data/raw/` y consultar nuevamente el portal web en vivo:
```bash
python -m src.main --all --force-refresh
```

---

## 7. Diseño del Modelo Dimensional

El modelo analitico adopta un esquema de Constelacion de Hechos con dimensiones conformadas:

### 7.1 Tablas de Dimensiones
- `dim_facultad`: Codigo sustituto, nombre de la unidad, sigla institucional (FIS, FICA, FCA, FIEE, etc.), autoridades de decanato, correo, telefono y ubicacion fisica.
- `dim_nivel_formacion`: Tecnologia, Grado, Maestria, Doctorado, y ciclo academico LOES.
- `dim_modalidad`: Presencial, Dual, En Linea, Semipresencial.
- `dim_carrera`: Título de la carrera, titulo otorgado, codigo de resolucion CES, perfil de ingreso y perfil de egreso.
- `dim_cargo`: Rector, Vicerrector/a, Decano/a, Subdecano/a, clasificado por nivel de gobierno central o de facultad.
- `dim_autoridad`: SCD Tipo 2 con fecha de inicio, fecha de fin y bandera de vigencia para seguimiento de relevos directivos.
- `dim_tiempo`: Calendario continuo con fecha, año, mes, nombre de mes, trimestre, semestre y clasificacion laboral.
- `dim_categoria_noticia`: Temas de comunicacion (Investigacion, Resoluciones, Convocatorias).

### 7.2 Tablas de Hechos
- `fact_oferta_academica`: Métricas de duracion en semestres, duracion en años, creditaje acumulado y acreditacion.
- `fact_designacion_autoridades`: Nombramientos directivos con indicador de titularidad frente a encargo temporal "(E)".
- `fact_comunicacion_institucional`: Conteo de noticias, volumen textual en caracteres y palabras publicadas.

---

## 8. Ejecucion de Pruebas Unitarias
El proyecto incluye una suite de pruebas automatizadas con pytest que valida selectores, normalizaciones, generacion determinista de claves y reglas de auditoria de calidad:
```bash
pytest -v
```

---

## 9. Consideraciones Eticas y Legales
El software respeta escrupulosamente el ordenamiento juridico ecuatoriano:
- **robots.txt**: Valida que no se acceda a rutas restringidas (`/wp-admin/`).
- **LOTAIP y LOES**: Procesa unicamente informacion de caracter publico garantizada por la legislacion de transparencia en educacion superior.
- **LOPDP**: Excluye datos personales sensibles de cualquier tipo, limitando los registros personales a autoridades de alta direccion en el ejercicio de sus funciones publicas.
- **COIP**: No vulnera mecanismos de autenticacion ni ejecuta tecnicas intrusivas de denegacion de servicio, aplicando rate limiting estricto de 1 segundo por peticion.

---

## 10. Limitaciones Conocidas y Lineas Futuras
1. **Contenido Dinamico Ocasional**: Ciertas mallas curriculares se ofrecen mediante enlaces externos a visores PDF de resoluciones CES en lugar de tablas HTML nativas. El pipeline captura el enlace URL canónico al documento.
2. **Evolucion Tecnologica**:
   - Integracion de orquestacion programada mediante Apache Airflow o Prefect.
   - Conexion directa con tableros interactivos en Power BI, Tableau o Apache Superset.
   - Incorporacion de transformaciones analiticas con dbt (data build tool).

---

## 11. Autores y Licencia
- **Desarrollador**: Proyecto academico de Business Intelligence, Escuela Politecnica Nacional.
- **Licencia**: MIT License - Uso academico, educativo y de investigacion cientifica abierta.

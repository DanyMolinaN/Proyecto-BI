# Revisión del scraper y mejoras aplicadas

**Para:** Dany Molina (autor del scraper)
**Alcance:** revisión de `epn-dwh-scraper`, correcciones y una corrida local contra el sitio real de la EPN.
**Estado de las pruebas:** 47 pruebas pasan (`pytest`). Antes eran 19; se agregaron 28 nuevas en `tests/test_improvements.py`.

---

> **Documentación por módulo:** ver [modulos/README.md](modulos/README.md). Desde la versión 2, cada módulo tiene su propio documento y se actualiza en el mismo commit que el código.

## 1. Resumen

El pipeline funciona de extremo a extremo y el diseño (capas raw / interim / processed, claves sustitutas deterministas, modelo dimensional) es sólido. El problema principal era que **cuando faltaba un dato, el código lo inventaba**, y eso hacía que el reporte de calidad dijera "0 nulos / CONFORME" en todas las tablas aunque los datos no fueran reales.

La regla que se aplicó en todo el código es simple:

> **Si el portal no publica un dato, queda `NULL` y el reporte de calidad lo muestra. Nunca se rellena con un valor plausible.**

---

## 2. Qué se cambió

| # | Problema encontrado | Dónde | Cambio |
| :-- | :-- | :-- | :-- |
| 1 | Listas "canónicas" escritas a mano (autoridades, facultades, carreras) que se cargaban como si fueran extraídas | `autoridades_scraper.py`, `facultades_scraper.py`, `carreras_scraper.py` | Se eliminaron. Si no se extrae, no se carga. |
| 2 | Valores por defecto inventados: 9 períodos, 4.5 años, 120 créditos, `contacto@epn.edu.ec`, correos `rectorado@…`, teléfono y ubicación fijos, perfiles de ingreso/egreso genéricos, "Aprobación CES Vigente", biografía genérica, `periodo_gestion = "2023 - 2028"` | scrapers y `cleaning.py` | Ahora son `NULL`. |
| 3 | Carreras sin facultad detectada se asignaban a la **primera** facultad de la tabla (o a Civil y Ambiental) | `cleaning.py`, `carreras_scraper.py` | Quedan sin facultad (`NULL`) y el validador las reporta. Las autoridades centrales (Rectorado) tampoco se asignan a una facultad. |
| 4 | `es_acreditada = 1` fijo, créditos estimados por nivel | `cleaning.py`, `carreras_scraper.py` | `NULL`: no se extrae de ninguna fuente. |
| 5 | SCD Tipo 2 declarado pero sin efecto: todas las autoridades `es_vigente = 1`, fecha fija `2023-11-01`, y la carga hacía `replace` | `transform/scd2.py` (nuevo), `main.py`, `to_database.py` | Ahora compara contra lo ya cargado: cierra la versión anterior, abre una nueva y cierra autoridades que ya no aparecen. Ver sección 4. |
| 6 | Pipeline "exitoso" con muy pocos registros | `base_scraper.py`, `settings.yaml` | `ExtractionError` si un scraper devuelve menos del mínimo (`min_records` en `settings.yaml`). |
| 7 | `verify_ssl: false` por defecto | `settings.yaml`, `.env.example` | Ahora `true`. Se puede desactivar con `SCRAPER_VERIFY_SSL=False` solo si hace falta. |
| 8 | Caché sin vencimiento | `http_client.py` | TTL configurable (`cache_ttl_hours`, 24 h por defecto). |
| 9 | Si `robots.txt` fallaba, se permitía todo | `http_client.py` | Criterio RFC 9309: 4xx = sin restricciones; error de red o 5xx = se suspende el rastreo. |
| 10 | `dim_tiempo` solo 2023–2027 | `cleaning.py`, `main.py` | Ahora 2015–2035. |
| 11 | Sin verificación de integridad referencial | `validation.py` | Detecta FK nulas o sin padre. También lista como `Info:` las columnas con datos faltantes. |
| 12 | `get_table_counts` armaba SQL con el nombre de la tabla sin escapar | `to_database.py` | Usa el inspector de SQLAlchemy y escapa el identificador. |
| 13 | DDL con `NOT NULL` en métricas que no se extraen | `sql/02_ddl_hechos.sql` | Ahora admiten `NULL`. |

### Errores reales que aparecieron al quitar los parches

Al dejar de rellenar datos, la corrida real destapó fallos que antes estaban escondidos:

- **Decano y subdecano pegados** (`"Dr. Jorge ToapaxiSubdecano: Dr. Khaled Hamad…"`) y correos con texto de más (`decano.civil@epn.edu.ecsubdecano`). Causa: `soup.get_text()` sin separador. Corregido con `get_text(separator="\n")`. También se descartan nombres de decano/subdecano que sean un correo.
- **Carreras sin facultad por diferencias de redacción**: el portal dice `Facultad de Ingeniería Geología y Petróleos` y el scraper de carreras usa `Facultad de Geologia y Petroleos`. El emparejamiento ahora ignora tildes y tolera variaciones menores.
- **Pérdida de precisión en claves**: al haber nulos, pandas convertía las claves hash de 56 bits a `float64` y las corrompía. Corregido con `Int64` nullable.
- **Duración, modalidad, título y facultad de las carreras de grado no se extraían.** El portal publica la ficha como pares "etiqueta / valor" en elementos consecutivos y **sin dos puntos** (`Duración` → `Nueve períodos académicos`), pero el scraper buscaba `Duración:`. Además el número viene a veces en palabras ("Nueve") sin dígitos. Ahora se leen por etiqueta (`extract_labeled_value` en `helpers.py`) y se reconoce el número en palabras. La facultad sale de la etiqueta `Unidad Académica`; antes se buscaba en párrafos de toda la página y podía tomar textos del menú (por ejemplo "Facultad de Ingeniería Civil y Ambiental" de la sección de infraestructura).
- **`perfil_ingreso`, `perfil_egreso` y `campo_ocupacional` estaban contaminados con texto del menú** ("INTRANET", "Resolución de aprobación CES…"): el selector tomaba el primer `div` grande que contenía "perfil de ingreso". Ahora se lee solo la zona de contenido que sigue a las pestañas `PERFIL DE INGRESO … CONTACTO`. Verificado contra las 35 páginas guardadas: 0 registros con texto del menú. El tope de texto subió de 500 a 1000 caracteres para no cortar a mitad de frase.
- **`--force-refresh` y `--no-cache` no hacían nada**: `ETLPipeline` guardaba las banderas pero el `HttpClient` leía la configuración por su cuenta. Con `--force-refresh` la corrida tardaba 5 s (todo desde caché) en vez de ~75 s. Ahora las banderas se pasan al cliente.
- Se agregó `pytest.ini` (`pythonpath = .`) para que `pytest` encuentre el paquete `src` sin importar desde dónde se invoque.
- **Más datos inventados en `noticias_scraper.py` e `institucional_scraper.py`**: tres noticias de ejemplo con fecha 2026, misión/visión/valores/principios por defecto, hitos y centros escritos a mano, año `1869` por defecto en 19 de 21 hitos, y misión/visión que en realidad guardaban el texto del menú. Todo eliminado; ahora la misión y la visión salen de sus encabezados, la historia se lee año por año (18 hitos con su año real) y los centros sin dato quedan `NULL`.
- Se modificó `extract_modality`: antes devolvía "Presencial" cuando no encontraba nada; ahora devuelve `None`.

---

## 3. Resultado de la corrida local

Ejecutado (la última vez, ya con la corrección de carreras) con `python -m src.main --all` contra https://www.epn.edu.ec (SSL verificado, `robots.txt` respetado, ~1.5 min). Se corrió varias veces para comprobar idempotencia.

| Tabla | Registros |
| :-- | :-- |
| dim_facultad | 9 |
| dim_carrera / fact_oferta_academica | 46 |
| dim_autoridad / fact_designacion_autoridades | 10 / 10 |
| fact_comunicacion_institucional | 30 |
| dim_informacion_institucional | 31 |

Con la regla de "no inventar", el reporte (`logs/reporte_calidad_datos.md`) muestra la realidad del portal.

**Carreras (`fact_oferta_academica`, 46 programas):**

| Campo | Antes de corregir la extracción | Ahora |
| :-- | :-- | :-- |
| `duracion_periodos` / `duracion_anios` | 100 % sin dato | **18 de 46 con dato** (las 18 carreras de grado: 9 períodos / 4.5 años). 28 sin dato: son posgrados |
| `facultad_key` | 23 sin dato | **16 sin dato**. Las 18 de grado vienen del portal (`Unidad Académica`); 12 de los posgrados se infieren por nombre y quedan marcados en `dim_carrera.campos_inferidos` |
| `creditos_totales` | 100 % sin dato | **100 % sin dato (definitivo)**: ninguna página del portal publica créditos totales. Solo aparecen enlaces como "Equivalencia de créditos". |
| `es_acreditada` | 100 % sin dato | 100 % sin dato |

Por qué los posgrados siguen vacíos: se revisó el HTML de las fichas de maestría y **no incluyen** duración, modalidad ni unidad académica; solo perfil de ingreso, resultados, horarios, malla y datos del coordinador. No es un fallo del extractor: el dato no está en la página (podría estar en los PDF de la malla, que no se procesan).

**Otros datos que el scraper actual no logra extraer:**

- Autoridades: `correo_contacto` y `biografia` 100 % sin dato.
- `dim_carrera.codigo_resolucion`: solo las carreras de grado lo publican; `campo_ocupacional`: 100 % sin dato; `perfil_egreso`: 31 de 46 sin dato (todos los posgrados y 3 de grado).
- `dim_facultad.ubicacion_campus`: 100 % sin dato.

Esto **no es un fallo del cambio**: son datos que antes estaban tapados con valores falsos.

---

## 4. Cómo funciona ahora el SCD Tipo 2 (`dim_autoridad`)

Clave de negocio: `nombre_completo`. Atributos que disparan una nueva versión: `titulo_academico`, `correo_contacto`, `biografia`.

| Situación en la nueva captura | Qué pasa |
| :-- | :-- |
| Autoridad sin cambios | Se conserva la fila vigente (sin duplicar). |
| Cambió algún atributo | La fila anterior se cierra (`es_vigente = 0`, `fecha_fin_vigencia = hoy`) y se crea otra con clave nueva y `es_vigente = 1`. |
| Ya no aparece en el portal | Se cierra su vigencia. |
| Persona nueva | Se inserta como vigente. |

`fact_designacion_autoridades` conserva las filas históricas y agrega las de la versión vigente. Se verificó que correr el pipeline varias veces seguidas deja 10 / 10 / 10 filas (idempotente).

**Limitación importante:** el portal no publica la fecha de posesión. Por eso `fecha_inicio_vigencia` y `tiempo_designacion_key` son la **fecha de la primera captura**, no la fecha real del nombramiento. Hay que decirlo así en la entrega académica.

---

## 5. Cómo probarlo

```bash
cd epn-dwh-scraper
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
pytest -v                      # 47 pruebas
python -m src.main --all       # pipeline completo
```

Para ver el historial SCD2 después de varias corridas:

```bash
sqlite3 data/epn_dwh.db "select nombre_completo, es_vigente, fecha_inicio_vigencia, fecha_fin_vigencia from dim_autoridad order by nombre_completo, fecha_inicio_vigencia;"
```

Si `ExtractionError` aparece, significa que el sitio cambió, hubo bloqueo o falla de red: no se guardó nada, que es el comportamiento buscado.

---

## 6. Pendientes sugeridos (no se hicieron)

1. **Posgrados**: duración, modalidad y facultad no están en la ficha HTML. Habría que leer los PDF de la malla o consultar otra fuente. La facultad inferida por nombre falla en 16 programas.
1b. **`campo_ocupacional`** queda vacío en las 46 carreras: ninguna ficha lo publica con un encabezado explícito. **`perfil_egreso`** solo se extrae en grado (bloque "Resultados Generales"); en posgrados no hay encabezado fiable. En posgrados `perfil_ingreso` puede quedar incompleto si el texto continúa en viñetas.
2. **Autoridades**: hay una URL de facultad escrita a mano en `_extract_deans_from_faculties`; conviene usar las URLs que descubre `FacultadesScraper`. Falta correo y biografía.
3. **Usar los DDL de `sql/`**: el pipeline carga con `pandas.to_sql(..., if_exists="replace")`, así que las claves primarias y foráneas de `01_ddl_dimensiones.sql` y `02_ddl_hechos.sql` **no se aplican** a la base real.
4. **Pruebas con HTML real**: los tests de scrapers usan HTML sintético. Guardar 2–3 páginas reales como fixtures detectaría cambios del sitio.
5. **Hechos con historial**: `fact_oferta_academica` y `fact_comunicacion_institucional` se reemplazan en cada corrida (snapshot). Si se quiere evolución en el tiempo, hay que cargarlos con `append`.
6. **`dim_modalidad`** tiene una fila "No especificado" cuando la ficha no indica modalidad; revisar si se quiere ese miembro explícito o una regla distinta.

---

## 7. Archivos tocados

Modificados: `.env.example`, `config/settings.yaml`, `sql/02_ddl_hechos.sql`, `src/config.py`, `src/main.py`, `src/load/to_database.py`, `src/scrapers/{autoridades,base,carreras,facultades}_scraper.py`, `src/transform/{cleaning,validation}.py`, `src/utils/{helpers,http_client}.py`, `tests/test_scrapers.py`, `logs/reporte_calidad_datos.md` (regenerado).
Nuevos: `src/transform/scd2.py`, `tests/test_improvements.py`, `pytest.ini`, `docs/modulos/` (un documento por módulo), este documento.

Nada se ha subido a GitHub: los cambios están solo en la copia local.

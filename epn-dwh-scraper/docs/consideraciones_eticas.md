# Consideraciones Eticas, Legales y Buenas Practicas de Web Scraping

El desarrollo de este proceso de extracción y carga para el Data Warehouse de la Escuela Politécnica Nacional (EPN) se rige bajo estrictos principios éticos, técnicos y legales orientados a la investigación académica y la analítica institucional.

---

## 1. Cumplimiento Tecnico y Politicas de Rastreo Etico

### 1.1 Respeto al Protocolo de Exclusion de Robots (`robots.txt`)
El cliente HTTP del proyecto (`src/utils/http_client.py`) consulta y valida formalmente las directivas emitidas en `https://www.epn.edu.ec/robots.txt` mediante la librería nativa de Python `urllib.robotparser`.
- El archivo oficial de la EPN restringe exclusivamente los directorios administrativos de control interno (`Disallow: /wp-admin/`).
- Todas las rutas empleadas en este proyecto (`/facultades/`, `/oferta-de-grado/`, `/oferta-de-posgrado/`, `/autoridades/`, `/nosotros/`, `/historia/`, `/laboratorios_institucionales/`, `/noticias/`) se encuentran formalmente autorizadas para indexación y consulta.

### 1.2 Identificacion Transparente mediante User-Agent
El extractor no enmascara su identidad ni se hace pasar por software malicioso. Las cabeceras HTTP incluyen una cadena identificable que explicita el propósito académico y los canales de contacto institucional:
```http
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 EPN-Academic-BI/1.0 (+https://www.epn.edu.ec; contacto-academico@epn.edu.ec)
```

### 1.3 Control de Frecuencia y Prevencion de Sobrecarga (Rate Limiting)
Para garantizar la disponibilidad ininterrumpida de los servidores institucionales y prevenir cualquier impacto sobre el ancho de banda o la capacidad de cómputo del portal:
- Se implementa una pausa obligatoria mínima entre peticiones sucesivas (`rate_limit_seconds: 1.0`).
- Se utiliza retroceso exponencial (exponential backoff) ante cualquier respuesta de congestión o error transitorio (`max_retries: 4`, `backoff_factor: 1.5`).
- Se incorpora un sistema de caché local persistente en `data/raw/`. Al descargar un recurso por primera vez, el contenido se almacena en disco con un hash determinista; las ejecuciones subsecuentes de depuración, desarrollo o pruebas leen directamente de la caché local, eliminando el tráfico hacia el servidor de la EPN.

---

## 2. Marco Legal Ecuatoriano

### 2.1 Ley Organica de Transparencia y Acceso a la Informacion Publica (LOTAIP)
De acuerdo con la LOTAIP y la Ley Orgánica de Educación Superior (LOES), la Escuela Politécnica Nacional es una institución pública de educación superior autónoma. Por mandato constitucional y legal:
- La oferta de carreras, las autoridades universitarias, los reglamentos, las resoluciones del Consejo Politécnico y los presupuestos son información de dominio público sujeta al principio de máxima publicidad.
- La extracción automatizada de esta información para fines docentes, estadísticos y analíticos promueve la transparencia y el escrutinio ciudadano.

### 2.2 Ley Organica de Proteccion de Datos Personales (LOPDP Ecuador)
El proyecto cumple rigurosamente con las disposiciones de la LOPDP publicada en el Registro Oficial Suplemento 459:
- **Exclusión de datos personales sensibles**: No se recopilan números de cédula, direcciones domiciliarias, información médica, biométrica, financiera ni opiniones políticas o religiosas de ninguna persona.
- **Datos de funcionarios en ejercicio de funciones públicas**: Los nombres de autoridades, rectores y decanos corresponden estrictamente a funcionarios en el desempeño de funciones de alta dirección universitaria, y sus correos electrónicos son institucionales de acceso público (`@epn.edu.ec`), destinados al contacto de la comunidad universitaria.

### 2.3 Codigo Organico Integral Penal (COIP)
El artículo 232 del COIP tipifica las infracciones contra la seguridad de los activos de los sistemas de información y comunicación (ataques a la integridad de sistemas, interceptación ilegal o alteración de datos).
- El presente software realiza únicamente operaciones de lectura idempotente (método HTTP GET) sobre recursos públicos accesibles en la World Wide Web sin vulnerar controles de acceso, firewalls, contraseñas ni sistemas de autenticación.
- No se realiza inyección de código ni pruebas de penetración no autorizadas.

---

## 3. Principios Eticos Académicos y Replicabilidad
1. **No comercialización**: Los datos estructurados en este Data Warehouse se destinan exclusivamente a fines educativos, analíticos y de modelado en la asignatura de Business Intelligence.
2. **Integridad del dato**: Se prohíbe la alteración maliciosa o sesgada de nombres, resoluciones o cifras oficiales. Cualquier transformación aplicada obedece a reglas objetivas de normalización sintáctica y ortográfica.
3. **Idempotencia y reproducibilidad**: El código puede ser auditado, ejecutado y verificado por pares académicos y docentes, garantizando el rigor metodológico exigido en la ingeniería de datos.

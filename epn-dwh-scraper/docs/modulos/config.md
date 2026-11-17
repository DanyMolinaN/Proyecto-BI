# `src/config.py`

**Estado:** estable · **Fase:** 1

## Propósito
Centraliza la configuración. Lee `config/settings.yaml`, permite sobrescribir valores con variables de entorno (`.env`) y expone un objeto global `settings`.

## Entradas y salidas
| | Detalle |
| :-- | :-- |
| Entrada | `config/settings.yaml`, `.env` |
| Salida | Instancia `settings` usada por todos los módulos; crea las carpetas `data/*` y `logs/` si no existen |

## Cómo funciona
Para cada parámetro: si existe la variable de entorno, gana; si no, se usa el valor del YAML; si tampoco está, un valor por defecto.

| Parámetro | YAML | Variable de entorno | Por defecto |
| :-- | :-- | :-- | :-- |
| User-Agent | `network.user_agent` | `SCRAPER_USER_AGENT` | el del YAML |
| Timeout (s) | `network.timeout_seconds` | `SCRAPER_TIMEOUT` | 15 |
| Espera entre peticiones (s) | `network.rate_limit_seconds` | `SCRAPER_RATE_LIMIT` | 1.0 |
| Reintentos | `network.max_retries` | `SCRAPER_MAX_RETRIES` | 4 |
| Factor de espera | `network.backoff_factor` | `SCRAPER_BACKOFF_FACTOR` | 1.5 |
| Usar caché | `network.use_cache` | `SCRAPER_USE_CACHE` | true |
| Vigencia de caché (h) | `network.cache_ttl_hours` | `SCRAPER_CACHE_TTL_HOURS` | 24 |
| Verificar SSL | `network.verify_ssl` | `SCRAPER_VERIFY_SSL` | **true** |
| Base de datos | `storage.database_url` | `DATABASE_URL` | SQLite en `data/epn_dwh.db` |
| Nivel de log | `logging.level` | `LOG_LEVEL` | INFO |
| Mínimo de registros por scraper | `min_records.<scraper>` | no | 1 |

## Reglas de datos
Ninguna.

## Configuración y secretos
- `.env` **no se versiona**. `.env.example` sí, solo con valores de ejemplo.
- Una cadena de conexión con contraseña (PostgreSQL) debe ir en `DATABASE_URL` dentro de `.env`, nunca en `settings.yaml`.
- `verify_ssl` solo debe ponerse en `False` si el certificado del sitio falla de verdad.

## Pruebas
Cubierto de forma indirecta (`monkeypatch` sobre `settings` en `tests/test_improvements.py`).

## Límites conocidos / pendientes (Fase 2)
- No valida valores inválidos (por ejemplo un timeout negativo).

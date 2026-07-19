# Checklist de configuracion externa

No registrar valores en Git, tickets, capturas, logs ni documentos. Los valores
se cargan directamente en la plataforma indicada.

## Render - FastAPI staging

| Variable | Finalidad | Obligatoria | Donde cargar | Verificacion segura |
|---|---|---:|---|---|
| `APP_ENV` | separa staging | si | Environment | `/health.environment=staging` |
| `APP_VERSION` | version visible | si | Environment | `/health.app_version` |
| `SOURCE_MODE` | fixture/live | si | Environment | `/health.build_info.source_mode` |
| `ENABLE_PUBLICATION` | gate global | si | Environment | debe ser `false` |
| `ENABLE_PRIVATE_PUBLICATION` | gate de escritura privada aprobada | si | Environment | debe ser `false` |
| `SCRAPER_API_KEY` | autentica n8n | si, secreto | Secret | 401/403/200 sin imprimirla |
| `SUPABASE_URL` | proyecto aislado | si, sensible | Secret | `/health.supabase_configured=true` |
| `SUPABASE_SERVICE_ROLE_KEY` | backend Supabase | si, secreto | Secret | insert fixture desde API |
| `RAW_BUCKET` | snapshots | si | Environment | objeto fixture privado |
| `PROCESSED_BUCKET` | datasets procesados | si | Environment | CSV fixture privado |
| `PUBLISHED_BUCKET` | salida futura | si | Environment | existe y sigue privado/vacio |
| `REQUEST_TIMEOUT_SECONDS` | timeout fuente/Supabase | si | Environment | valor inicial 120 |
| `REQUEST_DELAY_SECONDS` | pausa responsable | si | Environment | valor inicial 2 |
| `MAX_PRODUCTS_PER_RUN` | limite de seguridad | si | Environment | valor inicial 5 |
| `MAX_PAGES_PER_RUN` | limite de seguridad | si | Environment | valor inicial 1 |
| `LOG_LEVEL` | observabilidad | si | Environment | `INFO`, sin headers |

## n8n existente

| Variable | Finalidad | Obligatoria | Donde cargar | Verificacion segura |
|---|---|---:|---|---|
| `FASTAPI_BASE_URL` | URL HTTPS de FastAPI | si | variable/credential n8n | GET `/health` 200 |
| `SCRAPER_API_KEY` | autentica FastAPI | si, secreto | credential/secret n8n | request protegida 200 |
| `N8N_WEBHOOK_TOKEN` | autentica GitHub | si, secreto | credential/secret n8n | token incorrecto rechazado |
| `ENABLE_CLOUD_PUBLICATION` | gate adicional | si | variable n8n | `false` |
| `HEARTBEAT_URL` | confirma fin, no dispara | no | credential/variable | no configurarlo como trigger |

## GitHub

| Tipo | Nombre | Finalidad | Estado inicial | Verificacion |
|---|---|---|---|---|
| Variable | `PROJECT_SUPER_AUTOMATION_ENABLED` | kill switch | `false` | job real omitido |
| Secret | `N8N_PRODUCTION_WEBHOOK_URL` | webhook n8n | pendiente | solo se usa en `curl` |
| Secret | `N8N_WEBHOOK_TOKEN` | autentica webhook | pendiente | nunca aparece en logs |

Para la prueba E2E, cambiar temporalmente la variable a `true`, ejecutar
`workflow_dispatch` una vez y restaurarla a `false` al terminar.

## No exponer

- No usar `echo`, outputs, query strings ni nombres de artefactos con secretos.
- No guardar service role en n8n si FastAPI es el unico cliente de Supabase.
- No colocar secretos en `render.yaml`, JSON n8n o YAML de GitHub.
- Rotar inmediatamente cualquier valor que aparezca en historial o logs.

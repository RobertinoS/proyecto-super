# Evidencia E2E staging - Sprint 15

Estado: `VALIDACION_MANUAL_PARCIAL_CONFIRMADA`.

La validacion manual de staging se completo sin registrar secretos, URLs de
webhook, identificadores privados ni enlaces de consola. El E2E iniciado por
GitHub Actions continua pendiente y es la condicion externa restante para el
cierre funcional de Sprint 15.

## Validacion manual externa

- Fecha: 2026-07-14.
- FastAPI staging: desplegada y operativa en modo `fixture`.
- Supabase: entorno staging aislado confirmado; no se documentan IDs ni
  credenciales.
- n8n: URL Test y URL Production validadas manualmente con el flujo fixture.
- Resultado: respuesta estructurada satisfactoria con `rows_processed=3`.
- Idempotencia: repeticion controlada confirmada sin registros duplicados.
- Publicacion: bloqueada; `ENABLE_PUBLICATION=false` y
  `ENABLE_CLOUD_PUBLICATION=false`.
- GitHub Actions: el E2E mediante `workflow_dispatch` sigue pendiente; el
  kill switch `PROJECT_SUPER_AUTOMATION_ENABLED=false` debe conservarse.

## Auditoria del export n8n

- El artefacto versionado permanece con `active=false`; esto protege futuras
  importaciones y no altera la validacion manual ya realizada en staging.
- `trigger_type` se normaliza a `manual`, `manual_staging`,
  `github_actions`, `n8n` o `smoke_test` antes de invocar FastAPI.
- `/jobs/scrape` recibe solo `source`, `dry_run`, `max_products`,
  `max_pages`, `execution_id` y `trigger_type`.
- `Run Vea Scrape` y `Process and Validate` envian sus salidas de error a
  `Structured Error`; un HTTP fallido no alcanza `Quality Gate`.
- El workflow fuerza `dry_run=true`, limita la ejecucion a 5 productos y 1
  pagina, y conserva tres warm-ups de 120 segundos con esperas de 20 y 40
  segundos.

## Validacion local reproducible

- Fecha: 2026-07-13.
- Modo: fixture local, sin Supabase real.
- `execution_id`: `sprint15-fixture-idempotency`.
- `run_id`: `6b3cffd4-42c7-5e99-981a-d2e619447f0a`.
- Productos: 3.
- Calidad: `READY_FOR_APPROVAL`.
- Repeticion: mismo `run_id`, `duplicate_execution=true`.
- Publicacion sin aprobacion: bloqueada.
- Publicacion con aprobacion y gate global apagado: `DRY_RUN`.

Esta prueba valida logica, no demuestra independencia de la PC ni persistencia
externa.

Validacion HTTP local adicional:

- `/health=ok`, `/docs=200`, una fuente fixture.
- Sin API key: 401; API key incorrecta: 403.
- `run_id`: `a8e63bcd-3b6c-518f-83cf-e9ba6c453621`.
- 3 productos, `SCRAPED`, proceso `READY_FOR_APPROVAL`.
- Publicacion sin aprobacion: 409; con aprobacion: `DRY_RUN`.

Infraestructura externa observada:

- Render accesible y con un unico servicio n8n existente; FastAPI staging fue
  desplegada como servicio separado del orquestador.
- Health publico de n8n: `/healthz` respondio HTTP 200 y `status=ok`.
- UptimeRobot no se modifico; debe monitorear exclusivamente el health de n8n,
  nunca el webhook de scraping ni FastAPI.
- El repo tiene remote `origin`; la rama de staging puede publicarse para que
  GitHub Actions ejecute la prueba manual posterior.
- Suite completa: 87 pruebas aprobadas; una advertencia externa de deprecacion
  FastAPI TestClient/httpx.

## Evidencia externa a completar

| Paso | Estado | Evidencia no sensible |
|---|---|---|
| GitHub `workflow_dispatch` | PENDIENTE | run ID y conclusion |
| Webhook n8n | VALIDADO MANUALMENTE | Test y Production URL correctas |
| Warm-up FastAPI | VALIDADO MANUALMENTE | FastAPI fixture disponible para el flujo |
| Scrape fixture | VALIDADO MANUALMENTE | `rows_processed=3` |
| Process/calidad | VALIDADO MANUALMENTE | respuesta estructurada satisfactoria |
| `scrape_runs` | VALIDADO MANUALMENTE | repeticion sin duplicados |
| `price_observations` | VALIDADO MANUALMENTE | cero duplicados en prueba idempotente |
| `source_health` | PENDIENTE DE EVIDENCIA DETALLADA | registrar solo estado no sensible |
| `execution_events` | PENDIENTE DE EVIDENCIA DETALLADA | registrar etapas no sensibles |
| Storage privado | PENDIENTE DE EVIDENCIA DETALLADA | paths sin URL firmada |
| Publicacion | BLOQUEADA | sin dataset publico |

No registrar URL completa del webhook, tokens, service role, IDs de proyecto
privados ni enlaces de consola que contengan parametros sensibles.

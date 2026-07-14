# Evidencia E2E staging - Sprint 15

Estado: `PENDIENTE_ACCION_EXTERNA`.

No se inventan resultados de GitHub, n8n, Render o Supabase. Esta evidencia se
completa solo despues de desplegar un commit auditado y configurar los secretos
en sus plataformas.

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

Infraestructura externa observada sin cambios:

- Render accesible y con un unico servicio n8n existente; no se creo FastAPI.
- Health publico de n8n: `/healthz` respondio HTTP 200 y `status=ok`.
- Supabase y UptimeRobot requieren inicio de sesion; no se inspeccionaron ni
  modificaron configuraciones privadas.
- El repo local no tiene remote Git configurado; GitHub Actions no puede
  ejecutarse desde este checkout hasta enlazar un repositorio remoto.
- Suite completa: 87 pruebas aprobadas; una advertencia externa de deprecacion
  FastAPI TestClient/httpx.

## Evidencia externa a completar

| Paso | Estado | Evidencia no sensible |
|---|---|---|
| GitHub `workflow_dispatch` | PENDIENTE | run ID y conclusion |
| Webhook n8n | PENDIENTE | execution ID de n8n |
| Warm-up FastAPI | PENDIENTE | intentos y HTTP final |
| Scrape fixture | PENDIENTE | execution_id, run_id, cantidades |
| Process/calidad | PENDIENTE | estado y score |
| `scrape_runs` | PENDIENTE | una fila por execution_id |
| `price_observations` | PENDIENTE | cantidad y cero duplicados |
| `source_health` | PENDIENTE | estado actualizado |
| `execution_events` | PENDIENTE | etapas esperadas |
| Storage privado | PENDIENTE | paths sin URL firmada |
| Publicacion | BLOQUEADA | sin dataset publico |

No registrar URL completa del webhook, tokens, service role, IDs de proyecto
privados ni enlaces de consola que contengan parametros sensibles.

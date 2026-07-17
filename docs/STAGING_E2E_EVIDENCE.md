# Evidencia E2E staging - Sprint 15

## Preparacion Sprint 16 (sin validacion externa aun)

La implementacion local agrega migracion 003, endpoints de revision,
observabilidad y publicacion privada en seco. Esta seccion no constituye
evidencia de despliegue: al momento de actualizarla no se aplico SQL 003, no se
desplego FastAPI con Sprint 16, no se importo el workflow de aviso y no se
escribieron datasets privados. Los gates esperados siguen en `false`.

Estado: `COMPLETADO_V1.7.0`.

La validacion manual de staging se completo sin registrar secretos, URLs de
webhook, identificadores privados ni enlaces de consola. El E2E iniciado por
GitHub Actions se completo con fixture, persistencia aislada e idempotencia.

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
- GitHub Actions: el E2E mediante `workflow_dispatch` fue exitoso; el kill
  switch `PROJECT_SUPER_AUTOMATION_ENABLED=false` debe conservarse.

## E2E de cierre

- GitHub Actions ejecuto manualmente el workflow diario y recibio una respuesta
  HTTP 2xx de n8n; no se documentan identificadores de corrida.
- n8n completo `Structured Success`; FastAPI proceso el fixture y devolvio
  `rows_processed=3` con publicacion bloqueada.
- Supabase staging aislado registro la ejecucion, observaciones y eventos. La
  prueba de idempotencia no creo duplicados.
- La publicacion efectiva fue cero. `ENABLE_PUBLICATION=false` y
  `ENABLE_CLOUD_PUBLICATION=false` continuan activos.
- La prueba Vea ONLINE limitada se completo con `dry_run=true`; se conserva el
  canal `ONLINE` y no se representa como precio fisico de sucursal.
- El entorno se restauro a `SOURCE_MODE=fixture` y el kill switch a `false`.

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
- `execution_id` y `run_id`: deterministas y omitidos de esta evidencia.
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
- `run_id`: presente y omitido de esta evidencia.
- 3 productos, `SCRAPED`, proceso `READY_FOR_APPROVAL`.
- Publicacion sin aprobacion: 409; con aprobacion: `DRY_RUN`.

Infraestructura externa observada:

- Render accesible y con un unico servicio n8n existente; FastAPI staging fue
  desplegada como servicio separado del orquestador.
- Health publico de n8n: `/healthz` respondio HTTP 200 y `status=ok`.
- UptimeRobot no se modifico; debe monitorear exclusivamente el health de n8n,
  nunca el webhook de scraping ni FastAPI.
- El repo tiene remote `origin`; `main` es la rama predeterminada y GitHub
  Actions quedo registrado para ejecucion manual controlada.
- Suite completa: 87 pruebas aprobadas; una advertencia externa de deprecacion
  FastAPI TestClient/httpx.

## Evidencia externa completada

| Paso | Estado | Evidencia no sensible |
|---|---|---|
| GitHub `workflow_dispatch` | VALIDADO | 2xx y workflow exitoso |
| Webhook n8n | VALIDADO | Test y Production URL correctas |
| Warm-up FastAPI | VALIDADO | fixture disponible para el flujo |
| Scrape fixture | VALIDADO | `rows_processed=3` |
| Process/calidad | VALIDADO | `Structured Success` |
| `scrape_runs` | VALIDADO | idempotencia sin duplicados |
| `price_observations` | VALIDADO | observaciones persistidas sin duplicados |
| `source_health` | VALIDADO | estado actualizado por pipeline |
| `execution_events` | VALIDADO | trazabilidad de etapas persistida |
| Storage privado | VALIDADO | sin dataset publico |
| Publicacion | BLOQUEADA | sin dataset publico |

No registrar URL completa del webhook, tokens, service role, IDs de proyecto
privados ni enlaces de consola que contengan parametros sensibles.

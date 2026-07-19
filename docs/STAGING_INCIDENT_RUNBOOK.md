# Runbook de incidentes staging

## Kill switch inmediato

1. GitHub: `PROJECT_SUPER_AUTOMATION_ENABLED=false`.
2. n8n: desactivar `Proyecto Super - Daily Price Refresh - Staging`.
3. Render: `ENABLE_PUBLICATION=false` y `SOURCE_MODE=fixture`.
4. Render: `ENABLE_PRIVATE_PUBLICATION=false`.
5. Confirmar que UptimeRobot solo consulta la salud de n8n.

Estado posterior al cierre Sprint 15: mantener los cuatro gates en estado
seguro. El schedule de GitHub puede iniciar una corrida de control, pero
`PROJECT_SUPER_AUTOMATION_ENABLED=false` evita que alcance n8n. Para una nueva
ventana manual, restaurar este valor a `false` al finalizar y conservar
`SOURCE_MODE=fixture`, `ENABLE_PUBLICATION=false` y
`ENABLE_CLOUD_PUBLICATION=false`.

Estado posterior al cierre Sprint 16: `PRIVATE_DRY_RUN` fue validado sin
objetos de storage. Mantener `ENABLE_PRIVATE_PUBLICATION=false`, el bucket
privado y los workflows Sprint 16 inactivos. Ante regresion, hacer rollback del
servicio al release `v1.7.0`; no revertir SQL 003 con operaciones destructivas.

## Revision o publicacion privada anomala

- Bloquear inmediatamente `ENABLE_PRIVATE_PUBLICATION=false`; no habilitar la
  publicacion publica como alternativa.
- Conservar `review_queue`, `review_decisions`, `dataset_approvals` y
  `execution_events` como evidencia; no borrar observaciones para ocultar una
  incidencia.
- Revocar URLs firmadas activas, revisar el manifiesto/checksum y registrar una
  alerta operativa con el responsable de la investigacion.

## FastAPI no responde

- Revisar deploy/build y `/health`; esperar el arranque en frio previsto.
- Limitar a tres intentos con esperas de 20/40 segundos.
- Si no recupera, detener la corrida y hacer rollback desde Render Events.
- No crear keepalive ni ampliar reintentos indefinidamente.

## n8n no responde

- Confirmar `/healthz`, estado del servicio y monitor existente.
- No llamar al webhook desde UptimeRobot.
- Desactivar GitHub hasta recuperar n8n; no crear un segundo n8n.

## Supabase no responde o migracion incompleta

- `/health` debe quedar `degraded` y n8n no continuar.
- Detener escrituras; no cambiar al Supabase de n8n como fallback.
- Verificar proyecto `proyecto-super-staging`, orden `001`/`002`, tablas y
  buckets. No ejecutar SQL destructivo.

## GitHub Action falla

- Revisar conclusion, HTTP y presencia de Secrets sin imprimir valores.
- Mantener la variable en `false` hasta corregir.
- Reejecutar con el mismo run ID conserva `execution_id` estable.

## Clave invalida

- 401: header ausente. 403: clave incorrecta.
- Rotar en Render y n8n coordinadamente; rotar webhook token en n8n/GitHub.
- Nunca copiar claves a logs, issues o documentos.

## Datos vacios o fuente modificada

- Marcar `EMPTY`/`FAILED`, bloquear proceso/publicacion y conservar evento.
- Restaurar fixture. Si hay 403, CAPTCHA o cambio estructural, no evadir ni
  insistir agresivamente.

## Ejecucion duplicada o job interrumpido

- Repetir con el mismo `execution_id` y verificar el mismo `run_id`.
- Consultar `scrape_runs`, `price_observations`, `execution_events` y objetos por
  `run_id`. No borrar evidencia antes de inventariarla.
- Un job `RUNNING` abandonado requiere revision manual; no lanzar otro ID para
  ocultarlo.

## Publicacion inesperada

- Aplicar los cuatro kill switches, revocar accesos al bucket y rotar service
  role. Conservar el dataset y eventos como evidencia privada.
- Registrar ventana, aprobador, run ID y consumidores afectados.

## Recuperacion desde fixture

- `SOURCE_MODE=fixture`, limites 3/1 y `ENABLE_PUBLICATION=false`.
- Ejecutar health, autenticacion, scrape, process e idempotencia.
- Reactivar GitHub solo despues de una prueba manual completa y volver a
  `false` al cerrar la ventana de validacion.

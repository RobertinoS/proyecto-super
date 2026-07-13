# Auditoria de automatizacion existente

Fecha: 2026-07-13. Base auditada: `main` en tag `v1.5.0`.

## Resultado ejecutivo

No existian `.github/workflows/`, `automation/`, `render.yaml` ni `Dockerfile`. Tampoco habia referencias versionadas a UptimeRobot, n8n, Render, Supabase, webhooks o health checks. Por ello aplica el escenario D: no existe workflow cloud compatible y se crea un unico trigger diario.

## Inventario

| Artefacto | Trigger | Frecuencia | Objetivo | Keepalive | Deploy | Scheduler cloud | Decision |
|---|---|---:|---|---|---|---|---|
| `scripts/register_update_task.ps1` | Windows Task Scheduler | cada 5 horas por defecto | ejecutar pipeline local | no | no | no | conservar como opcion local legacy |
| `run_update.bat` | tarea local/manual | bajo demanda | `src/run_pipeline.py --all` y log local | no | no | no | conservar; no usar en cloud |
| `.github/workflows/` inicial | inexistente | n/a | n/a | n/a | n/a | n/a | crear un trigger diario |
| n8n externo declarado | webhook externo, no auditable desde Git | desconocida | automatizacion general | UptimeRobot lo mantiene activo | externo | candidato | no duplicar instancia; importar workflow Sprint 14 tras revision |

## Workflow agregado

`.github/workflows/daily-price-refresh.yml`:

- `schedule`: `17 10 * * *` (07:17 America/Argentina/Buenos_Aires mientras aplique UTC-3);
- `workflow_dispatch` manual;
- llama una sola vez al webhook productivo de n8n;
- usa `N8N_PRODUCTION_WEBHOOK_URL` y `N8N_WEBHOOK_TOKEN` desde GitHub Secrets;
- timeout de job de 10 minutos y hasta tres intentos totales de HTTP;
- envia `execution_id` deterministico por intento de GitHub;
- no scrapea, no despliega y no mantiene servicios despiertos.

## Riesgos y controles

- No fue posible auditar la configuracion privada de n8n, UptimeRobot, GitHub o Supabase desde el repo. Debe completarse el checklist manual antes de activar.
- Si ya existe en GitHub un workflow no descargado al repo, comparar horarios y deshabilitar uno para evitar doble ejecucion.
- UptimeRobot debe apuntar a `/healthz` de n8n, nunca a `/webhook/`.
- El scheduler local puede coexistir, pero no debe usarse sobre los mismos datasets cloud sin una estrategia de deduplicacion.

## Elementos a conservar, modificar y deshabilitar

- Conservar: infraestructura externa existente y automatizacion local como contingencia.
- Modificar manualmente: secretos, URL productiva, variables n8n y horario final.
- Deshabilitar: cualquier keepalive de GitHub Actions si existe fuera del repo; UptimeRobot ya cumple ese rol.

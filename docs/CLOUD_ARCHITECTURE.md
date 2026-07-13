# Arquitectura cloud Sprint 14

## Flujo logico

```text
GitHub Actions (diario/manual)
  -> webhook n8n en Render
  -> GET FastAPI /health (arranque en frio)
  -> POST FastAPI /jobs/scrape
  -> fuente oficial Vea, canal ONLINE
  -> POST /pipeline/process
  -> Supabase: runs, observaciones, eventos y Storage
  -> aprobacion explicita
  -> POST /pipeline/publish
  -> dataset publicado
  -> dashboard Proyecto Super
```

## Responsabilidades

- GitHub Actions: scheduler unico, no scraping ni keepalive.
- UptimeRobot: disponibilidad de n8n; nunca ejecuta scraping.
- n8n: autenticacion del webhook, `execution_id`, precalentamiento, orquestacion, gates y alertas.
- FastAPI: adaptadores, normalizacion, calidad, idempotencia y persistencia.
- Supabase: persistencia durable; el filesystem de Render no es fuente de verdad.
- Dashboard: consulta y decision; no contiene service role ni claves privadas.

## Despliegue y arranque en frio

n8n puede mantenerse activo con UptimeRobot. FastAPI puede dormir. n8n llama primero a `/health` con timeout de 120 segundos, hasta tres intentos y espera progresiva. Solo continua con HTTP 200 y `status=ok`. Render documenta que un servicio Free puede suspenderse tras 15 minutos sin trafico y tardar cerca de un minuto en despertar; tambien documenta filesystem efimero: [Render Free](https://render.com/docs/free).

## Idempotencia

- GitHub envia `execution_id=gha-{run_id}-{attempt}`.
- FastAPI mantiene indice por `execution_id` y devuelve el mismo `run_id` ante reintento.
- Supabase declara `scrape_runs.execution_id unique` y `price_observations unique(run_id, raw_hash)`.
- Storage usa rutas con `run_id`; no se sobrescriben snapshots.
- La publicacion tiene unicidad por corrida/estado y requiere calidad + aprobacion.

## Flujo de error

1. Infraestructura no saludable: n8n detiene la corrida y responde `FAILED`.
2. Fuente vacia o modificada: run `EMPTY`/`FAILED`; no procesa ni publica.
3. Calidad insuficiente: `QUALITY_REJECTED`; publicacion HTTP 409.
4. Supabase falla: conservar error estructurado; no publicar.
5. Ejecucion repetida: devolver corrida existente sin duplicar observaciones.

## Seguridad

- Webhook n8n y FastAPI usan secretos diferentes.
- FastAPI protege jobs y pipeline con `X-API-Key` y comparacion constante.
- `/health` y `/sources` son publicos y no exponen secretos.
- Service role vive solo en Render/n8n Credentials, nunca en frontend ni Git.
- CORS no se habilita en Sprint 14: el dashboard no llama directamente a FastAPI.

## Persistencia y recuperacion

Supabase guarda metadatos y observaciones; Storage guarda raw, processed y published. Ante reinicio de Render, la API reconstruira estado desde Supabase en una fase posterior. En Sprint 14 el registro en memoria sirve para una corrida sincrona y tests; no se promete recuperacion de jobs en curso tras reinicio.

## Monitoreo

- UptimeRobot: `/healthz` n8n.
- Render: `/health` FastAPI para health check de despliegue.
- n8n: execution log y rama de error.
- Supabase: `source_health` y `execution_events`.
- Heartbeat opcional: solo para confirmar finalizacion diaria, no para disparar scraping.

## Limites y criterio de pago

Render Free no es produccion garantizada, comparte 750 horas mensuales por workspace, puede suspender servicios por alto trafico saliente y no conserva archivos locales. Evaluar plan pago cuando haya SLA, mas de una corrida diaria, catalogos grandes, necesidad de jobs asincronos, consumo cercano al limite o suspensiones. Priorizar pagar n8n si es el orquestador critico; FastAPI puede seguir bajo demanda mientras el volumen lo permita.

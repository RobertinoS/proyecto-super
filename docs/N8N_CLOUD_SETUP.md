# Configuracion n8n y UptimeRobot

## Validacion UptimeRobot Sprint 15

La revision es manual; no se modifica UptimeRobot desde el repo.

- [ ] Monitor HTTP(s) existente apunta al dominio de n8n y termina en
  `/healthz` o equivalente.
- [ ] La URL no contiene `/webhook/` ni parametros secretos.
- [ ] Intervalo menor a 15 minutos, respuesta 200 y alertas activas.
- [ ] No existe monitor para mantener FastAPI despierta.
- [ ] No se creo un segundo monitor ni otro n8n.

Registrar solo resultado y fecha; no guardar el dominio privado completo.

Resultado 2026-07-13: el endpoint publico `/healthz` del unico servicio n8n
observado en Render respondio HTTP 200 con `status=ok`. La cuenta de UptimeRobot
requiere autenticacion en esta sesion, por lo que URL configurada, intervalo y
alertas permanecen pendientes de verificacion manual. No se modifico el monitor.

## Workflow staging Sprint 15

Importar `Proyecto Super - Daily Price Refresh - Staging` desactivado. El JSON
realiza hasta tres GET `/health` separados, con timeout 120 segundos y esperas
progresivas de 20 y 40 segundos. Usa limite 5/1, fuerza `dry_run=true` y no
activa schedule interno. Mismo `execution_id` conserva el mismo run en FastAPI.

No importar hasta que FastAPI provenga de un commit auditado y Supabase staging
este aislado. Configurar `ENABLE_CLOUD_PUBLICATION=false`.

## UptimeRobot: checklist manual

- [ ] Monitor HTTP(s) apunta al dominio de n8n.
- [ ] Endpoint recomendado: `/healthz`.
- [ ] Intervalo menor a 15 minutos mientras se use Render Free.
- [ ] Espera HTTP 200 y tiene alertas configuradas.
- [ ] Nombre identificable, por ejemplo `Proyecto Super - n8n health`.
- [ ] La URL **no contiene `/webhook/`**.
- [ ] El monitor no ejecuta scraping.
- [ ] No existe monitor permanente para FastAPI.
- [ ] Heartbeat opcional separado confirma fin de corrida diaria, no la dispara.
- [ ] Consumo de Render revisado mensualmente.

UptimeRobot no debe apuntar al webhook productivo de scraping.

## Importar workflow

1. Respaldar el workflow n8n existente.
2. Importar `automation/n8n/proyecto_super_daily_scrape.json` desactivado.
3. Configurar variables/credenciales: `N8N_WEBHOOK_TOKEN`, `FASTAPI_BASE_URL`, `SCRAPER_API_KEY`, `ENABLE_CLOUD_PUBLICATION=false`.
4. Regenerar el webhook de produccion y guardarlo como GitHub Secret `N8N_PRODUCTION_WEBHOOK_URL`.
5. Guardar el token como `N8N_WEBHOOK_TOKEN` en GitHub y n8n; no escribirlo en JSON.
6. Verificar que `/health` tolera arranque en frio: timeout 120 s, 3 intentos, espera 30 s.
7. Ejecutar manualmente con `dry_run=true`, limite bajo y `SOURCE_MODE=fixture`.
8. Revisar cada nodo, logs y respuesta estructurada antes de activar.

## Gates y recuperacion

- El webhook valida token y payload.
- `execution_id` evita duplicados.
- Si FastAPI no esta saludable, responde error y no publica.
- Si no hay productos o calidad falla, bloquea publicacion.
- Sprint 14 solo permite llamada de publicacion en `dry_run`; `ENABLE_PUBLICATION=false` en API.
- Ante 401/403, revisar credenciales sin imprimirlas.
- Ante timeout, revisar arranque en frio y no aumentar reintentos indefinidamente.
- Ante cambio de fuente/parsing, desactivar workflow y actualizar fixture/adaptador.

## Prueba manual de webhook

Usar la UI de n8n o un cliente local con headers secretos configurados fuera del historial. Nunca compartir la URL productiva completa en capturas o logs.

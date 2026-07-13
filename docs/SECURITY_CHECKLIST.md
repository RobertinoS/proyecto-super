# Checklist de seguridad cloud

## Antes de desplegar

- Generar claves aleatorias distintas para `N8N_WEBHOOK_TOKEN` y `SCRAPER_API_KEY`.
- Guardar secretos en GitHub Secrets, n8n Credentials/variables y Render Environment Secrets.
- Guardar `SUPABASE_SERVICE_ROLE_KEY` solo en backend; nunca en dashboard, logs o workflow JSON.
- Confirmar que `.env`, dumps, cookies, capturas privadas y logs siguen ignorados.
- Rotar cualquier secreto expuesto y revisar historial Git.
- Restringir CORS; Sprint 14 no habilita CORS porque el browser no llama a la API.
- Mantener `/health` publico pero sin detalles sensibles; revisar si `/sources` debe protegerse al pasar a produccion.
- Proteger `/jobs/*` y `/pipeline/*` con `X-API-Key`.
- Configurar rate limit en proxy/n8n antes de exponer uso general.
- Aplicar RLS a tablas y buckets; no crear politicas anonimas de escritura.
- Revisar que el service role omite RLS y por eso requiere custodia reforzada.

## Operacion

- No registrar headers de autenticacion, cookies ni bodies con secretos.
- Rotar claves trimestralmente o ante incidente.
- Revocar webhook y API key si aparecen ejecuciones no reconocidas.
- Revisar eventos 401/403, fallos consecutivos y volumen atipico.
- Limitar productos, paginas, timeout, reintentos y delay.
- Mantener publicacion desactivada hasta aprobar calidad y acceso del dashboard.

## Incidentes

1. Desactivar workflow GitHub y workflow n8n.
2. Rotar webhook token, API key y service role si aplica.
3. Revisar `execution_events`, n8n executions y logs Render.
4. Bloquear publicaciones afectadas y conservar evidencia sin datos privados.
5. Documentar causa, ventana, datasets y recuperacion.

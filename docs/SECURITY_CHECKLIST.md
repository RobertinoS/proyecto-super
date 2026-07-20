# Checklist de seguridad cloud

## Sprint 17A

- [x] JWT humano y `X-API-Key` de maquina son dependencias separadas.
- [x] JWT valida firma por JWKS, `kid`, algoritmo asimetrico, issuer,
  expiracion y audiencia cuando se configura.
- [x] JWKS usa cache acotado y refresh controlado ante rotacion de `kid`.
- [x] Roles se leen desde `app_user_roles`; no se confia en claims de rol.
- [x] `app_user_roles` y `dataset_access_logs` tienen RLS y revoke para
  `anon`/`authenticated` en la migracion local 004.
- [x] Logs de acceso no guardan JWT, API keys, headers, IP completa ni URL
  firmada; `(user_id, request_id)` evita auditoria duplicada por reintento.
- [x] `.env.example` contiene solo placeholders y los flags siguen bloqueados.
- [ ] Aplicar 004 solo tras confirmar nuevamente `proyecto-super-staging`.
- [ ] Configurar issuer, audience y JWKS reales exclusivamente en secretos de
  Render; no ponerlos en Git, n8n, dashboard o documentacion publica.

## Sprint 15

- [ ] Supabase separado `proyecto-super-staging`; no compartir base con n8n.
- [ ] GitHub variable `PROJECT_SUPER_AUTOMATION_ENABLED=false` por defecto.
- [ ] Workflow n8n importado inactivo y `ENABLE_CLOUD_PUBLICATION=false`.
- [ ] Render con fixture, limites 5/1 y `ENABLE_PUBLICATION=false`.
- [ ] Cero monitores/keepalives para FastAPI.
- [ ] Migraciones `001`/`002` validadas y sin operaciones destructivas.
- [ ] Buckets privados; sin policies anon/authenticated.
- [ ] Prueba de reintento conserva run ID y cero observaciones nuevas.
- [ ] Logs contienen IDs/estados, nunca headers ni valores secretos.
- [ ] Secretos distintos para webhook, FastAPI y service role.
- [ ] Live manual vuelve a fixture al terminar.

## Sprint 16

- [x] Migracion `003` aplicada solo en `proyecto-super-staging`, nunca en el
  Supabase operativo de n8n.
- [x] `ENABLE_PRIVATE_PUBLICATION=false` antes, durante y despues de pruebas.
- [x] `review_queue`, decisiones, aprobaciones y alertas tienen RLS y revoke
  para roles `anon` y `authenticated`.
- [x] El dashboard carga solo JSON saneado y rechaza claves con nombres de
  secretos; no contiene API key ni URL privada.
- [x] Toda decision registra responsable, timestamp e idempotency key.
- [x] No se habilita publicacion publica, bucket publico ni schedule automatico.
- [x] URL firmada solo se emite desde FastAPI autenticada y por tiempo corto.
- [x] `PRIVATE_DRY_RUN` deja evidencia durable sin objetos de storage ni URL
  publica; el bucket de publicacion se mantiene privado.

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

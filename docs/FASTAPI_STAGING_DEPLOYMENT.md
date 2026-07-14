# Despliegue FastAPI staging en Render

Estado: repo preparado; despliegue externo pendiente de candidato versionado y
acceso autenticado. No crear otro n8n ni monitor UptimeRobot para FastAPI.

## Servicio

- Nombre: `Proyecto Super FastAPI Staging`.
- Tipo: Web Service.
- Repositorio: Proyecto Super.
- Branch: rama auditada de Sprint 15; despues del cierre, `main`.
- Root directory: vacio/raiz del repo.
- Runtime: Docker.
- Dockerfile: `cloud_backend/Dockerfile`.
- Docker context: raiz (`.`).
- Auto deploy: desactivado.
- Health check: `/health`.

No desplegar la rama sin commit: Render debe construir un commit auditable. No
se publica un commit intermedio solo para destrabar staging.

## Variables iniciales

Usar `docs/EXTERNAL_CONFIGURATION_CHECKLIST.md`. Valores no secretos obligatorios:

```text
APP_ENV=staging
APP_VERSION=1.6.0
SOURCE_MODE=fixture
ENABLE_PUBLICATION=false
REQUEST_TIMEOUT_SECONDS=120
REQUEST_DELAY_SECONDS=2
MAX_PRODUCTS_PER_RUN=5
MAX_PAGES_PER_RUN=1
LOG_LEVEL=INFO
```

Las tres variables sensibles se cargan como secretos: `SCRAPER_API_KEY`,
`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.

## Validacion

1. Revisar build de Python 3.11 y dependencias, sin valores de entorno en logs.
2. Confirmar que Uvicorn escucha en `$PORT`.
3. Abrir `/health`: debe responder 200 con `status=ok`, `environment=staging`,
   `source_mode=fixture`, `staging_ready=true`.
4. Abrir `/docs`: HTTP 200.
5. Verificar `/jobs/scrape` sin clave (401), clave incorrecta (403) y clave
   correcta (200).
6. Ejecutar fixture con 3 productos, 1 pagina y `dry_run=true`.
7. Consultar `/jobs/{run_id}` y confirmar persistencia tras redeploy/reinicio.
8. Procesar y comprobar `READY_FOR_APPROVAL`.
9. Probar publicacion sin aprobacion (409) y con aprobacion (DRY_RUN).

## Arranque en frio

n8n realiza tres GET independientes a `/health`, con timeout de 120 segundos y
esperas de 20 y 40 segundos. Solo continua con `status=ok`. FastAPI puede dormir;
no recibe keepalive ni monitor UptimeRobot.

## Logs y rollback

- Buscar `execution_id`, `run_id`, etapa, estado y cantidades.
- No registrar headers, cuerpos de autenticacion ni service role.
- Ante fallo, desactivar n8n/GitHub, restaurar fixture y ejecutar rollback al
  deploy anterior desde Render Events.
- El filesystem no es persistencia; Supabase staging es obligatorio para
  `staging_ready=true`.

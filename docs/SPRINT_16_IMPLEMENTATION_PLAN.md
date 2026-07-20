# Plan de implementacion - Sprint 16

## Estado inicial

- Base: `main` en `v1.7.0`, sin cambios pendientes.
- Staging aislado: `proyecto-super-staging`; el proyecto operativo de n8n queda
  fuera de alcance.
- Circuito fixture GitHub Actions -> n8n -> FastAPI -> Supabase validado.
- Gates vigentes: `PROJECT_SUPER_AUTOMATION_ENABLED=false`,
  `SOURCE_MODE=fixture`, `ENABLE_PUBLICATION=false` y
  `ENABLE_CLOUD_PUBLICATION=false`.

## Alcance

1. Cola de revision y aprobacion de datasets, con trazabilidad durable.
2. Publicacion privada opcional, bloqueada por defecto y solo en dry run local.
3. Resumen operativo, estado de fuentes y alertas autenticadas.
4. Seccion acotada de operacion cloud en el dashboard, sin secretos ni acceso
   directo a Supabase.
5. Workflow n8n de notificacion importable e inactivo; no aprueba ni publica.

## Arquitectura

```text
Supabase staging
  <- FastAPI: runs, reviews, approvals, alerts, datasets privados
  <- n8n: orquestacion y notificacion estructurada
Dashboard local
  <- carga manual de resumen/revision o backend autenticado futuro
GitHub Actions
  -> solo webhook n8n, gobernado por kill switch
```

## Archivos permitidos

- `cloud_backend/`, `supabase/migrations/`, `automation/n8n/`, `dashboard/`.
- `scripts/13_validate_supabase_migrations.py`, pruebas y documentacion cloud.
- `.env.example`, `render.yaml` y workflow GitHub solo si conservan gates seguros.

## Archivos prohibidos

- Datos reales en `data/raw/`, outputs en `data/processed/` y archivos `.env`.
- Tablas, esquemas o configuracion del n8n operativo.
- Credenciales, URLs privadas, secretos, cambios de infraestructura externa y
  cualquier fuente adicional o scraping masivo.

## Riesgos y rollback

- Una aprobacion mal aplicada no puede alterar observaciones originales: se
  registra una decision y se revoca el dataset privado si hiciera falta.
- Un fallo de Supabase deja la API en modo bloqueado; no hay fallback al
  Supabase de n8n.
- La publicacion privada requiere `ENABLE_PRIVATE_PUBLICATION=true` y una
  aprobacion; por defecto responde dry run o bloqueo.
- Rollback: mantener los tres flags de seguridad en `false`, desactivar el
  workflow de notificacion y volver al commit/tag anterior.

## Criterios de aceptacion

- Revision, aprobacion, rechazo, correccion y descarte idempotentes y trazables.
- Incidencias criticas pendientes bloquean la aprobacion del dataset.
- Dataset aprobado solo se genera como private dry run por defecto.
- Operaciones, fuentes y alertas no exponen secretos.
- Dashboard presenta estado cloud y bandeja de revision sin API key.
- Pytest no usa Supabase real ni scraping live; `v1.7.0` permanece compatible.

## Regla de corte

Detener validacion externa si falta aislamiento de staging, aparece un secreto,
un gate permite publicacion publica, un workflow aprueba automaticamente o una
migracion toca estructuras de n8n. Documentar el bloqueo y conservar fixture.

# Decision de aislamiento Supabase - Sprint 15

Actualizado: 2026-07-13.

## Opcion elegida

Usar un proyecto Supabase separado llamado `proyecto-super-staging`.

No se autoriza aplicar las migraciones de Proyecto Super en el proyecto que
almacena la operacion interna de n8n. La alternativa de esquema o prefijo
dedicado queda descartada para este sprint porque incrementa el riesgo operativo
y exige auditar permisos y tablas privadas de una plataforma compartida.

## Motivo

- Aisla limites, service role, Storage, RLS, backups y retencion.
- Elimina colisiones con tablas o migraciones internas de n8n.
- Permite destruir o recrear staging en el futuro sin afectar al orquestador.
- Hace inequívoca la separacion entre staging y produccion.

## Tablas existentes detectadas

No se consulto ningun Supabase externo durante la preparacion local. Por lo
tanto, las tablas del proyecto operativo de n8n se consideran desconocidas y no
se enumeran. Esta falta de inventario es una razon para no reutilizarlo.

Antes de ejecutar SQL, el proyecto nuevo debe mostrar solo esquemas y objetos
base de Supabase. Si aparecen tablas de n8n como `workflow_entity`,
`execution_entity`, `credentials_entity` o equivalentes, se aplica la regla de
corte y no se ejecuta la migracion.

## Nombres finales

- Proyecto: `proyecto-super-staging`.
- Esquema aplicativo: `public`, permitido solo porque el proyecto es exclusivo.
- Tablas: `scrape_runs`, `price_observations`, `publication_runs`,
  `source_health`, `execution_events`.
- Buckets: `raw-price-snapshots`, `processed-price-datasets`,
  `published-price-datasets`.

## Riesgo de colision

Con un proyecto exclusivo, el riesgo de colision con n8n es bajo y verificable.
Reutilizar el proyecto de n8n se clasifica como riesgo alto y requiere una nueva
decision aprobada explicitamente; no es un fallback automatico.

## Rollback

1. Desactivar GitHub Actions y el workflow n8n de Proyecto Super.
2. Mantener `ENABLE_PUBLICATION=false` y `SOURCE_MODE=fixture`.
3. Revocar la service role configurada en Render si hubo exposicion.
4. Conservar logs/evidencia no sensible y detener escrituras.
5. Revertir objetos solo dentro de `proyecto-super-staging`, mediante SQL
   revisado manualmente. Las migraciones del repo no contienen rollback
   destructivo automatico.

## Impacto sobre n8n

Ninguno. n8n conserva su Supabase, tablas, credenciales y monitor actuales. Solo
invoca FastAPI mediante HTTPS y `X-API-Key`; no recibe la service role de
Proyecto Super ni acceso directo a sus tablas.

## Estado de la decision

Decision tecnica aprobada en el repo. Creacion y verificacion del proyecto
externo pendientes de una sesion autenticada. Hasta entonces no existe staging
aislado operativo y no se ejecuta `001` ni `002`.

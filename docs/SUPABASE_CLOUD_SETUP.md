# Configuracion Supabase para scraping cloud

## Decision Sprint 15

Se uso exclusivamente un proyecto separado `proyecto-super-staging`; no se
aplico SQL sobre la base operativa de n8n. Ver
`docs/SUPABASE_ISOLATION_DECISION.md`. Las migraciones revisadas se aplicaron
manualmente solo en staging. `002` crea/refuerza buckets privados, revoca roles
de navegador y agrega contratos de staging sin borrar datos.

Validacion previa obligatoria:

```powershell
python scripts/13_validate_supabase_migrations.py
```

No ejecutar migraciones automaticamente. La ejecucion manual en staging ya fue
validada; futuras modificaciones deben revisarse en un proyecto de prueba antes
de aplicarse.

## Extension Sprint 16 pendiente de aplicar

`003_review_and_private_publication.sql` es aditiva y no modifica 001/002.
Solo se puede aplicar tras revisar el validador estatico y confirmar que la
conexion apunta a `proyecto-super-staging`. Agrega:

- `review_queue` y `review_decisions` para decisiones trazables;
- `dataset_approvals` con una aprobacion por corrida;
- `operational_alerts` para salud operativa.
- `private_datasets` como indice durable de manifiestos/checksums privados.

Las cuatro tablas mantienen RLS y revocan acceso de `anon` y
`authenticated`. No ejecutar en el proyecto Supabase de n8n ni usarlo como
fallback. La aplicacion manual y evidencia externa de 003 permanecen pendientes
durante la implementacion local.

## Tablas propuestas

- `scrape_runs`: corrida idempotente por `execution_id`.
- `price_observations`: observaciones por `run_id` y `raw_hash`.
- `publication_runs`: aprobacion y dataset publicado.
- `source_health`: salud y fallos consecutivos.
- `execution_events`: eventos estructurados de orquestacion.

Todas tienen RLS habilitado y ninguna politica anonima de escritura. El service role del backend omite RLS y no debe compartirse; ver [Storage Access Control](https://supabase.com/docs/guides/storage/security/access-control).

## Buckets

| Bucket | Acceso | Ruta |
|---|---|---|
| `raw-price-snapshots` | privado | `source/YYYY/MM/DD/run_id/timestamp.json` |
| `processed-price-datasets` | privado | `processed/YYYY/MM/DD/run_id/precios_procesados.csv` |
| `published-price-datasets` | privado con lectura controlada | `published/YYYY/MM/DD/run_id/precios_publicados.csv` |

Los buckets privados requieren JWT o URL firmada; Supabase documenta que los buckets son privados por defecto y que las signed URLs deben tener vencimiento: [Storage Buckets](https://supabase.com/docs/guides/storage/buckets/fundamentals).

Para Sprint 16 la ruta privada prevista cambia a
`published/YYYY/MM/DD/run_id/precios_aprobados.csv` junto con
`manifiesto.json`. No se escribe mientras `ENABLE_PRIVATE_PUBLICATION=false`.

## Creacion manual

1. Crear los tres buckets privados en Storage.
2. Limitar MIME a JSON/CSV y tamano por objeto.
3. Aplicar SQL revisado en entorno de prueba.
4. Configurar `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` solo en Render.
5. Ejecutar API en `SOURCE_MODE=fixture`, `ENABLE_PUBLICATION=false`.
6. Verificar inserts de prueba y eliminarlos.
7. Crear una funcion/endpoint backend para URL firmada si el dashboard cloud la necesita; no exponer service role.

## Evidencia de cierre Sprint 15

El E2E con fixture registro una ejecucion, observaciones y eventos en el
proyecto staging aislado, sin duplicados ante idempotencia. La publicacion
efectiva fue cero y los buckets permanecen privados. No se documentan IDs,
URLs firmadas ni credenciales.

## Retencion y backup

- Raw: 30 dias iniciales, salvo incidentes o auditoria.
- Processed: 90 dias.
- Published: conservar versiones usadas por usuarios y manifestos.
- Eventos: 180 dias.
- Automatizar limpieza solo despues de medir volumen y probar restauracion.
- Exportar periodicamente metadatos y datasets publicados fuera del filesystem de Render.

# Configuracion Supabase para scraping cloud

No ejecutar migraciones automaticamente. Revisar `supabase/migrations/001_cloud_scraping_foundation.sql` en un proyecto de prueba y aplicar manualmente.

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

## Creacion manual

1. Crear los tres buckets privados en Storage.
2. Limitar MIME a JSON/CSV y tamano por objeto.
3. Aplicar SQL revisado en entorno de prueba.
4. Configurar `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` solo en Render.
5. Ejecutar API en `SOURCE_MODE=fixture`, `ENABLE_PUBLICATION=false`.
6. Verificar inserts de prueba y eliminarlos.
7. Crear una funcion/endpoint backend para URL firmada si el dashboard cloud la necesita; no exponer service role.

## Retencion y backup

- Raw: 30 dias iniciales, salvo incidentes o auditoria.
- Processed: 90 dias.
- Published: conservar versiones usadas por usuarios y manifestos.
- Eventos: 180 dias.
- Automatizar limpieza solo despues de medir volumen y probar restauracion.
- Exportar periodicamente metadatos y datasets publicados fuera del filesystem de Render.

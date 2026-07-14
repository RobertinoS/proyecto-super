# Checklist de Storage staging

Estado: preparado en `002_staging_hardening.sql`; no ejecutado externamente.

## Buckets

| Bucket | Privacidad | Escritura | Lectura | MIME inicial |
|---|---|---|---|---|
| `raw-price-snapshots` | privado | FastAPI service role | backend/auditoria | JSON |
| `processed-price-datasets` | privado | FastAPI service role | backend controlado | CSV |
| `published-price-datasets` | privado | bloqueada en Sprint 15 | backend o URL firmada futura | CSV |

No se crean politicas para `anon` ni `authenticated`. El dashboard no recibe la
service role. `published-price-datasets` no se hace publico durante Sprint 15.

## Rutas

- Raw: `vea/YYYY/MM/DD/{run_id}/{timestamp}.json`.
- Processed: `processed/YYYY/MM/DD/{run_id}/precios_procesados.csv`.
- Published futuro: `published/YYYY/MM/DD/{run_id}/precios_publicados.csv`.

`run_id` es deterministico por `execution_id`; una repeticion no crea una ruta
alternativa. Un HTTP 409 por objeto existente se trata como resultado
idempotente, no como permiso para sobrescribirlo.

## Retencion

- Raw: 30 dias, salvo corrida bajo investigacion.
- Processed: 90 dias.
- Published: sin limpieza automatica hasta definir versionado y restauracion.
- Eventos/metadatos: 180 dias como minimo inicial.

La limpieza no se activa en Sprint 15. Primero se mide volumen, se prueba backup
y se requiere una corrida en dry run del futuro job de retencion.

## Verificacion manual

- [ ] Proyecto visible: `proyecto-super-staging`.
- [ ] Los tres buckets existen y muestran `Public bucket = OFF`.
- [ ] Limite por objeto: 10 MiB.
- [ ] Raw acepta JSON y rechaza CSV.
- [ ] Processed/published aceptan CSV.
- [ ] Clave anonima no puede listar, leer, escribir ni borrar objetos.
- [ ] Service role desde FastAPI puede crear un objeto fixture.
- [ ] Reintento del mismo run no crea un segundo snapshot.
- [ ] No existe URL publica permanente.
- [ ] No existe policy con escritura para `anon` o `authenticated`.

## Rollback

1. Desactivar GitHub/n8n y mantener publicacion en `false`.
2. Revocar la service role de Render si corresponde.
3. Conservar objetos de evidencia mientras se investiga.
4. Eliminar objetos de prueba solo mediante la consola del proyecto staging y
   con inventario previo. No se incluye SQL destructivo en las migraciones.

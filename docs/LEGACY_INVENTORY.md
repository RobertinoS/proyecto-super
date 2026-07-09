# Inventario legacy y artefactos

Sprint 0 no borra ni mueve archivos. Este documento lista candidatos para revision futura.

| Archivo/carpeta | Tipo | Tamano aprox. | Estado | Utilidad | Recomendacion | Accion futura |
|---|---|---:|---|---|---|---|
| `data/raw/` | Capturas crudas HTML/JSON | 199.5 MB | Artefacto operativo pesado | Auditoria y debugging de scrapers | Conservar por ahora | Definir retencion por fecha/fuente en Sprint 8 |
| `data/processed/` | CSV procesados y diagnosticos | 2.6 MB | Artefacto operativo | Auditoria de extracciones | Conservar | Limpiar versiones antiguas solo con politica aprobada |
| `data/export/` | JSON dashboard | 4.9 MB | Activo | Alimenta dashboard | No borrar | Mantener version demo estable |
| `database/precios_san_juan.sqlite` | SQLite | 15.0 MB | Activo | Base local principal | No borrar | Backup antes de migraciones |
| `.pytest_cache/` | Cache pytest | pequeno | Generado | Sin valor funcional | Ignorar en Git | Borrar solo si se aprueba limpieza |
| `logs/` | Carpeta logs | 0 MB | Reservada | Futuro monitoreo | Conservar | Usar en Sprint 6 |
| Git root en `C:\Users\Rober\Desktop` | Configuracion Git | n/a | Riesgo externo al proyecto | Ninguna para el repo actual | No commitear desde ahi | Crear repo dedicado dentro del proyecto o mover `.git` con cuidado |

## No detectado dentro del proyecto actual

- Notebooks `.ipynb`.
- Excel `.xlsx` / `.xls`.
- Bases DuckDB.
- Parquet.
- Entornos virtuales `.venv`, `venv`, `env`.
- Carpeta `streamlit_super`.

## Observaciones

- `data/raw` esta correctamente ignorado por `.gitignore`, pero existe localmente y puede crecer rapido.
- `data/export` no debe ignorarse si se quiere que el dashboard tenga datos demo.
- No se debe limpiar legacy sin aprobacion del usuario y sin backup de base/export.

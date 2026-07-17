# Guia de publicacion privada

## Estado por defecto

Sprint 16 conserva ambos gates apagados:

```text
ENABLE_PUBLICATION=false
ENABLE_PRIVATE_PUBLICATION=false
```

`ENABLE_PUBLICATION` gobierna toda publicacion publica y debe seguir en falso.
`ENABLE_PRIVATE_PUBLICATION` es un gate independiente para escribir un dataset
aprobado solamente en el bucket privado `published-price-datasets`.

## Requisitos de una publicacion privada

1. Corrida procesada con estado `READY_FOR_APPROVAL`.
2. Sin incidencias criticas ni revisiones pendientes.
3. Registro `dataset_approvals` en estado `APPROVED` con responsable.
4. Solicitud autenticada a `POST /runs/{run_id}/private-publish`.
5. Configuracion explicita de `ENABLE_PRIVATE_PUBLICATION=true` para una
   ventana controlada posterior a la validacion staging.

Con el gate apagado o `dry_run=true`, FastAPI devuelve `PRIVATE_DRY_RUN`,
calcula checksum, manifiesto y ruta prevista, pero no escribe objetos.

## Artefactos cuando se habilite de forma controlada

```text
published/YYYY/MM/DD/run_id/precios_aprobados.csv
published/YYYY/MM/DD/run_id/manifiesto.json
```

El manifiesto incluye `run_id`, `approval_id`, timestamp, filas, checksum,
responsable, version del extractor y calidad. No contiene service role,
headers, tokens ni URLs permanentes.

`private_datasets` conserva el indice durable del dataset y su manifiesto, por
lo que los endpoints de consulta no dependen de la memoria de FastAPI despues
de un reinicio.

El bucket permanece privado. El acceso se ofrece por una URL firmada de vida
corta mediante `GET /datasets/{dataset_id}/download-url` o por un backend
autenticado. No se crean datasets ni buckets publicos.

## Verificacion y rollback

- Consultar `GET /datasets/latest-approved` y `GET /datasets/{dataset_id}`.
- Verificar checksum, cantidad de filas y aprobador antes de entregar el CSV.
- Para detener: volver `ENABLE_PRIVATE_PUBLICATION=false`, conservar
  `ENABLE_PUBLICATION=false`, revocar enlaces firmados activos y registrar una
  alerta/revision si corresponde.
- La publicacion publica queda fuera de alcance de Sprint 16.

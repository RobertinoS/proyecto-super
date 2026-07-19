# Gate de publicacion

## Extension Sprint 16: publicacion privada

`ENABLE_PRIVATE_PUBLICATION=false` agrega una segunda barrera, independiente de
la publicacion publica. Un dataset privado requiere una aprobacion durable de
`dataset_approvals`, sin revisiones criticas o pendientes, y una llamada
autenticada. Mientras el gate esta apagado, el resultado es `PRIVATE_DRY_RUN`:
hay checksum, manifiesto y ruta prevista, pero no se escriben objetos.

La publicacion privada, cuando se habilite en una ventana futura, solo usa el
bucket privado `published-price-datasets` y URLs firmadas temporales. No crea
un enlace permanente, acceso anonimo ni publicacion al dashboard publico.

Sprint 15 opera con `ENABLE_PUBLICATION=false`. Ningun workflow, aprobador o
payload puede omitir este bloqueo global.

## Validacion de cierre Sprint 16

La prueba de aprobacion humana y posterior `PRIVATE_DRY_RUN` proceso tres filas
con calidad 100. Se produjo manifiesto y checksum, conservados en
`private_datasets`, sin escritura en Storage. `ENABLE_PUBLICATION=false`,
`ENABLE_CLOUD_PUBLICATION=false` y `ENABLE_PRIVATE_PUBLICATION=false` se
mantuvieron durante toda la validacion.

## Estados permitidos

- `SCRAPED`: extraccion terminada.
- `QUALITY_REJECTED`: calidad insuficiente; publicacion prohibida.
- `READY_FOR_APPROVAL`: calidad aceptable; todavia no publicado.
- `DRY_RUN`: aprobacion ensayada, sin escritura publicada.
- `PUBLISHED`: reservado para un sprint futuro con gate habilitado.
- `REJECTED` o `FAILED`: corrida bloqueada o fallida.

## Condiciones futuras de aprobacion

Todas deben cumplirse:

1. `ENABLE_PUBLICATION=true` mediante cambio controlado.
2. Dataset en `READY_FOR_APPROVAL` y score minimo definido.
3. Aprobacion explicita con identidad no secreta del aprobador.
4. Fuente, canal, fecha, cantidades e incidencias visibles.
5. Repeticion idempotente y Storage privado verificados.
6. Bucket y consumidor autorizados; nunca acceso anonimo de escritura.

Rol aprobador inicial futuro: responsable de datos designado. n8n y GitHub no
son aprobadores por si mismos.

## Reglas de bloqueo Sprint 15

- Sin aprobacion: HTTP 409.
- Con aprobacion pero `ENABLE_PUBLICATION=false`: `DRY_RUN`.
- Calidad rechazada o dataset vacio: HTTP 409.
- Supabase no configurado: no publicar.
- n8n mantiene `ENABLE_CLOUD_PUBLICATION=false` y su nodo de publicacion usa
  siempre `dry_run=true`.
- GitHub solo llama al webhook n8n; no conoce el endpoint de publicacion.
- `published-price-datasets` permanece privado y sin dataset publico.

## Trazabilidad

Los intentos bloqueados o en dry run se registran como eventos y, si Supabase
staging esta disponible, como `publication_runs` idempotentes. Nunca se registran
credenciales ni headers.

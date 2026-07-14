# Gate de publicacion

Sprint 15 opera con `ENABLE_PUBLICATION=false`. Ningun workflow, aprobador o
payload puede omitir este bloqueo global.

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

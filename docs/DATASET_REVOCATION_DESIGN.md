# Diseno de revocacion y restauracion de datasets

## Principios

La revocacion es inmediata para nuevas emisiones de acceso, trazable y no
destructiva. Un archivo que un usuario ya descargo no puede retirarse de su
equipo; por eso la vigencia corta y el control de nuevas emisiones son la
barrera principal.

## Transiciones permitidas

```text
PRIVATE_DRY_RUN -> APPROVED -> PUBLISHED_PRIVATE -> ACTIVE
ACTIVE -> SUPERSEDED | REVOKED
SUPERSEDED -> ACTIVE (restore controlado) | ARCHIVED
REVOKED -> ARCHIVED
FAILED -> ARCHIVED
```

`PUBLISHED_PRIVATE` no se expone hasta que un administrador lo active.
`ACTIVE` es unico por canal/alcance de consumidor. `SUPERSEDED` conserva una
version previamente activa; `ARCHIVED` conserva evidencia sin descarga.

## Revocar

Solo `dataset_admin` puede revocar. El endpoint exige `reason`,
`Idempotency-Key` y confirmacion de la version. En una transaccion debe:

1. Registrar `dataset_revocations` con actor, motivo y estado previo.
2. Cambiar estado a `REVOKED`.
3. Crear `dataset_activation_history` y alerta de severidad segun motivo.
4. Bloquear nuevas URLs y devolver `410` para el dataset.
5. Exigir decision explicita de fallback; por defecto no activar otro dataset.

La misma clave de idempotencia devuelve el resultado existente y no agrega
auditoria duplicada.

## Restaurar y fallback

Un restore requiere dos responsables distintos: solicitante y confirmador. La
version debe estar `SUPERSEDED` o `ARCHIVED`, con aprobacion vigente, checksum
verificado y sin una revocacion propia. Al activarla, el dataset actual pasa a
`SUPERSEDED` y queda un evento de transicion.

Como alternativa, la revocacion puede incluir un `fallback_dataset_id` ya
validado por ambos responsables. Esto evita un periodo sin dataset activo sin
activar automaticamente una version no revisada.

## Rollback

- Servicio: volver Render a `v1.8.0` y mantener los flags en `false`.
- Dataset: restaurar una version elegible mediante endpoint auditado.
- Workflow: desactivar la copia de Sprint 17 y conservar el kill switch.
- Datos: no borrar `private_datasets`, aprobaciones, revisiones, alertas ni
  eventos para ocultar una incidencia.

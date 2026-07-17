# Flujo de revision humana

## Objetivo

Ningun dataset llega al consumidor del dashboard cloud sin una decision humana
trazable. La revision se almacena en `review_queue`; cada accion se agrega a
`review_decisions` y no reescribe la observacion original.

## Estados de una revision

- `PENDING`: detectada automaticamente y pendiente de responsable.
- `IN_REVIEW`: asignada o bajo analisis.
- `APPROVED`: incidencia revisada sin requerir correccion del valor fuente.
- `REJECTED`: incidencia o dato rechazado.
- `CORRECTED`: existe una correccion propuesta con valor anterior y nuevo.
- `DISMISSED`: incidencia descartada con motivo.

Los tipos cubiertos son `PRICE_SUSPICIOUS`, `DUPLICATE`, `SOURCE_CONFLICT`,
`MISSING_FIELD`, `QUALITY_WARNING`, `OUTLIER` y `SOURCE_FAILURE`.

## Endpoints protegidos

- `GET /reviews` admite filtros por estado, severidad, fuente, corrida y tipo.
- `GET /reviews/{review_id}` devuelve una incidencia concreta.
- `POST /reviews/{review_id}/approve`
- `POST /reviews/{review_id}/reject`
- `POST /reviews/{review_id}/correct`
- `POST /reviews/{review_id}/dismiss`
- `POST /runs/{run_id}/request-approval`
- `GET /runs/{run_id}/approval-status`
- `POST /runs/{run_id}/approve-dataset`
- `POST /runs/{run_id}/reject-dataset`

Toda decision requiere `actor`. Un rechazo requiere motivo. Una correccion
requiere `corrected_value` y conserva `previous_value` en la auditoria. Una
solicitud repetida con la misma clave de idempotencia no duplica decisiones.

## Gate de dataset

1. El pipeline debe quedar `READY_FOR_APPROVAL`.
2. FastAPI genera o recupera incidencias de calidad.
3. No puede haber incidencias `CRITICAL` ni estados activos `PENDING` o
   `IN_REVIEW`.
4. El responsable aprueba o rechaza el dataset.
5. Solo un dataset aprobado puede solicitar publicacion privada.

La bandeja del dashboard standalone no llama a FastAPI ni guarda API keys. Es
un modo local para filtrar, preparar decisiones y exportarlas. La aplicacion
durable se realiza desde un cliente autenticado contra FastAPI.

## Auditoria y revocacion

Una aprobacion de dataset es idempotente. Si un problema aparece despues,
registrar una alerta, crear una nueva revision y cambiar el dataset a
`REVOKED` mediante una operacion backend futura; nunca borrar observaciones ni
eventos para ocultar la evidencia.

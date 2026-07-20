# Diseno de consumo privado de datasets aprobados

## Objetivo

Entregar solamente datasets `ACTIVE` a usuarios internos autorizados, con
identidad individual, expiracion, auditoria y cero secretos en el navegador.
La publicacion publica queda fuera de alcance.

## Autenticacion y autorizacion

La identidad recomendada es Supabase Auth. FastAPI valida el JWT y sus claims
de rol; RLS mantiene las tablas y buckets cerrados al cliente directo. FastAPI
usa service-role solo en servidor para leer metadata, registrar auditoria y
emitir URLs firmadas. El navegador nunca recibe esa clave.

Roles iniciales: `viewer`, `reviewer`, `dataset_admin` y `operator`. El
principio es minimo privilegio: `viewer` no ve raw ni puede solicitar versiones
revocadas; `reviewer` no activa; `operator` no aprueba su propia corrida;
`dataset_admin` requiere una segunda confirmacion para restore.

## Acceso temporal

1. El usuario pide acceso al dataset `ACTIVE`.
2. FastAPI valida JWT, rol, estado y limite de descarga.
3. Se registra un intento en `dataset_access_logs` antes de devolver contenido.
4. FastAPI devuelve una URL firmada de cinco minutos o hace proxy del contenido
   si se requiere ocultar por completo la ruta.
5. Tras expirar, una nueva descarga requiere una nueva autorizacion y log.

La primera implementacion debe preferir URL firmada de cinco minutos por costo
y simplicidad. No usar URLs permanentes ni enlaces almacenados en localStorage.
Un limite inicial conservador es cinco emisiones exitosas por usuario y dataset
por hora; excederlo crea alerta `ACCESS_LIMIT_EXCEEDED` y no entrega URL.

## Contrato de acceso propuesto

`POST /private/datasets/{dataset_id}/access`

Entrada: `purpose` corto y `Idempotency-Key`. El actor se obtiene del JWT, no
del cuerpo. Salida: `dataset_id`, `expires_at`, `download_url` y
`checksum_sha256` solo para un dataset activo autorizado. Para metadata usar
`GET /private/datasets/current` o `GET /private/datasets/{dataset_id}`.

Errores: `401` sin identidad, `403` sin rol, `404` no disponible, `410`
revocado, `409` no activo o sin aprobacion, `429` limite de acceso. Ningun
error incluye ruta de bucket, token, URL interna o datos raw.

## Auditoria minima

Cada intento registra resultado `GRANTED`, `DENIED`, `EXPIRED` o `RATE_LIMITED`,
subject estable, rol, dataset, metodo, request_id, expiracion y timestamp. Se
usan hashes o truncamiento para datos de red si fueran imprescindibles; no IP
completa ni user-agent crudo por defecto.

El acceso al dataset no equivale a aprobacion ni altera `dataset_approvals`.
La retencion de logs sigue la politica de datos y no habilita borrado
destructivo durante el piloto.

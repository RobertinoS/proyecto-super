# Runbook de observabilidad

## Alcance Sprint 16

La observabilidad se consulta mediante FastAPI autenticada y registros durables
del proyecto Supabase aislado `proyecto-super-staging`. El dashboard HTML no
recibe claves: puede cargar exportaciones JSON saneadas para consulta local.

Endpoints protegidos:

- `GET /operations/summary`
- `GET /operations/sources`
- `GET /operations/alerts`
- `POST /operations/alerts/{alert_id}/acknowledge`

## Estados de fuente

- `HEALTHY`: existe un exito reciente y no hay fallos consecutivos.
- `DEGRADED`: hay fallos recientes, pero la fuente conserva capacidad parcial.
- `FAILED`: fallos consecutivos o ejecucion fallida que requiere intervencion.
- `STALE`: datos mas antiguos que el umbral operativo definido.
- `DISABLED`: sin ejecucion habilitada o sin evidencia suficiente.

## Rutina de revision

1. Consultar resumen y fuentes con una credencial backend autorizada.
2. Revisar alertas abiertas por severidad y reconocer solo las comprendidas.
3. Abrir la bandeja de revision para corridas con calidad insuficiente,
   duplicados, conflictos u outliers.
4. Solicitar aprobacion de dataset solo cuando no existan incidencias criticas
   pendientes.
5. Mantener `PROJECT_SUPER_AUTOMATION_ENABLED=false` fuera de una ventana
   manual controlada.

## Respuesta a eventos

### Fuente caida o estructura modificada

- Registrar alerta `SOURCE_FAILURE` o `SOURCE_CONFLICT`.
- Mantener `SOURCE_MODE=fixture` y no insistir ante CAPTCHA, login, 403 o rate
  limit.
- Revisar el adaptador y ejecutar fixture antes de una nueva prueba live.

### FastAPI dormida o no disponible

- n8n debe usar el warm-up `GET /health` existente y respetar sus tres
  intentos progresivos.
- Si no recupera, detener el flujo, revisar Render y no crear keepalives.

### Supabase no disponible

- No usar el Supabase operativo de n8n como fallback.
- Mantener jobs staging bloqueados/degradados hasta recuperar
  `proyecto-super-staging`.

### Datos vacios o calidad insuficiente

- Crear o conservar la revision correspondiente.
- No aprobar el dataset ni intentar publicacion privada.
- Documentar causa, fuente, corrida y accion siguiente sin copiar valores
  sensibles ni URLs privadas.

## Rollback

1. Mantener `ENABLE_PUBLICATION=false`.
2. Mantener `ENABLE_PRIVATE_PUBLICATION=false`.
3. Cambiar `PROJECT_SUPER_AUTOMATION_ENABLED=false`.
4. Desactivar el workflow n8n de Proyecto Super si una ejecucion esta activa.
5. Restaurar `SOURCE_MODE=fixture`.
6. Revertir el deploy de FastAPI desde Render solo despues de preservar eventos
   y evidencia no sensible.

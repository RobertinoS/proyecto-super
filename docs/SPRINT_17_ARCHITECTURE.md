# Sprint 17 - Arquitectura de consumo privado y operacion supervisada

## Estado de partida

La base es `v1.8.0`. Sprint 16 ya aporta revision humana, aprobacion de
dataset, alertas, `private_datasets`, storage privado y `PRIVATE_DRY_RUN`.
El consumo de contenido aprobado, su revocacion y la operacion live sostenida
todavia no existen. El proyecto Supabase de staging sigue aislado del entorno
operativo de n8n.

## Alcance y limites

Sprint 17 habilitara consumo autenticado de datasets privados aprobados,
auditoria de accesos, activacion/revocacion/restore trazables y un piloto Vea
live supervisado. No habilita publicacion publica, no entrega service-role al
frontend, no activa un schedule diario y no cambia la fuente por defecto de
`fixture` fuera de ventanas manuales aprobadas.

Cada bloque de implementacion posterior tendra su propia rama y auditoria. No
se implementan migraciones, codigo, variables, workflows, Render ni buckets en
esta rama de planificacion.

## Consumidor inicial y permisos

El consumidor inicial recomendado es un equipo interno pequeno: un dashboard
privado para consulta y un administrador de datos para decisiones. Un proceso
backend puede consumir metadata para integraciones futuras, pero no reemplaza
la aprobacion humana.

| Rol | Puede | No puede |
|---|---|---|
| `viewer` | Ver dataset activo, metadata, calidad y alertas permitidas; pedir acceso temporal | Revisar, activar, revocar, ejecutar live |
| `reviewer` | Resolver revisiones y solicitar aprobacion | Activar/revocar datasets, cambiar flags |
| `dataset_admin` | Aprobar, activar, revocar, restaurar y ejecutar corrida manual autorizada | Ver service-role, publicar publicamente |
| `operator` | Iniciar una ventana live manual dentro de limites | Aprobar su propia corrida sin segundo responsable |

El frontend nunca recibe service-role, API keys administrativas, rutas internas
de bucket, snapshots raw, cookies, headers, identificadores de sesion ni URLs
firmadas persistentes. Las acciones sensibles pasan siempre por FastAPI.

## Arquitectura recomendada

Adoptar **Supabase Auth + JWT + RLS como identidad (B)** y **URLs firmadas
temporales emitidas por FastAPI (D)** como mecanismo de entrega. FastAPI es el
punto de decision: valida JWT y rol, aplica las reglas de negocio, registra el
acceso y genera una URL de una sola finalidad y corta vigencia solo para un
dataset `ACTIVE`.

Una API key administrativa (A) queda como herramienta de operacion backend o
emergencia, nunca para el navegador. Una sesion propia (C) no se recomienda:
duplica identidad, rotacion, recuperacion de cuenta y superficie de seguridad
sin aportar ventaja frente a Auth administrado.

| Alternativa | Seguridad | Costo/complejidad | Revocacion/auditoria | Recomendacion |
|---|---|---|---|---|
| A. API key administrativa | Adecuada solo servidor a servidor | Baja | Actor no verificable por usuario; rotacion manual | No para UI |
| B. Supabase Auth + JWT + RLS | Alta, identidad individual y roles | Media, dentro del proyecto existente | Buena; `sub` y claims auditables | Identidad recomendada |
| C. Sesion propia | Media si se construye correctamente | Alta, mantenimiento propio | Requiere toda la infraestructura | Rechazada |
| D. URL firmada temporal | No autentica por si sola | Baja | Expira; no revoca una URL ya emitida | Complemento de B |

Las URLs firmadas no son autorizacion: FastAPI las entrega despues de verificar
un JWT. Para una revocacion inmediata se bloquean nuevas emisiones, se reduce
la vigencia a cinco minutos y se cambia el estado del dataset. No se intenta
invalidar retroactivamente un archivo ya descargado.

## Flujo de consumo propuesto

```text
Usuario autenticado
  -> FastAPI valida JWT, rol y dataset ACTIVE
  -> registra dataset_access_log (sin URL ni secretos)
  -> devuelve metadata o URL firmada de 5 minutos
  -> cliente descarga desde bucket privado
  -> expiracion; nuevas descargas requieren nueva autorizacion
```

Si no existe un dataset activo, el backend responde `404 DATASET_NOT_AVAILABLE`
sin revelar rutas. Si el dataset esta `REVOKED`, responde `410 DATASET_REVOKED`.
El fallback al anterior solo ocurre cuando un `dataset_admin` lo restaura o lo
indica expresamente como fallback elegible en la misma transaccion de
revocacion; nunca se activa una version anterior de forma silenciosa.

## Contratos propuestos, no implementados

Todos los endpoints requieren JWT valido y aplican RBAC en FastAPI. Toda accion
mutante requiere `Idempotency-Key`, `actor` derivado del JWT y `request_id`.

| Endpoint propuesto | Rol | Resultado seguro |
|---|---|---|
| `GET /private/datasets/current` | viewer+ | Metadata del dataset `ACTIVE`, sin ruta interna |
| `GET /private/datasets` | dataset_admin | Historial paginado, estado, calidad y aprobacion |
| `GET /private/datasets/{id}` | viewer+ segun estado | Metadata autorizada |
| `POST /private/datasets/{id}/access` | viewer+ | URL firmada de 300 s o contenido proxy; crea audit log |
| `POST /private/datasets/{id}/activate` | dataset_admin | Activa version aprobada y supersede la anterior |
| `POST /private/datasets/{id}/revoke` | dataset_admin | Motivo obligatorio, bloqueo inmediato de nuevas descargas |
| `POST /private/datasets/{id}/restore` | dataset_admin con segundo responsable | Restaura version historica elegible |

Respuestas de metadata incluyen `id`, `status`, `created_at`, `row_count`,
`quality_score`, `checksum_sha256`, `approval_id` y fechas de estado. Nunca
incluyen bucket, `dataset_path`, manifest path, URL firmada, tokens ni claves.

## Revocacion, archivo y rollback

Estados recomendados: `PRIVATE_DRY_RUN`, `APPROVED`, `PUBLISHED_PRIVATE`,
`ACTIVE`, `SUPERSEDED`, `REVOKED`, `ARCHIVED` y `FAILED`.

- **Revocar**: retira un dataset de consumo inmediato, exige motivo y registra
  actor, estado previo, timestamp e idempotency key.
- **Archivar**: conserva un dataset no activo para retencion; no equivale a
  incidente ni habilita descarga.
- **Eliminar**: no forma parte de Sprint 17; evidencia y objetos se retienen
  conforme a la politica aprobada.
- **Restaurar**: requiere que la version previa siga aprobada, checksum valido,
  sin revocacion propia y segunda confirmacion humana. La version activa se
  vuelve `SUPERSEDED`.

Rollback de servicio: volver Render a `v1.8.0`, conservar gates en `false` y
desactivar los workflows nuevos. Rollback de datos: activar una version previa
conservada, no borrar registros. Rollback de workflow: desactivar la copia
staging y mantener `PROJECT_SUPER_AUTOMATION_ENABLED=false`.

## Modelo de datos propuesto

Se reutilizan `private_datasets`, `dataset_approvals`, `review_queue`,
`review_decisions`, `operational_alerts`, `scrape_runs` y `execution_events`.
No crear `operational_incidents`: `operational_alerts` ya cumple esa funcion.
No crear `live_pilot_runs` inicialmente: usar `scrape_runs.run_meta` y eventos;
evaluar una tabla solo si las consultas de piloto justifican indice propio.

Una futura migracion aditiva podria extender `private_datasets` con estado
operativo, `activated_at`, `revoked_at`, `superseded_by` y `version_number`, y
crear solamente:

- `dataset_access_logs`: dataset, sujeto autenticado, rol, metodo, resultado,
  expiracion, request_id y marca de tiempo; no URL, token ni IP completa.
- `dataset_revocations`: dataset, actor, motivo, estado anterior, idempotency
  key, momento y fallback seleccionado.
- `dataset_activation_history`: transicion, dataset anterior/nuevo, actor,
  motivo, aprobacion y request_id.

## Interfaz administrativa recomendada

Crear una pagina administrativa separada y protegida por autenticacion, servida
por FastAPI o un frontend privado posterior. Es mas clara y segura que mezclar
operaciones destructivas con el dashboard de compra. Swagger queda solo para
staging y pruebas de operadores; no es la interfaz diaria.

La pagina muestra datasets, calidad, aprobacion, historial, alertas, estado de
fuente y accesos. Las acciones Activar, Revocar, Restaurar y Ejecutar live
requieren confirmacion visible, motivo cuando corresponda y una respuesta
auditada. El dashboard de compra solo consume el dataset `ACTIVE` aprobado.

## Alertas minimas

| Alerta | Severidad y condicion | Accion | Detiene / revision |
|---|---|---|---|
| Fuente inaccesible, CAPTCHA, 403 o 429 | HIGH al primer evento | Cortar ventana live, registrar evento | Si / Si |
| Estructura modificada o campos esenciales ausentes | HIGH | Bloquear proceso y volver fixture | Si / Si |
| Cero productos inesperado | HIGH | No aprobar; revisar fuente | Si / Si |
| Caida de productos >30% | MEDIUM | Marcar degradado y comparar corrida previa | No / Si |
| Precio invalido o duplicado | HIGH | Crear review | Si para dataset / Si |
| Calidad <95 | HIGH | No solicitar aprobacion | Si / Si |
| Dataset pendiente >24 h | MEDIUM | Notificar `dataset_admin` | No / Si |
| Publicacion bloqueada | LOW en dry run, HIGH si inesperada | Confirmar gates y auditoria | No / Si |
| Dataset revocado | HIGH | Bloquear nuevas emisiones y evaluar fallback | Si para acceso / Si |
| FastAPI, n8n o Supabase caido | HIGH | Detener orquestacion y seguir runbook | Si / Si |
| Schedule fuera de ventana | CRITICAL | Desactivar job y registrar incidente | Si / Si |
| Tres fallos consecutivos | HIGH | Volver Etapa 0 o 1 | Si / Si |

`operational_alerts` conserva estas alertas. La implementacion debe agregar
tipos sin repetir una tabla de incidentes. Ninguna alerta expone secretos,
cabeceras, URLs firmadas ni contenido raw.

## Division de implementacion

### Sprint 17A - Arquitectura y contratos

- **Objetivo**: convertir este diseno en contratos, estados y migracion
  propuesta revisable.
- **Permitido**: `docs/`, contratos de modelos, validadores estaticos y tests.
- **Prohibido**: desplegar, tocar flags, buckets, n8n, dashboard de compra o
  publicar objetos.
- **Entregables**: decision Auth/RBAC, contrato de endpoints, diseno aditivo de
  tablas y plan de migracion/rollback.
- **Pruebas**: contratos, transiciones de estado, ausencia de secretos y SQL
  no destructivo.
- **Aceptacion/corte**: no hay identidad ambigua ni acceso anonimo; detener si
  RLS o separacion staging no pueden demostrarse.
- **Dependencia/rollback**: `v1.8.0`; reversion consiste en no aplicar cambios.

### Sprint 17B - Consumo privado autenticado y auditoria

- **Objetivo**: autenticar `viewer` y emitir acceso temporal auditado.
- **Permitido**: FastAPI, dependencias JWT, migracion aditiva de auditoria,
  pruebas, configuracion de staging y documentacion.
- **Prohibido**: service-role en browser, URLs permanentes, publicacion publica,
  UI administrativa mutante y schedule.
- **Entregables**: endpoints de metadata/acceso, `dataset_access_logs`, rate
  limit, RBAC y pruebas con JWT simulados.
- **Pruebas**: 401/403, expiracion, limite, dataset no activo/revocado, auditoria
  e idempotencia.
- **Aceptacion/corte**: identidad individual y logs sin URL/token; detener si
  una descarga funciona sin JWT o si se expone una ruta interna.
- **Rollback**: deshabilitar endpoints nuevos y volver Render a `v1.8.0`.

### Sprint 17C - Revocacion, restore y administracion protegida

- **Objetivo**: controlar ciclo `ACTIVE`, `REVOKED`, `SUPERSEDED` y restore.
- **Permitido**: FastAPI, migracion aditiva de estados/auditoria, pagina admin
  separada, tests y runbooks.
- **Prohibido**: borrar evidencia, activar publicacion publica, modificar el
  dashboard de compra para acciones administrativas o automatizar aprobaciones.
- **Entregables**: activate/revoke/restore, doble confirmacion, historial y
  visualizacion protegida de alertas/accesos.
- **Pruebas**: motivo obligatorio, idempotencia, bloqueo inmediato, fallback
  explicito, restore elegible y permisos por rol.
- **Aceptacion/corte**: revocacion bloquea nuevas URLs y no existe doble activo;
  detener ante transicion no auditada o restauracion automatica.
- **Rollback**: activar version previa elegible o volver servicio a `v1.8.0`.

### Sprint 17D - Piloto live supervisado y activacion gradual

- **Objetivo**: ejecutar Vea live manual dentro de los limites documentados y
  avanzar de Etapa 1 a 3 solo con evidencia.
- **Permitido**: configuracion temporal de staging aprobada, n8n de staging
  inactivo/Test URL, `workflow_dispatch`, observabilidad y documentacion.
- **Prohibido**: pytest live, CAPTCHAs/bypass, schedule, paralelismo, publicacion
  publica y cambios permanentes de `SOURCE_MODE`.
- **Entregables**: bitacora de ventanas, evidencia de calidad/duplicados,
  checklist de retorno a fixture y decision de avanzar o cortar.
- **Pruebas**: fixture previo, smoke live limitado, reintentos, alertas, restore
  a fixture e idempotencia.
- **Aceptacion/corte**: cinco exitos en tres dias para Etapa 2; detener ante
  cualquiera de las condiciones de corte del piloto.
- **Rollback**: `SOURCE_MODE=fixture`, gates en false, kill switch false y
  workflow desactivado.

## Decisiones pendientes del usuario

1. Confirmar los usuarios internos iniciales y quien recibe los roles
   `dataset_admin` y `operator`.
2. Aprobar Supabase Auth como proveedor de identidad y el modelo de roles por
   claims, sin cuentas compartidas.
3. Definir retencion de `dataset_access_logs` y si el acceso inicial requiere
   descarga CSV o solo metadata.
4. Autorizar expresamente la futura escritura privada de Etapa 2; no esta
   aprobada por este plan.
5. Elegir ventana horaria de piloto y responsable on-call antes de Etapa 1.

## Regla de corte

Detener cualquier bloque si aparece exposicion de secretos, un dataset publico,
ambiguedad entre staging y otro proyecto, ausencia de auditoria, descarga sin
identidad, revocacion que no bloquea nuevas emisiones, duplicados no
idempotentes o una fuente live que exige evadir controles.

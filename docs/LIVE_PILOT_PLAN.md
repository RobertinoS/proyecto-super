# Plan de piloto Vea ONLINE supervisado

## Regla base

`SOURCE_MODE=live` solo se habilita temporalmente en staging por un
`dataset_admin` durante una ventana manual. Se restaura a `fixture` al terminar.
No se usa pytest, schedule ni scraping paralelo. `dry_run=true`,
`ENABLE_PUBLICATION=false`, `ENABLE_CLOUD_PUBLICATION=false` y
`ENABLE_PRIVATE_PUBLICATION=false` permanecen obligatorios en Etapa 1.

## Ventana y limites

- Maximo 30 minutos por ventana, una ventana por dia.
- Maximo una pagina y tres productos durante las primeras cinco corridas.
- Luego de cinco exitos consecutivos, maximo cinco productos y una pagina.
- Timeout configurado, delay activo y reintentos limitados; no reintentar ante
  CAPTCHA, login, 403 o 429.
- Al finalizar: restaurar `SOURCE_MODE=fixture` y confirmar kill switch `false`.

## Criterios de estabilidad

Antes de avanzar se requieren cinco corridas exitosas en al menos tres dias,
sin duplicados, con 100% de campos esenciales presentes, cero precios invalidos
y calidad al menos 95. La estructura debe conservar producto, marca si existe,
precio, URL, timestamp y canal `ONLINE`. Cualquier dataset requiere revision
humana antes de aprobacion.

## Regla de corte

Detener la ventana inmediatamente ante CAPTCHA, login, 403, dos 5xx
consecutivos, 429, cero productos no esperado, caida mayor a 30% contra la
mediana reciente, cambio de estructura, precio fuera de rango, duplicado no
idempotente o ausencia de trazabilidad. Registrar alerta y conservar fixture;
nunca evadir controles, cambiar User-Agent agresivamente ni usar proxies.

## Activacion gradual

| Etapa | Entrada y limite | Monitoreo/rol | Salida y rollback |
|---|---|---|---|
| 0. Fixture | Estado actual; todos los gates en false | `dataset_admin`; salud y alertas | Base segura |
| 1. Live manual bloqueado | Una pagina, 3-5 productos, dry run | `operator` + reviewer | 5 exitos/3 dias; volver fixture |
| 2. Dataset privado aprobado | Live manual, aprobacion y escritura privada solo en ventana aprobada | Dos responsables | Auditoria/acceso correctos; revoke o fixture |
| 3. workflow_dispatch | Solo disparo manual, una ejecucion autorizada | GitHub+n8n+FastAPI observados | 10 exitos/5 dias; kill switch false |
| 4. Schedule limitado | Una ventana semanal fijada, sin live fuera de horario | Alertas y responsable on-call | 4 semanas estables; desactivar schedule |
| 5. Operacion estable | Frecuencia aprobada y runbook probado | Revision continua | Cualquier alerta critica vuelve a Etapa 0/1 |

No se habilita Etapa 2 sin una aprobacion adicional explicita que autorice
escritura privada; no se habilita Etapa 4 sin aprobacion de seguridad y una
prueba de rollback registrada.

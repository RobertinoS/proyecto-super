# Plan de despliegue staging - Sprint 15

Actualizado: 2026-07-13.

## Objetivo

Validar el circuito GitHub Actions -> n8n -> FastAPI -> Supabase en un entorno
staging aislado, con fixture, trazabilidad durable y publicacion bloqueada. El
despliegue no se considera completo mientras dependa de memoria o archivos de
Render, use el Supabase operativo de n8n o carezca de evidencia E2E.

## Estado inicial

- `main` limpio en `v1.6.0` y rama `sprint-15-controlled-staging-deployment`.
- FastAPI, adaptador Vea, fixture, Dockerfile y Blueprint Render disponibles.
- Workflow n8n importable e inactivo.
- GitHub Actions diario/manual versionado, aun sin kill switch de repositorio.
- Migracion `001` propuesta y nunca ejecutada.
- `SOURCE_MODE=fixture` y `ENABLE_PUBLICATION=false`.
- 74 pruebas aprobadas en el cierre de Sprint 14.

## Componentes existentes

| Componente | Estado inicial | Decision Sprint 15 |
|---|---|---|
| FastAPI | local, estado de jobs en memoria | persistencia e idempotencia durable en staging |
| Vea ONLINE | fixture y live limitado | fixture primero; live manual posterior |
| n8n | externo existente; JSON inactivo | importar sin reemplazar workflows ni activar schedule |
| GitHub Actions | workflow unico | agregar kill switch y mantener trigger manual |
| Supabase | instancia externa de n8n declarada | no tocar; usar proyecto staging separado |
| UptimeRobot | monitor externo declarado para n8n | auditar por checklist; no crear monitor FastAPI |
| Publicacion | desactivada | mantener bloqueada durante todo el sprint |

## Componentes externos pendientes

1. Proyecto Supabase separado `proyecto-super-staging`.
2. Web Service Render `Proyecto Super FastAPI Staging`.
3. Importacion desactivada del workflow en el n8n existente.
4. Variables de Render/n8n y Secrets/Variables de GitHub.
5. Verificacion manual del monitor UptimeRobot de n8n.

Ningun valor secreto se registra en este documento ni en evidencia versionada.

## Orden de despliegue

1. Auditar repo, migraciones, JSON/YAML y ausencia de secretos.
2. Crear el proyecto Supabase staging separado y verificar que no contiene
   tablas internas de n8n.
3. Ejecutar `001` y luego `002` solo en ese proyecto; crear buckets privados.
4. Desplegar FastAPI con fixture, limites bajos y publicacion desactivada.
5. Validar health, autenticacion, fixture, proceso y gate de publicacion.
6. Importar n8n desactivado, configurar variables y probarlo manualmente.
7. Configurar GitHub con kill switch en `false`; habilitarlo solo durante la
   prueba manual controlada y volverlo a `false` al terminar.
8. Ejecutar E2E fixture e idempotencia; registrar evidencia no sensible.
9. Ejecutar un live minimo solo si la fuente responde sin protecciones.
10. Restaurar fixture, mantener publicacion bloqueada y auditar el sprint.

## Puntos de control

- C0: Git limpio y `v1.6.0` confirmado.
- C1: Supabase staging separado y sin tablas n8n.
- C2: migraciones estaticamente validas y backup/rollback documentado.
- C3: FastAPI `status=ok`, autenticacion 401/403/200 y fixture persistido.
- C4: n8n inactivo, warm-up controlado y mismo `execution_id` en reintentos.
- C5: GitHub manual exitoso con schedule efectivamente bloqueado.
- C6: repeticion idempotente con cero duplicados.
- C7: publicacion y buckets publicos inexistentes.

## Rollback

- GitHub: `PROJECT_SUPER_AUTOMATION_ENABLED=false`.
- n8n: desactivar el workflow importado.
- FastAPI: `SOURCE_MODE=fixture`, `ENABLE_PUBLICATION=false` y rollback al
  deploy anterior desde Render.
- Supabase: detener escrituras, conservar evidencia y revertir solo objetos
  exclusivos del proyecto staging mediante un procedimiento revisado. No se
  borran tablas como parte de una ejecucion automatica.
- Secretos: rotar en la plataforma correspondiente sin escribirlos en Git.

## Riesgos

- Arranque en frio de Render y timeout insuficiente.
- Supabase compartido accidentalmente con n8n.
- Duplicados por reintentos entre instancias.
- Activacion prematura del schedule o de publicacion.
- Cambio o bloqueo de la fuente Vea.
- Falta de acceso autenticado a plataformas externas desde esta sesion.

## Regla de corte

Se detiene toda accion externa ante credenciales en el repo, falta de
aislamiento, operaciones SQL destructivas, publicacion habilitada, live
automatico, duplicados no controlados, protecciones anti-bot o imposibilidad de
distinguir staging de produccion. El bloqueo y la accion minima se documentan;
no se improvisan excepciones.

## Criterios de aceptacion

- Supabase staging aislado y migraciones aplicadas sin afectar n8n.
- FastAPI desplegada en fixture y persistencia durable verificada.
- n8n importado inactivo, warm-up e idempotencia comprobados.
- GitHub Actions manual exitoso y schedule gobernado por kill switch.
- E2E fixture e idempotencia con evidencia en Supabase.
- Live minimo opcional en dry run, seguido de restauracion a fixture.
- Publicacion desactivada, buckets privados, pruebas aprobadas y cero secretos.

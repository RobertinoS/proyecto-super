# Auditoria de cierre - v2.0.0 piloto interno

Fecha de auditoria: 2026-07-21.

## Estado real

- Base auditada: `main` limpio con tag `v1.9.0`.
- Migraciones versionadas: `001` a `005`.
- El repositorio contiene FastAPI, el dashboard local, archivos de muestra y
  las rutas internas protegidas por `X-API-Key`.
- GitHub Actions conserva el kill switch
  `PROJECT_SUPER_AUTOMATION_ENABLED=false`.
- La documentacion de staging confirma bucket privado, fixture como modo final
  y publicacion publica bloqueada.

## Flujo principal a liberar

1. Ejecutar una extraccion Vea limitada y manual.
2. Procesar y validar en FastAPI.
3. Revisar y aprobar el dataset.
4. Publicar en el bucket privado.
5. Solicitar una URL firmada temporal y descargar el CSV.
6. Cargar el CSV en el dashboard y comparar una lista de compra.
7. Restaurar todos los flags seguros.

## Bloqueantes resueltos en las dos rondas permitidas

### B-01 - estado incompatible entre publicacion y acceso interno - RESUELTO

`PrivatePublicationService` genera el estado `PRIVATE_PUBLISHED` cuando una
publicacion privada efectiva esta habilitada. En cambio,
`InternalDatasetAccessService` acepta solamente `PUBLISHED_PRIVATE` o `ACTIVE`
para emitir una URL temporal. El flujo versionado no contiene una transicion
entre esos estados.

Impacto: sin una correccion o una transicion trazable, una publicacion real no
puede encadenarse de forma reproducible con la solicitud de URL firmada. Esto
impide completar el flujo principal sin una intervencion externa no documentada.

Ronda 1: la publicacion privada efectiva ahora registra
`PUBLISHED_PRIVATE`, estado que consume el acceso interno. La regresion cubre
la publicacion efectiva simulada, el estado elegible, el CSV y el manifiesto.

### B-02 - CSV privado sin grupo de comparacion - RESUELTO

El CSV de la canalizacion cloud conserva el contrato base de precios, pero no
incluye necesariamente `grupo_comparacion`. Sin ese campo el dashboard no
ofrecia productos en el armado de lista.

Ronda 2: el dashboard usa el nombre exacto de `producto` como grupo de
comparacion cuando el campo es opcional y falta. La regresion cubre carga,
busqueda, agregado y ranking. No se agregaron pantallas, endpoints,
migraciones ni automatizaciones.

## No bloqueantes

- `AGENTS.md` conserva rutas operativas historicas que no corresponden al
  flujo cloud actual. La guia de piloto sera la referencia para el operador.
- La autenticacion humana Supabase Auth/JWT sigue experimental y pendiente de
  validacion externa. No es necesaria para el piloto backend-only.
- La disponibilidad de Vea live puede variar por cambios o restricciones de la
  fuente. El piloto debe detenerse ante CAPTCHA, 403, 429 o estructura no
  reconocida y volver a fixture.

## Mejoras diferidas

Se registraran en `BACKLOG_V2.md`: login multiusuario, administracion de
roles, recuperacion de contrasena, interfaz administrativa, revocacion y
restauracion, schedule, publicacion publica, nuevas cadenas, scraping masivo,
movil, notificaciones y optimizaciones.

## Decision

**NO-GO temporal por evidencia externa pendiente.** Los dos bloqueantes locales
fueron resueltos dentro de las dos rondas autorizadas. Falta ejecutar el flujo
fixture y la corrida Vea live limitada sobre el commit desplegable de cierre,
y completar la UAT de un operador interno siguiendo la guia. No se autoriza
ningun desarrollo adicional: las mejoras van a `BACKLOG_V2.md`.

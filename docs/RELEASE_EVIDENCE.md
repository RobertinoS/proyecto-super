# Evidencia de cierre v2.0.0-rc1

Fecha: 2026-07-21. Esta evidencia no contiene claves, URLs temporales,
identificadores externos sensibles ni datos reales.

## Validacion local de cierre

- `python -m compileall scripts cloud_backend`: correcto.
- `python scripts/13_validate_supabase_migrations.py`: migraciones 001 a 005,
  12 tablas esperadas y 3 buckets esperados; correcto.
- `python scripts/14_validate_staging_idempotency.py`: fixture de tres
  productos, ejecucion duplicada detectada, proceso listo para aprobacion y
  publicacion sin aprobacion bloqueada; correcto.
- `python scripts/08_generar_mvp_demo.py`: 32 precios de demo, 7 comercios y
  12 recomendaciones de ruta; correcto.
- `python -m pytest`: 130 pruebas aprobadas y una advertencia externa de
  deprecacion de Starlette/TestClient.
- La canalizacion fixture produjo tres observaciones Vea y el CSV privado
  generado por el servicio mantuvo las columnas que requiere el dashboard:
  comercio, sucursal, localidad, producto, marca, categoria, presentacion,
  precio, fecha_relevamiento y fuente.
- La publicacion privada efectiva simulada registra `PUBLISHED_PRIVATE`, que
  es elegible para el acceso interno. La prueba tambien confirma dos
  artefactos privados esperados: CSV y manifiesto.
- El dashboard cargo el CSV de canalizacion con tres precios, permitio buscar
  Yerba, crear una lista con unidad `un` y calculo un ranking con cobertura
  100 por ciento. La consola del navegador no registro errores.
- La regresion automatizada cubre la compatibilidad de columnas y el fallback
  de grupo de comparacion por nombre exacto cuando el CSV cloud no trae ese
  campo.

## Seguridad e idempotencia

- Los validadores locales confirman las migraciones 001 a 005 y la prueba de
  idempotencia fixture conserva una sola ejecucion logica.
- La evidencia staging previa valida acceso sin clave rechazado, auditoria
  idempotente por `request_id`, bucket privado y expiracion aproximada de cinco
  minutos de una URL firmada. No se conserva la URL completa en auditoria.
- Los flags operativos deben permanecer apagados al finalizar cada prueba.

## Pendiente de release candidate

- Repetir en staging, sobre un commit desplegable de `release-v2-pilot`, el
  flujo fixture completo y una corrida Vea live limitada conforme a
  `docs/PILOT_USER_GUIDE.md`.
- Registrar solo conteos, checksum, estados y resultado de expiracion.
- Completar una prueba de usuario interno siguiendo la guia sin asistencia
  tecnica. No crear el tag final hasta que ambas evidencias esten aprobadas.

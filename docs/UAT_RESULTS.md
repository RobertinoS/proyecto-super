# Resultados UAT del piloto interno

Fecha: 2026-07-21.

## Prueba local simulada

Tiempo total: no medido. La medicion corresponde a la UAT externa desde cero;
no se debe inventar un tiempo de operador.

| Escenario | Resultado | Evidencia |
| --- | --- | --- |
| CSV privado de fixture | Aprobado | Tres precios cargados en dashboard. |
| Busqueda y lista | Aprobado | Producto encontrado, agregado y ranking calculado. |
| Compatibilidad de columnas | Aprobado | Contrato base de precios conservado. |
| Lista vacia | Aprobado | El dashboard mantiene las acciones de calculo bloqueadas. |
| Archivo incorrecto | Aprobado | El cargador informa que faltan columnas de precio. |
| Consola del navegador | Aprobado | Sin errores durante el flujo probado. |

## Hallazgos no bloqueantes

- Para un CSV cloud sin unidad comparable, el operador debe seleccionar `un`
  al armar la lista. La guia incorpora este paso.
- Con datos de una unica cadena no existe ahorro entre comercios. El ranking
  sigue siendo valido como costo y cobertura de esa cadena.

## UAT externo pendiente

Un operador interno debe seguir `docs/PILOT_USER_GUIDE.md` desde cero en
staging con su acceso seguro. Debe registrar tiempo total, pasos confusos,
resultado fixture, resultado live limitado, checksum, expiracion de acceso y
restauracion de flags. Solo un impedimento del flujo principal se corrige antes
del release; mejoras se registran en `BACKLOG_V2.md`.

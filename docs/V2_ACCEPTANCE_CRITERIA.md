# Criterios verificables para v2.0.0

## Obligatorio

- Consumidor interno autenticado con identidad individual y RBAC.
- Dataset `ACTIVE` privado, aprobado y accesible solo mediante FastAPI.
- Auditoria de acceso, aprobacion, activacion, revocacion y restore.
- Revocacion que bloquea nuevas emisiones de URL y restore de version previa
  mediante doble confirmacion.
- Cero secretos en repositorio, frontend, logs o workflows.
- Buckets privados, sin URLs permanentes ni publicacion publica.
- Observabilidad con alertas, historial de fuente y runbook probado.
- Piloto Vea live estable con limites, revision humana, idempotencia y rollback
  probado; GitHub/n8n solo avanzan segun las etapas aprobadas.
- Documentacion, pruebas automatizadas y evidencia staging actualizadas.

## Recomendable

- Pagina administrativa separada y protegida.
- Rate limit de accesos, retencion formal de logs y export de auditoria.
- Dashboard de compra consumiendo metadata del dataset activo.
- Prueba de restauracion de dataset y simulacro de incidente trimestral.

## Posterior a v2.0

- Publicacion publica y CDN.
- Notificaciones a usuarios finales.
- Automatizacion diaria de varias fuentes sin supervision humana por corrida.
- Aplicacion movil y analitica de consumo avanzada.

## Multicomercio futuro

Cada nuevo comercio requiere adaptador independiente, contrato de calidad,
piloto fixture/live, limites propios, aprobacion y rollback. No se habilita una
nueva fuente por compartir categoria o tecnologia con Vea.

## Evidencia de release

v2.0.0 solo puede etiquetarse con una matriz que pruebe los puntos obligatorios,
resultados de staging sin datos sensibles, pruebas locales completas, version
desplegada identificable y confirmacion de rollback a la version anterior.

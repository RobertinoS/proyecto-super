# Roadmap por sprints

## Sprint 0 - Gobernanza y orden

Objetivo de negocio: dejar el proyecto controlado, auditable y listo para evolucionar sin romper lo construido.

Entregables:

- `AGENTS.md`.
- `ROADMAP.md`.
- `BACKLOG.md`.
- `DATA_CONTRACT.md`.
- `TEST_PLAN.md`.
- `docs/PROJECT_STATUS.md`.
- `docs/CHANGELOG.md`.
- `docs/ARCHITECTURE.md`.
- `docs/LEGACY_INVENTORY.md`.

Archivos involucrados: documentacion y `.gitignore`.

Pruebas minimas:

- `python -m pytest`.
- `python src/run_pipeline.py --export`.
- Verificacion HTTP local del dashboard.

Criterio de aceptacion: documentos creados, alcance respetado, pruebas ejecutadas y proximo sprint definido.

## Sprint 1 - Contrato de datos y calidad

Objetivo de negocio: confiar en que precio, producto, fuente y promocion significan lo mismo en todo el sistema.

Entregables:

- Validadores de contrato para JSON exportado.
- Reglas de precio sospechoso.
- Reporte de calidad por fuente.
- Tests de schema para export.

Archivos involucrados: `src/export_dashboard.py`, `src/database.py`, `tests/`, `docs/`.

Pruebas minimas:

- Tests unitarios de contrato.
- `python src/run_pipeline.py --export`.

Criterio de aceptacion: export falla de forma clara si rompe campos minimos o tipos esperados.

## Sprint 2 - Matching de productos, cantidades y equivalencias

Objetivo de negocio: comparar productos realmente equivalentes y evitar decisiones incorrectas.

Entregables:

- Diccionario de productos normalizados.
- Reglas de equivalencia por marca, presentacion, unidad y categoria.
- Manejo consistente de cantidades.
- Tests de matching.

Archivos involucrados: `src/normalize.py`, `src/search_engine.py`, `src/basket_optimizer.py`, `app/index.html`, `tests/`.

Pruebas minimas:

- Casos `yerba mate 1kg`, `cafe 750g`, `leche 1l`, `aceite 900ml`.

Criterio de aceptacion: no compara presentaciones incompatibles sin advertencia.

## Sprint 3 - Listas guardadas y experiencia de usuario

Objetivo de negocio: que el usuario pueda repetir compras frecuentes con poco esfuerzo.

Entregables:

- Mejoras de UX en listas guardadas.
- Validaciones visuales de cantidad.
- Estados vacios y errores.
- Persistencia local documentada.

Archivos involucrados: `app/index.html`, `docs/`, `tests` manuales.

Pruebas minimas:

- Crear, guardar, cargar, editar y borrar lista.
- Verificar en desktop y mobile.

Criterio de aceptacion: una lista frecuente se puede reutilizar sin recargar datos manualmente.

## Sprint 4 - Promociones, tarjetas y reglas comerciales

Objetivo de negocio: mostrar oportunidades de ahorro sin confundir promo general con promo condicional.

Entregables:

- Clasificacion de promociones.
- Separacion de tarjetas, bancos, cuotas y combos.
- Reglas de vigencia si la fuente las expone.
- Tests de clasificacion.

Archivos involucrados: `src/export_dashboard.py`, `app/promociones.html`, `DATA_CONTRACT.md`, `tests/`.

Pruebas minimas:

- Promos por sector.
- Promos por tarjeta.
- Catalogos oficiales.

Criterio de aceptacion: ninguna promo condicional aparece como precio final sin etiqueta.

## Sprint 5 - Ruta de compra, ahorro y distancia

Objetivo de negocio: transformar precios en una recomendacion accionable de compra.

Entregables:

- `config/locales_san_juan.yml`.
- Coordenadas y sucursales oficiales.
- Distancia estimada entre tiendas.
- Costo/beneficio de dividir compra.

Archivos involucrados: `src/basket_optimizer.py`, `app/index.html`, `config/`, `tests/`.

Pruebas minimas:

- Lista de 5 productos con ruta sugerida.
- Comparacion contra mejor cadena unica.

Criterio de aceptacion: la ruta explica ahorro, tiendas usadas y productos no encontrados.

## Sprint 6 - Automatizacion y monitoreo

Objetivo de negocio: actualizar datos sin intervencion y detectar fallas temprano.

Entregables:

- Logs estructurados.
- Auditoria de runs.
- Alerta local o reporte de errores.
- Tarea programada documentada.

Archivos involucrados: `src/run_pipeline.py`, `scripts/`, `run_update.bat`, `docs/`.

Pruebas minimas:

- Ejecutar tarea manual.
- Simular scraper fallido.

Criterio de aceptacion: una falla de fuente no rompe todo el pipeline y queda registrada.

## Sprint 7 - Mejora visual avanzada

Objetivo de negocio: que el dashboard sea convincente, profesional y usable para clientes.

Entregables:

- Refinamiento BI/SaaS.
- Graficos mas utiles para decision.
- Responsive audit.
- Estados de carga y errores.

Archivos involucrados: `app/index.html`, `app/promociones.html`, `docs/`.

Pruebas minimas:

- Desktop y mobile.
- Busqueda, filtros, listas, promociones.

Criterio de aceptacion: la experiencia comunica ahorro, confianza y accion clara.

## Sprint 8 - Limpieza legacy y empaquetado final

Objetivo de negocio: dejar una version entregable y mantenible.

Entregables:

- Limpieza aprobada de raw/legacy/cache.
- README final.
- Paquete local reproducible.
- Checklist de entrega.

Archivos involucrados: todos los inventariados, con aprobacion previa.

Pruebas minimas:

- Setup desde cero.
- Pipeline.
- Dashboard.

Criterio de aceptacion: proyecto portable, documentado y sin basura tecnica innecesaria.

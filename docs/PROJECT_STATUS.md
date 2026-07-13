# Estado del proyecto

Actualizado: 2026-07-13.

## Sprint actual

Sprint 14 - Piloto cloud de scraping oficial.

Estado: funcionalmente completo. Base cloud lista para despliegue controlado en Sprint 15; sin despliegue ni migraciones ejecutadas y con publicacion real desactivada.

Rama:

```text
sprint-14-cloud-scraping-pilot
```

Objetivo: dejar una base cloud desplegable, segura e idempotente para una fuente oficial piloto sin depender de la PC local.

## Diagnostico ejecutivo

El repo Git dedicado esta en:

```text
C:\Users\Rober\Desktop\Proyecto Super
```

Sprint 1 a Sprint 13 se mantienen compatibles y la rama parte de `main` con tag `v1.5.0`. Sprint 14 agrega `cloud_backend/` como capa aislada; no modifica la logica del dashboard. La fuente piloto Vea usa fixture por defecto, limites estrictos y canal `ONLINE`. La publicacion real, el despliegue Render y la migracion Supabase quedan desactivados hasta revision manual.

## Artefactos Sprint 14

- FastAPI en `cloud_backend/` con health, fuentes, jobs y pipeline.
- Adaptador Vea con fixture reproducible, limites, timeout, delay y reintentos.
- `render.yaml`, Dockerfile y `.env.example` sin secretos reales.
- SQL revisable en `supabase/migrations/001_cloud_scraping_foundation.sql`.
- Workflow n8n importable y GitHub Action diario unico.
- Auditorias y guias cloud en `docs/`.
- Smoke test `scripts/12_smoke_test_fuente_piloto.py`.

## Decisiones Sprint 14

- UptimeRobot solo mantiene/supervisa n8n; FastAPI duerme y n8n la precalienta.
- GitHub Actions ejecuta una vez al dia y no actua como keepalive.
- `execution_id` y `raw_hash` controlan idempotencia.
- `/health` y `/sources` son publicos; jobs/pipeline requieren `X-API-Key`.
- Vea se selecciona por JSON publico y presencia oficial San Juan, pero se etiqueta ONLINE.
- `SOURCE_MODE=fixture` y `ENABLE_PUBLICATION=false` son defaults seguros.

## Validaciones Sprint 14

- `python -m compileall scripts cloud_backend`: OK.
- Smoke fixture: 3 productos, 0 incidencias, dry run, sin publicacion.
- Smoke live controlado: 1 producto, 1 pagina, dry run, sin persistencia/publicacion.
- FastAPI local: `/health`, `/sources`, scrape, job, process y publish dry run OK; falta de API key devuelve 401.
- `/docs`: HTTP 200 en `http://127.0.0.1:8014/docs`.
- Flujo MVP `scripts/08_generar_mvp_demo.py`: OK, 32 precios y 12 recomendaciones de ruta.
- `python -m pytest`: 74 passed; las 51 pruebas previas continúan aprobadas.
- JSON n8n, YAML Render/GitHub y SQL: parseo/contratos automaticos OK.
- Docker no se construyo localmente porque Docker CLI no esta instalado; queda pendiente validar imagen en CI/Render.

## Cierre funcional Sprint 14

- Release objetivo: `v1.6.0`.
- Base cloud reproducible y auditada localmente.
- Despliegue externo pendiente para Sprint 15.
- Migracion Supabase propuesta y no ejecutada.
- Workflow n8n importable e inactivo.
- GitHub Actions versionado, todavia sin secretos externos configurados.
- Publicacion real bloqueada por `ENABLE_PUBLICATION=false` y aprobacion explicita.

## Artefactos Sprint 13

- `design_reference/site_model/`: dos capturas y HTML de referencia aportados por el usuario.
- `docs/UI_INTEGRATION_PLAN.md`.
- `docs/UI_COMPONENT_MAPPING.md`.
- `dashboard/index.html`: interfaz Site integrada y unica entrada oficial.
- `tests/test_dashboard_site_integration.py`.

## Decision tecnica Sprint 13

- El dashboard v1.4.0 fue la fuente de verdad funcional.
- Se conservaron el JavaScript embebido, los contratos CSV y todos los IDs funcionales.
- Se cambio la capa visual a fondo claro, sidebar verde profundo, acento lima, cards blancas y tablas ligeras.
- Se agregaron resumen ejecutivo, loader, feedback, acciones deshabilitadas, etiquetas accesibles y confirmacion de limpieza.
- No se separo JavaScript en modulos para evitar una refactorizacion simultanea al rediseno.
- La version anterior se conserva mediante Git; no se crearon copias legacy.
- La candidata temporal `dashboard/v2/index.html` se elimino al confirmar que tenia el mismo hash que la version promovida.

## Validaciones Sprint 13

- Pruebas frontend focalizadas: 5 passed.
- `python -m compileall scripts`: OK.
- `python scripts/08_generar_mvp_demo.py`: OK.
- Consolidacion y matching: 12 filas y 6 grupos.
- Archivos demo: 32 precios, 7 comercios, 5 items y 12 recomendaciones de ruta.
- Calidad: 4 grupos leidos por la interfaz.
- `python -m pytest`: 51 passed.
- HTTP local: dashboard oficial promovido respondio correctamente.
- Desktop 1440x1000 y mobile 390x844: sin desborde horizontal ni controles fuera de pantalla.
- Consola del navegador: sin errores.

## Artefactos Sprint 12

- `data/sample/multifile/`
- `data/raw/precios_reales/manual/.gitkeep`
- `scripts/11_consolidar_relevamientos.py`
- `tests/test_multifile_consolidation.py`
- integracion compatible en `scripts/10_generar_reporte_calidad_datos.py`
- actualizaciones en README y documentacion operativa/tecnica.

## Decision tecnica Sprint 12

- Los CSV se descubren recursivamente y se procesan por ruta relativa en orden lexicografico.
- Cada archivo reutiliza `scripts/09_validar_precios_reales.py`; las filas fatales no ingresan al consolidado.
- Los duplicados internos se excluyen. Entre archivos gana el ultimo registro procesado y queda marcado como conflicto.
- El consolidado conserva archivo de origen y fecha de procesamiento.
- El manifiesto resume cada corrida; todos los outputs permanecen ignorados por Git.
- `scripts/10_generar_reporte_calidad_datos.py` mantiene el reporte Sprint 10 y suma soporte al reporte de consolidacion.

## Validaciones Sprint 12

- `python -m compileall scripts`: OK.
- Consolidacion sample: 5 archivos, 15 filas leidas, 12 consolidadas y 1 conflicto entre archivos.
- Matching: 12 filas, 6 grupos y confianza promedio `0.8792`.
- Calidad desde consolidacion: 4 comercio/sucursal evaluados.
- Lista demo: ranking de 2 comercios; Vea resulta primero con `$7100.00` y 60% de cobertura.
- `python scripts/08_generar_mvp_demo.py`: OK, flujo v1.3.0 compatible.
- `python -m pytest`: 48 passed.
- Dashboard por HTTP: OK, estructura visible y consola sin errores.
- Validacion funcional del CSV consolidado: 12 filas, una sola Yerba Vea Centro y precio ganador `$3150.00`.

## Artefactos Sprint 11

- `docs/OPERACION_DIARIA_PRECIOS.md`
- `docs/NAMING_CONVENTION.md`
- `scripts/10_generar_reporte_calidad_datos.py`
- `tests/test_data_quality_operations.py`
- `dashboard/index.html`
- `scripts/09_validar_precios_reales.py`
- `README.md`
- `docs/GUIA_USO_MVP.md`
- `docs/GUIA_CARGA_PRECIOS_REALES.md`
- `docs/DATA_CONTRACT.md`
- `docs/TEST_PLAN.md`
- `docs/DATA_RETENTION_POLICY.md`
- `docs/CHANGELOG.md`

## Decision tecnica Sprint 11

- `data/raw/precios_reales/manual/{comercio}/{sucursal}/{YYYY-MM-DD}/` queda como estructura documentada no versionable.
- El reporte de validacion conserva columnas requeridas y suma contexto `comercio`, `sucursal`, `localidad`.
- `precios_reales_validados.csv` suma `fila_origen` para trazabilidad sin romper matching ni dashboard.
- Los estados se calculan con prioridad: `INVALIDO`, `DESACTUALIZADO`, `REVISAR`, `OK`.
- `score_calidad` parte de 100 y penaliza errores fatales, duplicados, precios sospechosos y antiguedad.
- El dashboard agrega un panel simple de calidad sin redisenar la UI.

## Validaciones Sprint 11

- `python -m compileall scripts`: OK.
- `python scripts/09_validar_precios_reales.py --input data/sample/precios_reales_demo.csv`: OK, 24 filas validas y 5 incidencias.
- `python scripts/10_generar_reporte_calidad_datos.py`: OK, 12 comercio/sucursal evaluados.
- `python scripts/08_generar_mvp_demo.py`: OK, flujo v1.2.0 compatible.
- `python -m pytest`: 42 passed.
- Dashboard por HTTP local: OK, `dashboard/`, `resumen_calidad_fuente.csv` y `reporte_calidad_datos.csv` respondieron 200.
- Validacion JS del dashboard: OK, panel de calidad lee 12 filas de resumen y 12 de detalle.

## Artefactos Sprint 10

- `data/sample/precios_reales_template.csv`
- `data/sample/precios_reales_demo.csv`
- `docs/GUIA_CARGA_PRECIOS_REALES.md`
- `scripts/09_validar_precios_reales.py`
- `tests/test_real_data_validation.py`
- `dashboard/index.html`
- `README.md`
- `docs/GUIA_USO_MVP.md`
- `docs/DATA_CONTRACT.md`
- `docs/TEST_PLAN.md`
- `docs/DATA_RETENTION_POLICY.md`
- `docs/CHANGELOG.md`

## Decision tecnica Sprint 10

- La carga real se valida antes de entrar al flujo analitico.
- Las filas con errores fatales se excluyen de `precios_reales_validados.csv`.
- Los precios sospechosos se informan como alerta y se conservan para revision.
- `direccion` y `observacion` se preservan como trazabilidad, pero el contrato canonico de 10 columnas sigue intacto.
- El dashboard suma avisos livianos de calidad si el usuario carga un CSV crudo directo.
- No se modifica la logica principal de matching, promociones, lista ni ruta.

## Validaciones Sprint 10

- `python -m compileall scripts`: OK.
- `python scripts/09_validar_precios_reales.py --input data/sample/precios_reales_demo.csv`: OK, 24 filas validas y 5 incidencias controladas.
- `python scripts/04_matching_productos.py --input data/processed/precios_reales_validados.csv --output data/processed/precios_reales_matcheados.csv`: OK, 24 filas matcheadas y 19 grupos.
- `python scripts/06_aplicar_promociones.py --prices data/processed/precios_reales_matcheados.csv --output data/processed/precios_reales_con_promociones.csv --date 2026-07-11`: OK, 7 filas con promocion.
- `python scripts/05_calcular_lista_compra.py --prices data/processed/precios_reales_con_promociones.csv`: OK, ranking con `precio_efectivo`.
- `python scripts/08_generar_mvp_demo.py`: OK, flujo MVP demo compatible.
- `python -m pytest`: 39 passed.
- Dashboard por HTTP local: OK, `http://127.0.0.1:8026/dashboard/` respondio 200 y cargo precios reales matcheados/con promociones.

## Artefactos Sprint 9

- `dashboard/index.html`
- `README.md`
- `docs/GUIA_USO_MVP.md`
- `docs/PROJECT_STATUS.md`
- `docs/CHANGELOG.md`
- `docs/TEST_PLAN.md`

## Decision tecnica Sprint 9

- No se modifican scripts Python.
- Se conservan los ids y funciones JS usados por pruebas y flujo MVP.
- Se agrega navegacion lateral por secciones: Resumen, Precios, Lista de compra, Comparacion y Ruta/cercania.
- Se agregan estados visuales por archivo cargado.
- Se agrega accion global `Recalcular`.
- Se agrega accion global `Limpiar sesion`.
- Se mantiene funcionamiento sin backend y con archivos CSV locales.

## Resumen ejecutivo MVP v1.0

Funcionalidades terminadas:

- carga de CSV local en dashboard standalone;
- importacion manual de fuente tipo SEPA/sample;
- filtro San Juan;
- normalizacion y matching de productos equivalentes;
- precio unitario comparable;
- listas de compra desde CSV o UI;
- persistencia local con `localStorage`;
- exportacion de lista compatible con scripts;
- promociones y precio efectivo;
- ranking por comercio, ahorro y faltantes;
- compra dividida por producto;
- sucursales demo y ubicacion demo;
- score de conveniencia por precio + distancia;
- ruta dividida sugerida;
- script unico `scripts/08_generar_mvp_demo.py`.

## Flujo actual

```text
data/sample/sepa/sepa_precios_simulado.csv
        -> scripts/03_filtrar_san_juan.py
        -> data/processed/precios_san_juan_sepa.csv
        -> scripts/04_matching_productos.py
        -> data/processed/precios_matcheados.csv
        -> scripts/06_aplicar_promociones.py
        -> data/processed/precios_con_promociones.csv
        -> scripts/05_calcular_lista_compra.py
        -> data/processed/comparacion_lista_compra.csv
        -> data/processed/mejor_compra_por_producto.csv
        -> scripts/07_planificar_ruta.py
        -> data/processed/recomendacion_ruta.csv
        -> data/processed/ruta_compra_dividida.csv
        -> dashboard/index.html
```

Flujo recomendado para usuario MVP:

```bash
python scripts/08_generar_mvp_demo.py
python -m http.server 8026 --bind 127.0.0.1
```

Dashboard:

```text
http://127.0.0.1:8026/dashboard/
```

Archivos a cargar:

```text
data/processed/precios_con_promociones.csv
data/sample/lista_compra_demo.csv
data/sample/sucursales_demo.csv
data/sample/ubicacion_usuario_demo.csv
```

## Artefactos Sprint 8

- `scripts/08_generar_mvp_demo.py`
- `docs/GUIA_USO_MVP.md`
- `docs/RELEASE_CHECKLIST.md`
- `README.md`
- `dashboard/index.html`
- `docs/DATA_CONTRACT.md`
- `docs/TEST_PLAN.md`
- `docs/PROJECT_STATUS.md`
- `docs/CHANGELOG.md`
- `docs/DATA_RETENTION_POLICY.md`

## Artefactos Sprint 7

- `data/sample/sucursales_demo.csv`
- `data/sample/ubicacion_usuario_demo.csv`
- `scripts/07_planificar_ruta.py`
- `tests/test_route_planning.py`
- `dashboard/index.html`
- `tests/test_dashboard_shopping_list_ui.py`
- `README.md`
- `docs/DATA_CONTRACT.md`
- `docs/TEST_PLAN.md`
- `docs/PROJECT_STATUS.md`
- `docs/CHANGELOG.md`

## Decision tecnica

- La distancia se calcula con Haversine en linea recta.
- La distancia es aproximada y no reemplaza navegacion real.
- No se usa Google Maps API ni servicios externos.
- `score_conveniencia = costo_total_estimado + penalizacion_distancia`.
- `penalizacion_distancia = distancia_km * costo_km_estimado`.
- `costo_km_estimado` demo: `180` pesos por km.
- El ranking prioriza cobertura completa y luego menor score de conveniencia.
- La ruta dividida usa una heuristica simple de vecino mas cercano entre comercios recomendados.
- Si el usuario ingresa coordenadas manuales en el dashboard, esas coordenadas tienen prioridad sobre el CSV de ubicacion.

## Funcionalidades Sprint 7

- Archivo demo de sucursales por Capital, Rawson, Santa Lucia y Rivadavia.
- Archivo demo de ubicacion del usuario.
- Script local de planificacion de ruta.
- Generacion de `recomendacion_ruta.csv`.
- Generacion de `ruta_compra_dividida.csv`.
- Ranking por precio efectivo y cobertura.
- Ranking por conveniencia precio + distancia.
- Ruta dividida sugerida por comercio recomendado.
- Dashboard con carga de sucursales, ubicacion o coordenadas manuales.

## Validaciones actuales

Pruebas Sprint 9:

- `python scripts/08_generar_mvp_demo.py`: OK;
- `python -m pytest`: 33 passed;
- dashboard por HTTP local: OK, `http://127.0.0.1:8026/dashboard/` respondio 200;
- validacion visual: sidebar, header, flujo guiado, estados de archivo y botones globales presentes;
- validacion funcional JS con CSV reales: OK;
- consola del navegador: sin errores.

Pruebas release MVP:

- `python -m compileall scripts`: OK;
- `python scripts/08_generar_mvp_demo.py`: OK;
- `python -m pytest`: 33 passed;
- dashboard por HTTP local: OK, `http://127.0.0.1:8026/dashboard/` respondio 200;
- validacion funcional JS con CSV reales: OK.

Pruebas agregadas:

- `tests/test_route_planning.py`

Cobertura:

- lectura de sucursales;
- lectura de ubicacion usuario;
- calculo Haversine;
- generacion de `recomendacion_ruta.csv`;
- generacion de `ruta_compra_dividida.csv`;
- ranking por `score_conveniencia`;
- compatibilidad con outputs de Sprint 6;
- dashboard JS con ranking de conveniencia y ruta dividida.

Pruebas ejecutadas:

```bash
python -m py_compile scripts/07_planificar_ruta.py
python scripts/02_normalizar_precios.py
python scripts/01_descargar_o_importar_sepa.py --mode manual --input data/sample/sepa/sepa_precios_simulado.csv
python scripts/03_filtrar_san_juan.py --input data/raw/sepa/manual/sepa_precios_simulado.csv
python scripts/04_matching_productos.py
python scripts/06_aplicar_promociones.py --date 2026-07-11
python scripts/05_calcular_lista_compra.py --prices data/processed/precios_con_promociones.csv
python scripts/07_planificar_ruta.py
python -m pytest
```

Resultado:

- `python -m pytest`: `33 passed`.
- `scripts/07_planificar_ruta.py`: OK, 12 recomendaciones y 2 paradas de ruta dividida.
- Mejor recomendacion demo actual: `ChangoMas - Hiper San Juan`, score `8004.62`.
- Dashboard servido por HTTP local: OK, `dashboard/` HTTP 200.
- Validacion JS del dashboard: OK con `precios_con_promociones.csv`, `lista_compra_demo.csv`, `sucursales_demo.csv` y `ubicacion_usuario_demo.csv`.

## Riesgos y pendientes

- Los datos demo no son datos reales de compra.
- Las coordenadas demo son aproximadas.
- La distancia Haversine no modela calles, transito, horarios ni tiempos reales.
- El costo por km es demo y debe calibrarse con criterio operativo o de usuario.
- La disponibilidad por sucursal todavia se aproxima desde el comercio, no desde stock real por sucursal.
- Falta procedimiento operativo para fuentes reales por cadena.
- Falta selector avanzado de preferencias: distancia maxima, cantidad maxima de paradas, medio de pago y tolerancia a faltantes.

## Proximo sprint recomendado

Sprint 10 - Datos reales operativos y preferencias avanzadas.

Objetivo: incorporar fuentes reales/manuales verificadas, calibrar coordenadas/costo por km y permitir que el usuario configure prioridad entre ahorro, distancia, cantidad maxima de paradas, medios de pago y cobertura minima.

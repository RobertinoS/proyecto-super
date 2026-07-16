# Changelog

## v1.7.0 - Sprint 15 - Staging controlado

Sprint 15 cerrado con staging aislado y validacion E2E controlada. No habilita
publicacion real, modo live permanente ni automatizacion operativa:

- plan de despliegue, aislamiento Supabase, storage, variables, FastAPI,
  evidencia E2E, gate de publicacion y runbook de incidentes;
- decision obligatoria de usar `proyecto-super-staging` separado de n8n;
- migracion `002` no destructiva con hardening y buckets privados;
- validador estatico de migraciones que protege el hash de `001`;
- limites staging 5 productos/1 pagina, fixture y publicacion desactivada;
- kill switch GitHub y execution ID estable entre reintentos;
- n8n versionado inactivo con warm-up progresivo en tres intentos;
- run ID deterministico, recuperacion Supabase y upserts idempotentes;
- persistencia privada de trazabilidad en dry run y gate de publicacion intacto;
- validador de idempotencia local/remoto sin imprimir credenciales.

Validacion manual externa no sensible:

- FastAPI Render activa y Supabase staging aislado;
- n8n Test URL y Production URL correctas, con `Structured Success` y
  `rows_processed=3`;
- idempotencia confirmada sin duplicados y publicacion bloqueada;
- export n8n endurecido: normalizacion de `trigger_type`, payload limitado al
  contrato `/jobs/scrape` y salidas HTTP de scrape/proceso separadas hacia
  `Structured Error`.

Evidencia E2E de cierre, sin valores sensibles:

- GitHub `workflow_dispatch` llamo al webhook productivo de n8n y recibio 2xx;
- n8n completo warm-up, fixture, proceso y `Structured Success`;
- Supabase staging registro ejecucion, observaciones y eventos sin duplicados;
- la publicacion efectiva fue cero; los gates `ENABLE_PUBLICATION=false` y
  `ENABLE_CLOUD_PUBLICATION=false` siguen activos;
- Vea ONLINE se valido en live limitado, con `dry_run=true`, limites bajos y
  sin representar precios fisicos de sucursal;
- `SOURCE_MODE` fue restaurado a `fixture` y
  `PROJECT_SUPER_AUTOMATION_ENABLED` permanece en `false`.

GitHub Actions ahora registra de manera segura el 2xx y los campos no sensibles
`status`, `execution_id`, `run_id`, `rows_processed`, `publication` y
`duplicate_execution`, sin imprimir headers ni secretos.

Validacion local:

- compilacion, demo MVP, consolidacion y fixture: OK;
- migraciones: `001` intacta, 5 tablas y 3 buckets esperados;
- idempotencia: mismo run ID, proceso estable y publicacion `DRY_RUN`;
- FastAPI HTTP: health/docs, 401, 403, scrape, job, process y gates OK;
- n8n existente: `/healthz` HTTP 200, sin crear servicios nuevos;
- `python -m pytest`: 87 passed, 1 warning externo;
- fixture E2E y live limitado externos: validados sin publicacion.

## 2026-07-13 - Sprint 14 - Piloto cloud de scraping oficial

Completado para release local `v1.6.0`:

- auditoria de automatizacion, UptimeRobot y cuatro fuentes oficiales;
- seleccion de Vea como piloto condicionado, con canal ONLINE explicito;
- FastAPI desplegable con autenticacion, idempotencia y gates de calidad/publicacion;
- fixture reproducible y smoke test limitado;
- propuesta SQL Supabase y buckets privados;
- Docker/Render con arranque en frio y filesystem efimero documentados;
- workflow n8n importable sin credenciales y GitHub Action diario unico;
- publicacion real, migracion y despliegue desactivados hasta revision.

Pruebas:

- compilacion de `scripts` y `cloud_backend`: OK;
- smoke fixture: 3 productos, dry run;
- smoke live: 1 producto, 1 pagina, dry run;
- FastAPI local y OpenAPI: OK;
- flujo MVP v1.5.0: OK;
- `python -m pytest`: 74 passed, 1 warning de deprecacion externo de FastAPI TestClient.
- Docker build pendiente por ausencia de Docker CLI local.
- auditoria final sin secretos reales, datos crudos, outputs, logs ni archivos `.env` reales versionados;
- JSON n8n, YAML GitHub/Render, `.env.example` y SQL propuesto validados estaticamente;
- despliegue, activacion n8n, migracion Supabase y publicacion real diferidos a Sprint 15.

## 2026-07-13 - Sprint 13 - Integracion funcional del modelo visual Site

Cambios:

- Se inventariaron dos capturas y el HTML de `design_reference/site_model/`.
- Se crearon `docs/UI_INTEGRATION_PLAN.md` y `docs/UI_COMPONENT_MAPPING.md` antes de implementar.
- Se creo `dashboard/v2/index.html` como candidata aislada.
- Se aplico la direccion Site: tema claro, sidebar verde, acento lima, cards blancas, barras y tablas ligeras.
- Se conservaron IDs, contratos CSV, validaciones y logica completa de v1.4.0.
- Se agregaron resumen ejecutivo, loader de archivos, feedback, acciones deshabilitadas y confirmacion al limpiar.
- Se mejoraron etiquetas, foco de teclado, contraste y responsive.
- Tras validar paridad, se promovio la candidata a `dashboard/index.html` sin crear una copia legacy.
- Se elimino `dashboard/v2/` al confirmar igualdad de hash; Git conserva el historial de la candidata.
- Se agregaron pruebas en `tests/test_dashboard_site_integration.py`.

Pruebas:

- `python -m compileall scripts`: OK.
- Flujo demo y consolidacion multiarchivo: OK.
- Datos demo, promociones, lista, calidad y ruta leidos por el JavaScript real: OK.
- `python -m pytest`: 51 passed.
- Desktop 1440x1000 y mobile 390x844: sin desborde horizontal.
- Consola del navegador: sin errores.

## 2026-07-12 - Sprint 12 - Consolidacion multiarchivo diaria

Cambios:

- Se agrego `data/sample/multifile/` con cinco CSV, cuatro sucursales, dos fechas e incidencias controladas.
- Se creo `scripts/11_consolidar_relevamientos.py` para descubrimiento recursivo, validacion individual y consolidacion trazable.
- Se definio una regla determinista: ante duplicados entre archivos, gana el ultimo archivo en orden lexicografico de ruta relativa.
- Se generan `precios_reales_consolidados.csv`, `reporte_consolidacion.csv` y `manifiesto_consolidacion.csv`.
- Se amplio `scripts/10_generar_reporte_calidad_datos.py` para aceptar el reporte de consolidacion sin romper el formato Sprint 10.
- Se agregaron pruebas en `tests/test_multifile_consolidation.py`.
- Se versiona solo `.gitkeep` de la estructura raw; los CSV reales siguen ignorados.
- Se actualizaron README, operacion diaria, convencion de nombres, guia de carga, contrato, pruebas, estado y retencion.
- Se documento la secuencia auditable `01_`, `02_`, `03_` para cargas y correcciones sucesivas.

Pruebas:

- `python -m compileall scripts`: OK.
- Consolidador sample: 5 archivos, 15 filas y 12 registros unicos.
- Matching consolidado: 12 filas y 6 grupos.
- Calidad consolidada: 4 comercio/sucursal evaluados.
- Ranking lista demo: 2 comercios, sin duplicar la correccion de Vea Centro.
- `python scripts/08_generar_mvp_demo.py`: OK.
- `python -m pytest`: 48 passed.
- Dashboard por HTTP: OK, consola sin errores y funciones reales validadas con el CSV consolidado.

## 2026-07-12 - Sprint 11 - Flujo operativo diario y calidad de datos

Cambios:

- Se creo `docs/OPERACION_DIARIA_PRECIOS.md` con flujo diario/semanal.
- Se creo `docs/NAMING_CONVENTION.md` con convencion de nombres para archivos reales.
- Se agrego `scripts/10_generar_reporte_calidad_datos.py`.
- Se generan `data/processed/reporte_calidad_datos.csv` y `data/processed/resumen_calidad_fuente.csv`.
- Se agregaron estados `OK`, `REVISAR`, `INVALIDO`, `DESACTUALIZADO`.
- Se agrego `score_calidad`.
- Se mejoro `scripts/09_validar_precios_reales.py` con `fila_origen` y contexto de incidencia.
- Se agrego panel `Calidad` en `dashboard/index.html`.
- Se agregaron pruebas `tests/test_data_quality_operations.py`.
- Se actualizaron README, guia de uso, guia de carga real, contrato de datos, plan de pruebas, estado y politica de retencion.

Archivos creados:

- `docs/OPERACION_DIARIA_PRECIOS.md`
- `docs/NAMING_CONVENTION.md`
- `scripts/10_generar_reporte_calidad_datos.py`
- `tests/test_data_quality_operations.py`

Archivos modificados:

- `dashboard/index.html`
- `scripts/09_validar_precios_reales.py`
- `tests/test_dashboard_shopping_list_ui.py`
- `README.md`
- `docs/GUIA_USO_MVP.md`
- `docs/GUIA_CARGA_PRECIOS_REALES.md`
- `docs/DATA_CONTRACT.md`
- `docs/TEST_PLAN.md`
- `docs/PROJECT_STATUS.md`
- `docs/DATA_RETENTION_POLICY.md`
- `docs/CHANGELOG.md`

Pruebas ejecutadas:

- `python -m compileall scripts`: OK.
- `python scripts/09_validar_precios_reales.py --input data/sample/precios_reales_demo.csv`: OK.
- `python scripts/10_generar_reporte_calidad_datos.py`: OK, genero reportes de calidad.
- `python scripts/08_generar_mvp_demo.py`: OK, flujo v1.2.0 compatible.
- `python -m pytest`: 42 passed.
- Dashboard por HTTP local: OK, carga resumen/detalle de calidad y mantiene flujo MVP.

## 2026-07-12 - Sprint 10 - Operacion real controlada

Cambios:

- Se creo `data/sample/precios_reales_template.csv` como plantilla versionable para carga manual.
- Se creo `data/sample/precios_reales_demo.csv` con mas de 20 productos y errores controlados.
- Se agrego `scripts/09_validar_precios_reales.py` para validar columnas, precios, fechas, localidades, comercio/sucursal, duplicados y precios sospechosos.
- Se generan `data/processed/precios_reales_validados.csv` y `data/processed/reporte_validacion_precios_reales.csv`.
- Se creo `docs/GUIA_CARGA_PRECIOS_REALES.md`.
- Se agregaron pruebas automatizadas en `tests/test_real_data_validation.py`.
- Se mejoro `dashboard/index.html` con avisos de calidad para cargas reales crudas.
- Se amplio la prueba JS del dashboard para cubrir avisos de calidad.
- Se actualizaron README, guia de uso, contrato de datos, plan de pruebas, estado y politica de retencion.

Archivos creados:

- `data/sample/precios_reales_template.csv`
- `data/sample/precios_reales_demo.csv`
- `docs/GUIA_CARGA_PRECIOS_REALES.md`
- `scripts/09_validar_precios_reales.py`
- `tests/test_real_data_validation.py`

Archivos modificados:

- `dashboard/index.html`
- `tests/test_dashboard_shopping_list_ui.py`
- `README.md`
- `docs/GUIA_USO_MVP.md`
- `docs/DATA_CONTRACT.md`
- `docs/TEST_PLAN.md`
- `docs/PROJECT_STATUS.md`
- `docs/DATA_RETENTION_POLICY.md`
- `docs/CHANGELOG.md`

Pruebas ejecutadas:

- `python -m compileall scripts`: OK.
- `python scripts/09_validar_precios_reales.py --input data/sample/precios_reales_demo.csv`: OK, genero archivo validado y reporte.
- `python scripts/04_matching_productos.py --input data/processed/precios_reales_validados.csv --output data/processed/precios_reales_matcheados.csv`: OK.
- `python scripts/06_aplicar_promociones.py --prices data/processed/precios_reales_matcheados.csv --output data/processed/precios_reales_con_promociones.csv --date 2026-07-11`: OK.
- `python scripts/05_calcular_lista_compra.py --prices data/processed/precios_reales_con_promociones.csv`: OK.
- `python scripts/08_generar_mvp_demo.py`: OK.
- `python -m pytest`: 39 passed.
- Dashboard por HTTP local: OK, carga precios reales validados/matcheados, promociones, lista demo, ranking, faltantes, compra dividida y avisos ante CSV crudo con errores.

## 2026-07-11 - Sprint 9 - Rediseno UI/UX del dashboard

Cambios:

- Se rediseno `dashboard/index.html` con layout tipo BI/SaaS.
- Se agrego header superior, sidebar de navegacion y area principal central.
- Se organizaron secciones por `Resumen`, `Precios`, `Lista de compra`, `Comparacion` y `Ruta/cercania`.
- Se mejoraron cards, paneles, tablas, badges, espaciado y jerarquia visual.
- Se agregaron estados visuales para archivos cargados: precios, lista, sucursales y ubicacion.
- Se agrego boton global `Recalcular`.
- Se agrego boton global `Limpiar sesion`.
- Se mantuvo la logica existente de carga CSV, lista, promociones, ranking, faltantes, compra dividida y ruta.
- Se actualizaron README, guia de uso, estado y plan de pruebas.

Archivos modificados:

- `dashboard/index.html`
- `README.md`
- `docs/GUIA_USO_MVP.md`
- `docs/PROJECT_STATUS.md`
- `docs/CHANGELOG.md`
- `docs/TEST_PLAN.md`

Pruebas ejecutadas:

- `python scripts/08_generar_mvp_demo.py`: OK, genero todos los outputs MVP.
- `python -m pytest`: 33 passed.
- Dashboard por HTTP local: OK, `http://127.0.0.1:8026/dashboard/` respondio 200.
- Validacion funcional JS con CSV reales: OK, carga precios/promos, lista, sucursales, ubicacion, ranking, faltantes, export CSV y ruta.
- Consola del navegador: sin errores.

## 2026-07-11 - Sprint 8 - Release MVP v1.0 listo para release local

Cambios:

- Se agrego `scripts/08_generar_mvp_demo.py` para ejecutar el flujo demo completo en un comando.
- Se creo `docs/GUIA_USO_MVP.md` con instrucciones simples para usar el dashboard.
- Se creo `docs/RELEASE_CHECKLIST.md` para validar pruebas, archivos ignorados, dashboard y documentacion.
- Se actualizo `README.md` con inicio rapido, flujo completo, estructura, limitaciones y proximos pasos.
- Se actualizo `docs/PROJECT_STATUS.md` indicando MVP v1.0 listo para release local.
- Se actualizo `docs/DATA_CONTRACT.md` con el flujo orquestado por Sprint 8.
- Se actualizo `docs/TEST_PLAN.md` con pruebas de release MVP.
- Se actualizo `docs/DATA_RETENTION_POLICY.md` con todos los samples versionables actuales.
- Se mejoraron mensajes del dashboard para CSV sin filas validas, lista vacia, sucursales vacias, precios faltantes y ruta/cercania incompleta.
- Se documento `python -m compileall scripts` como comando de compilacion compatible con PowerShell.

Archivos creados:

- `scripts/08_generar_mvp_demo.py`
- `docs/GUIA_USO_MVP.md`
- `docs/RELEASE_CHECKLIST.md`

Archivos modificados:

- `README.md`
- `dashboard/index.html`
- `docs/DATA_CONTRACT.md`
- `docs/TEST_PLAN.md`
- `docs/PROJECT_STATUS.md`
- `docs/CHANGELOG.md`
- `docs/DATA_RETENTION_POLICY.md`

Pruebas ejecutadas:

- `python -m compileall scripts`: OK.
- `python scripts/08_generar_mvp_demo.py`: OK, genero todos los outputs demo.
- `python -m pytest`: 33 passed.
- Dashboard por HTTP local: OK, `http://127.0.0.1:8026/dashboard/` respondio 200.
- Validacion funcional JS del dashboard con CSV reales: OK, carga precios/promos, lista, sucursales, ubicacion, ranking, localStorage, export CSV y ruta.

## 2026-07-11 - Sprint 7 - Ruta y cercania

Cambios:

- Se creo `data/sample/sucursales_demo.csv` con sucursales demo y coordenadas locales.
- Se creo `data/sample/ubicacion_usuario_demo.csv` con punto de partida demo.
- Se agrego `scripts/07_planificar_ruta.py` para calcular distancia Haversine, score de conveniencia y ruta dividida.
- Se genera `data/processed/recomendacion_ruta.csv`.
- Se genera `data/processed/ruta_compra_dividida.csv`.
- Se agrego score `costo_total_estimado + distancia_km * costo_km_estimado`.
- Se definio `costo_km_estimado` demo en 180 pesos por km.
- Se actualizo `dashboard/index.html` con carga de sucursales, ubicacion, coordenadas manuales, ranking por conveniencia y ruta dividida sugerida.
- Se agregaron pruebas automatizadas de ruta y se amplio la prueba JS del dashboard.
- Se actualizaron README, contrato de datos, plan de pruebas y estado del proyecto.

Archivos creados:

- `data/sample/sucursales_demo.csv`
- `data/sample/ubicacion_usuario_demo.csv`
- `scripts/07_planificar_ruta.py`
- `tests/test_route_planning.py`

Archivos modificados:

- `dashboard/index.html`
- `tests/test_dashboard_shopping_list_ui.py`
- `README.md`
- `docs/DATA_CONTRACT.md`
- `docs/TEST_PLAN.md`
- `docs/PROJECT_STATUS.md`
- `docs/CHANGELOG.md`

Pruebas:

- `python -m py_compile scripts/07_planificar_ruta.py`: OK.
- `python scripts/07_planificar_ruta.py`: OK, 12 recomendaciones y 2 paradas.
- `python -m pytest tests/test_route_planning.py tests/test_promotions.py tests/test_shopping_list.py`: 14 passed.
- `python -m pytest tests/test_dashboard_shopping_list_ui.py tests/test_route_planning.py`: 5 passed.
- Flujo completo Sprint 1-7 con promociones y ruta: OK.
- `python -m pytest`: 33 passed.
- Dashboard por HTTP local: OK, secciones de ruta visibles y CSV de recomendacion servido.

## 2026-07-11 - Sprint 6 - Promociones y precio efectivo

Cambios:

- Se creo `data/sample/promociones_demo.csv` con promociones demo versionables.
- Se agrego `scripts/06_aplicar_promociones.py` para calcular `precio_efectivo`.
- Se agrego soporte para descuentos por porcentaje, monto fijo, segunda unidad, precio especial y medio de pago.
- Se agrego logica de vigencia, dia de semana, topes, prioridad y acumulabilidad.
- Se documento que `--date 2026-07-11` es fecha de prueba para promociones demo y que, si se omite, el script usa la fecha actual del sistema.
- Se actualizo `scripts/05_calcular_lista_compra.py` para usar `precio_efectivo` y `precio_unitario_efectivo` cuando existen.
- Se actualizo `dashboard/index.html` para cargar CSV con o sin promociones.
- Se agrego visualizacion de precio original, precio efectivo, ahorro y descripcion de promocion.
- Se agregaron pruebas automatizadas de promociones y ranking con precio efectivo.
- Se ampliaron las pruebas JS del dashboard para validar precio efectivo.
- Se actualizaron README, contrato de datos, plan de pruebas y estado del proyecto.

Archivos creados:

- `data/sample/promociones_demo.csv`
- `scripts/06_aplicar_promociones.py`
- `tests/test_promotions.py`

Archivos modificados:

- `dashboard/index.html`
- `scripts/05_calcular_lista_compra.py`
- `tests/test_dashboard_shopping_list_ui.py`
- `README.md`
- `docs/DATA_CONTRACT.md`
- `docs/TEST_PLAN.md`
- `docs/PROJECT_STATUS.md`
- `docs/CHANGELOG.md`

Pruebas:

- `python -m py_compile scripts/05_calcular_lista_compra.py scripts/06_aplicar_promociones.py`: OK.
- `python scripts/02_normalizar_precios.py`: OK.
- `python scripts/01_descargar_o_importar_sepa.py --mode manual --input data/sample/sepa/sepa_precios_simulado.csv`: OK.
- `python scripts/03_filtrar_san_juan.py --input data/raw/sepa/manual/sepa_precios_simulado.csv`: OK, 32 filas San Juan.
- `python scripts/04_matching_productos.py`: OK, 32 filas y 7 grupos.
- `python scripts/06_aplicar_promociones.py --date 2026-07-11`: OK, 32 filas, 12 con promocion, ahorro total 3045.50.
- `python scripts/05_calcular_lista_compra.py`: OK, modo `precio_gondola`.
- `python scripts/05_calcular_lista_compra.py --prices data/processed/precios_con_promociones.csv --report data/processed/lista_compra_promociones_reporte.json`: OK, modo `precio_efectivo`, mejor comercio `ChangoMas`.
- `python -m pytest`: 30 passed.
- Dashboard por HTTP local: OK, `dashboard/` HTTP 200 y CSV promocionado HTTP 200.

## 2026-07-10 - Sprint 5 - Lista visual en dashboard

Cambios:

- Se actualizo `dashboard/index.html` con un modulo visual para armar listas de compra.
- Se agrego busqueda de productos/grupos comparables desde `precios_matcheados.csv`.
- Se agrego alta de items con cantidad, unidad y prioridad.
- Se agrego edicion de cantidad/unidad/prioridad y eliminacion de items.
- Se agrego persistencia local con `localStorage`.
- Se agrego recuperacion y limpieza de lista guardada.
- Se agrego exportacion CSV compatible con `scripts/05_calcular_lista_compra.py`.
- Se mantuvo compatibilidad con carga de `data/sample/lista_compra_demo.csv`.
- Se agrego seccion visual de faltantes por comercio.
- Se agregaron pruebas automatizadas del JS embebido del dashboard.
- Se actualizaron README, contrato de datos, plan de pruebas y estado del proyecto.

Archivos creados:

- `tests/test_dashboard_shopping_list_ui.py`

Archivos modificados:

- `dashboard/index.html`
- `README.md`
- `docs/DATA_CONTRACT.md`
- `docs/TEST_PLAN.md`
- `docs/PROJECT_STATUS.md`
- `docs/CHANGELOG.md`

Pruebas:

- `python -m pytest tests/test_dashboard_shopping_list_ui.py`: OK.
- `python -m pytest`: 22 passed.
- Dashboard servido por HTTP local y validado con CSV real `precios_matcheados.csv`: OK.

## 2026-07-10 - Sprint 4 - Listas de compra y ahorro

Cambios:

- Se creo la lista demo `data/sample/lista_compra_demo.csv`.
- Se agrego el script `scripts/05_calcular_lista_compra.py` para calcular costo total por comercio, faltantes, cobertura, ahorro y compra dividida.
- Se generan `data/processed/comparacion_lista_compra.csv` y `data/processed/mejor_compra_por_producto.csv` como outputs reproducibles.
- Se agregaron pruebas automatizadas para lectura de lista, conversion de unidades, ranking por cobertura/precio, faltantes y generacion de outputs.
- Se actualizo `dashboard/index.html` con un segundo cargador CSV para listas de compra, ranking por comercio, KPIs de ahorro y mejor compra por producto.
- Se actualizo documentacion de README, contrato de datos, plan de pruebas y estado del proyecto.

Archivos creados:

- `data/sample/lista_compra_demo.csv`
- `scripts/05_calcular_lista_compra.py`
- `tests/test_shopping_list.py`

Archivos modificados:

- `dashboard/index.html`
- `README.md`
- `docs/DATA_CONTRACT.md`
- `docs/TEST_PLAN.md`
- `docs/PROJECT_STATUS.md`
- `docs/CHANGELOG.md`

Pruebas:

- `python -m py_compile scripts/05_calcular_lista_compra.py`: OK.
- `python scripts/05_calcular_lista_compra.py`: OK, 5 items y 7 comercios.
- `python -m pytest`: 20 passed.

Resultado demo:

- Mejor comercio completo: `Atomo Conviene`.
- Costo estimado: `9130.50`.
- Ahorro contra el comercio mas caro con cobertura completa: `488.50`.

## 2026-07-10 - Sprint 3 - Matching de productos

Cambios:

- Se creo el script de matching `scripts/04_matching_productos.py`.
- Se agrego el diccionario editable `data/sample/product_dictionary.csv`.
- Se agrego calculo de `cantidad_base`, `unidad_base`, `precio_unitario_comparable`, `grupo_comparacion` y `confianza_matching`.
- Se actualizaron las pruebas con equivalencias de kg/1000 g, litro/1000 ml y precio unitario.
- Se agrego prueba de falsos positivos para evitar agrupar comun/zero, entera/descremada e integral/largo fino.
- Se actualizo `dashboard/index.html` para cargar CSV matcheado sin perder compatibilidad con CSVs anteriores.
- Se actualizo documentacion de contrato, pruebas, estado y README.

Archivos creados:

- `data/sample/product_dictionary.csv`
- `scripts/04_matching_productos.py`
- `tests/test_product_matching.py`

Archivos modificados:

- `dashboard/index.html`
- `README.md`
- `docs/DATA_CONTRACT.md`
- `docs/TEST_PLAN.md`
- `docs/PROJECT_STATUS.md`
- `docs/CHANGELOG.md`

Pruebas:

- `python -m py_compile scripts/04_matching_productos.py`: OK.
- `python scripts/04_matching_productos.py`: OK, 32 filas, 7 grupos comparables.
- `python -m pytest`: 17 passed.

## 2026-07-09 - Sprint 2 - Ingestion SEPA/manual San Juan

Cambios:

- Se creo una rama dedicada `sprint-2-sepa-ingestion`.
- Se documento la estructura esperada de SEPA y sus paquetes ZIP/CSV.
- Se agrego un importador manual para ZIP/CSV SEPA y un modo preparado para descarga futura.
- Se agrego un filtro San Juan que genera CSV compatible con el dashboard Sprint 1.
- Se agrego un sample tipo SEPA versionable para pruebas reproducibles.
- Se agregaron pruebas automatizadas para CSV consolidado, ZIP manual, ZIP tipo SEPA oficial y error por campos minimos.

Archivos creados:

- `data/sample/sepa/sepa_precios_simulado.csv`
- `scripts/01_descargar_o_importar_sepa.py`
- `scripts/03_filtrar_san_juan.py`
- `tests/test_sepa_ingestion.py`
- `docs/SEPA_STRUCTURE.md`

Archivos modificados:

- `README.md`
- `docs/DATA_CONTRACT.md`
- `docs/TEST_PLAN.md`
- `docs/PROJECT_STATUS.md`
- `docs/CHANGELOG.md`

Pruebas:

- `python -m py_compile scripts/01_descargar_o_importar_sepa.py scripts/02_normalizar_precios.py scripts/03_filtrar_san_juan.py`: OK.
- `python scripts/02_normalizar_precios.py`: OK, 31 registros validos, 0 errores.
- `python scripts/01_descargar_o_importar_sepa.py --mode download-plan`: OK.
- `python scripts/01_descargar_o_importar_sepa.py --mode manual --input data/sample/sepa/sepa_precios_simulado.csv`: OK.
- `python scripts/03_filtrar_san_juan.py --input data/raw/sepa/manual/sepa_precios_simulado.csv`: OK, 32 filas San Juan, 2 fuera de provincia excluidas.
- `python -m pytest`: 10 passed.
- Dashboard: abre por HTTP local y el parser lee `data/processed/precios_san_juan_sepa.csv` con 32 filas, 7 productos, 7 comercios, busqueda `yerba` con 6 resultados y tabla ordenada.

## 2026-07-09 - Sprint 1 - Base funcional CSV local

Cambios:

- Se agrego un CSV demo local con precios ficticios realistas de San Juan.
- Se creo un normalizador Python para validar columnas, limpiar texto, convertir precios y validar fechas.
- Se creo un dashboard standalone para cargar CSV local y comparar precios sin backend.
- Se agrego documentacion Sprint 1 en `docs/ROADMAP.md`, `docs/DATA_CONTRACT.md` y `docs/TEST_PLAN.md`.
- Se actualizo README, estado del proyecto y reglas de `.gitignore` para versionar los entregables demo.

Archivos creados:

- `data/sample/precios_demo.csv`
- `scripts/02_normalizar_precios.py`
- `dashboard/index.html`
- `docs/ROADMAP.md`
- `docs/DATA_CONTRACT.md`
- `docs/TEST_PLAN.md`

Archivos modificados:

- `README.md`
- `.gitignore`
- `docs/PROJECT_STATUS.md`
- `docs/CHANGELOG.md`

Pruebas:

- `python scripts/02_normalizar_precios.py`: OK, 31 registros validos, 0 errores.
- `python -m py_compile scripts/02_normalizar_precios.py`: OK.
- Prueba temporal de columna faltante: OK.
- Prueba temporal de precio invalido: OK.
- `python -m pytest`: 6 passed.
- Dashboard servido temporalmente en `http://127.0.0.1:8011/dashboard/`: HTTP 200.
- Verificacion estructural: cargador CSV y parser presentes.

Auditoria posterior:

- Se detecto y corrigio un error en `dashboard/index.html`: el parser de precio removia todos los puntos y podia leer `870.00` como `87000`.
- Se agrego `parsePrice()` para soportar precios con punto decimal y formato argentino con coma decimal.
- Revalidacion del dashboard con `data/processed/precios_normalizados.csv`: 31 filas, 7 productos, 7 comercios, promedio $2.378,40, busqueda `yerba` con 5 resultados y orden ascendente correcto.

Cierre Git:

- Se eligio la opcion A recomendada: datos demo versionables en `data/sample/precios_demo.csv`.
- `data/raw/` queda ignorado para crudos reales.
- `data/processed/precios_normalizados.csv` queda como salida generada reproducible y no versionada.

## 2026-07-09 - Sprint 0 - Gobernanza, orden y control

Cambios:

- Se creo documentacion de gobierno para trabajo por sprints.
- Se documento arquitectura, contrato de datos, backlog y plan de pruebas.
- Se documento inventario de artefactos/legacy sin borrar archivos.
- Se actualizo estado del proyecto con diagnostico Sprint 0.
- Se completo `.gitignore` para caches locales.

Archivos creados:

- `AGENTS.md`
- `ROADMAP.md`
- `BACKLOG.md`
- `DATA_CONTRACT.md`
- `TEST_PLAN.md`
- `docs/ARCHITECTURE.md`
- `docs/LEGACY_INVENTORY.md`
- `docs/CHANGELOG.md`

Archivos modificados:

- `.gitignore`
- `docs/PROJECT_STATUS.md`

Pruebas:

- `python -m pytest`: 6 passed.
- `python src/run_pipeline.py --export`: OK.
- `python -m http.server 8000`: verificacion HTTP 200 en `/app/` y `/app/promociones.html`.

Observaciones:

- No se modificaron archivos funcionales de app, pipeline, scrapers, base ni exports.
- Git apunta al Desktop completo; no se hizo commit automatico.

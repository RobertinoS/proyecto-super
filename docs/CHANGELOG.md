# Changelog

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

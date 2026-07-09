# Changelog

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

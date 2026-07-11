# Estado del proyecto

Actualizado: 2026-07-11.

## Sprint actual

Sprint 9 - Rediseno UI/UX del dashboard.

Rama:

```text
sprint-9-dashboard-ui-redesign
```

Objetivo: mejorar la interfaz y distribucion del dashboard sin cambiar la logica principal del negocio.

## Diagnostico ejecutivo

El repo Git dedicado esta en:

```text
C:\Users\Rober\Desktop\Proyecto Super
```

Sprint 1 a Sprint 8 se mantienen compatibles. El proyecto mantiene MVP v1.0.0 en `main` y este sprint rediseña solamente la capa visual del dashboard: navegacion lateral, header, estados de archivo, cards y mejor distribucion de secciones. No usa Google Maps API, APIs pagas, credenciales ni backend obligatorio.

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

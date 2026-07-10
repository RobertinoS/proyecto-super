# Estado del proyecto

Actualizado: 2026-07-10.

## Sprint actual

Sprint 5 - Lista visual de compra en dashboard.

Rama:

```text
sprint-5-shopping-list-ui
```

Objetivo: permitir que el usuario cree, edite, guarde, recupere y exporte listas de compra desde `dashboard/index.html`, sin editar CSV manualmente.

## Diagnostico ejecutivo

El repo Git dedicado esta en:

```text
C:\Users\Rober\Desktop\Proyecto Super
```

Sprint 1, Sprint 2, Sprint 3 y Sprint 4 se mantienen compatibles. El dashboard conserva la carga de CSV local y ahora suma un constructor visual de listas basado en `grupo_comparacion`. Todo funciona local, sin backend obligatorio, sin credenciales y sin servicios pagos.

## Flujo actual

```text
data/sample/sepa/sepa_precios_simulado.csv
        -> scripts/03_filtrar_san_juan.py
        -> data/processed/precios_san_juan_sepa.csv
        -> scripts/04_matching_productos.py
        -> data/processed/precios_matcheados.csv
        -> dashboard/index.html
        -> armar/guardar/exportar lista
        -> ranking, faltantes, ahorro y compra dividida
```

Tambien sigue disponible el flujo por script:

```text
data/processed/precios_matcheados.csv
        + data/sample/lista_compra_demo.csv
        -> scripts/05_calcular_lista_compra.py
        -> data/processed/comparacion_lista_compra.csv
        -> data/processed/mejor_compra_por_producto.csv
```

## Artefactos Sprint 5

- `dashboard/index.html`
- `tests/test_dashboard_shopping_list_ui.py`
- `README.md`
- `docs/DATA_CONTRACT.md`
- `docs/TEST_PLAN.md`
- `docs/PROJECT_STATUS.md`
- `docs/CHANGELOG.md`

## Decision tecnica

- La interfaz usa `precios_matcheados.csv` como catalogo de grupos comparables.
- Agregar productos usa `grupo_comparacion`, cantidad, unidad y prioridad.
- La lista se mantiene en memoria y puede persistirse en `localStorage`.
- La exportacion CSV conserva el contrato `item_lista,grupo_comparacion,cantidad,unidad,prioridad`.
- El calculo de ranking y compra dividida reutiliza la logica del Sprint 4 embebida en el dashboard.
- No se agrega backend ni dependencia paga.

## Funcionalidades Sprint 5

- Cargar `precios_matcheados.csv`.
- Buscar productos o grupos para agregar.
- Agregar productos a la lista desde la UI.
- Editar cantidad, unidad y prioridad.
- Eliminar productos.
- Guardar lista en el navegador.
- Recuperar lista guardada al abrir o con boton.
- Limpiar lista guardada.
- Exportar CSV compatible con `scripts/05_calcular_lista_compra.py`.
- Cargar `data/sample/lista_compra_demo.csv`.
- Calcular ranking por comercio desde la interfaz.
- Mostrar mejor comercio, ahorro estimado, faltantes y mejor compra dividida.

## Validaciones actuales

Pruebas agregadas:

- `tests/test_dashboard_shopping_list_ui.py`

Cobertura:

- secciones visuales del dashboard;
- carga logica de precios matcheados;
- catalogo por `grupo_comparacion`;
- agregar, editar y eliminar items;
- guardar, recuperar y limpiar `localStorage`;
- exportar CSV;
- ranking, faltantes y compra dividida.

Pruebas ejecutadas:

```bash
python -m pytest
```

Resultado:

- `22 passed`.

Validacion manual:

- `dashboard/index.html` servido por HTTP local: OK.
- Secciones de Sprint 5 visibles: OK.
- JS del dashboard validado con `data/processed/precios_matcheados.csv`: 32 precios, 7 grupos, lista visual simulada, export CSV y ranking OK.

## Riesgos y pendientes

- La lista visual depende de que el CSV tenga `grupo_comparacion`.
- El usuario todavia debe cargar manualmente el CSV de precios local.
- La persistencia vive solo en el navegador actual.
- Falta incorporar promociones, descuentos de tarjeta y ruta de compra.

## Proximo sprint recomendado

Sprint 6 - Promociones, descuentos y planificacion de ruta.

Objetivo: integrar promociones por sector/tarjeta, calcular precio efectivo y sugerir ruta de compra considerando ahorro, faltantes y cercania.

# Estado del proyecto

Actualizado: 2026-07-11.

## Sprint actual

Sprint 6 - Promociones y precio efectivo.

Rama:

```text
sprint-6-promotions-effective-price
```

Objetivo: calcular precio efectivo con promociones simples, descuentos por medio de pago, topes, vigencia y prioridad, manteniendo compatibilidad con los sprints anteriores.

## Diagnostico ejecutivo

El repo Git dedicado esta en:

```text
C:\Users\Rober\Desktop\Proyecto Super
```

Sprint 1 a Sprint 5 se mantienen compatibles. El proyecto ahora agrega un motor local de promociones que genera `data/processed/precios_con_promociones.csv` sin modificar los precios matcheados originales. El dashboard puede cargar precios con o sin promociones y cambia automaticamente el ranking de lista segun el precio disponible.

## Flujo actual

```text
data/sample/sepa/sepa_precios_simulado.csv
        -> scripts/03_filtrar_san_juan.py
        -> data/processed/precios_san_juan_sepa.csv
        -> scripts/04_matching_productos.py
        -> data/processed/precios_matcheados.csv
        -> scripts/06_aplicar_promociones.py
        -> data/processed/precios_con_promociones.csv
        -> dashboard/index.html
        -> ranking con precio efectivo, faltantes, ahorro y compra dividida
```

Tambien sigue disponible el flujo sin promociones:

```text
data/processed/precios_matcheados.csv
        + data/sample/lista_compra_demo.csv
        -> scripts/05_calcular_lista_compra.py
        -> data/processed/comparacion_lista_compra.csv
        -> data/processed/mejor_compra_por_producto.csv
```

## Artefactos Sprint 6

- `data/sample/promociones_demo.csv`
- `scripts/06_aplicar_promociones.py`
- `tests/test_promotions.py`
- `scripts/05_calcular_lista_compra.py`
- `dashboard/index.html`
- `tests/test_dashboard_shopping_list_ui.py`
- `README.md`
- `docs/DATA_CONTRACT.md`
- `docs/TEST_PLAN.md`
- `docs/PROJECT_STATUS.md`
- `docs/CHANGELOG.md`

## Decision tecnica

- `precio` queda como precio de gondola.
- `precio_original` conserva explicitamente el precio base cuando se aplican promociones.
- `precio_efectivo` representa el precio final luego de promociones aplicables.
- `precio_unitario_efectivo` se usa para comparar por kg, litro o unidad cuando existe.
- `scripts/05_calcular_lista_compra.py` usa precio efectivo si el CSV lo trae; si no, usa el precio comparable original.
- Promociones no acumulables: gana la de mayor ahorro.
- Promociones acumulables: se aplican por prioridad ascendente, respetando topes.
- `segunda_unidad` se calcula como descuento promedio por unidad.
- Para pruebas reproducibles del demo se usa `--date 2026-07-11`.
- Si no se informa `--date`, `scripts/06_aplicar_promociones.py` usa la fecha actual del sistema.
- No se agregan APIs, credenciales, backend ni servicios pagos.

## Funcionalidades Sprint 6

- Archivo demo de promociones versionable.
- Aplicacion de descuentos por porcentaje.
- Aplicacion de descuentos de monto fijo.
- Aplicacion de segunda unidad.
- Aplicacion de precio especial.
- Aplicacion de descuento por medio de pago.
- Validacion de vigencia por fecha y dia de semana.
- Soporte de tope de descuento.
- Soporte de prioridad y acumulabilidad.
- Dashboard con precio original, precio efectivo, ahorro y descripcion de promocion.
- Ranking de lista usando precio efectivo cuando esta disponible.

## Validaciones actuales

Pruebas agregadas:

- `tests/test_promotions.py`

Cobertura:

- carga de promociones;
- vigencia por fecha y dia;
- promociones vencidas no aplican;
- promociones futuras no aplican antes de `fecha_inicio`;
- descuento porcentual;
- descuento monto fijo;
- tope;
- precio especial;
- segunda unidad;
- medio de pago;
- prioridad;
- acumulabilidad;
- generacion de `precios_con_promociones.csv`;
- ranking de lista con precio efectivo;
- dashboard JS con precio efectivo.

Pruebas ejecutadas:

```bash
python -m py_compile scripts/05_calcular_lista_compra.py scripts/06_aplicar_promociones.py
python scripts/02_normalizar_precios.py
python scripts/01_descargar_o_importar_sepa.py --mode manual --input data/sample/sepa/sepa_precios_simulado.csv
python scripts/03_filtrar_san_juan.py --input data/raw/sepa/manual/sepa_precios_simulado.csv
python scripts/04_matching_productos.py
python scripts/06_aplicar_promociones.py --date 2026-07-11
python scripts/05_calcular_lista_compra.py
python scripts/05_calcular_lista_compra.py --prices data/processed/precios_con_promociones.csv --report data/processed/lista_compra_promociones_reporte.json
python -m pytest
```

Resultado:

- `precios_con_promociones.csv`: 32 filas generadas, 12 con promocion aplicada.
- `rows_with_promotion`: 12.
- `total_saving`: `3045.50`.
- Ranking sin promociones: mejor comercio `Atomo Conviene`, modo `precio_gondola`.
- Ranking con promociones: mejor comercio `ChangoMas`, modo `precio_efectivo`, costo `7771.55`.
- `python -m pytest`: `30 passed`.
- Dashboard servido por HTTP local: OK, `dashboard/` HTTP 200 y CSV promocionado HTTP 200.

## Riesgos y pendientes

- Las promociones demo son ficticias y deben reemplazarse por promociones oficiales o relevadas de cada comercio.
- La seleccion de medio de pago todavia se controla por script; el dashboard muestra promociones disponibles del CSV cargado.
- `segunda_unidad` se modela como descuento promedio por unidad, no como optimizacion exacta por pares en lista.
- Falta optimizacion de ruta/distancia y cercania de sucursales.

## Proximo sprint recomendado

Sprint 7 - Ruta de compra y cercania.

Objetivo: sumar ubicacion/sucursal, distancia estimada y una recomendacion que balancee ahorro, faltantes y esfuerzo de traslado.

# Estado del proyecto

Actualizado: 2026-07-10.

## Sprint actual

Sprint 4 - Listas de compra, ahorro y compra dividida.

Rama:

```text
sprint-4-shopping-list
```

Objetivo: permitir que el usuario cargue una lista de compra y vea costo total por comercio, cobertura, faltantes, ahorro potencial y mejor compra por producto usando los grupos comparables del Sprint 3.

## Diagnostico ejecutivo

El repo Git dedicado esta en:

```text
C:\Users\Rober\Desktop\Proyecto Super
```

Sprint 1, Sprint 2 y Sprint 3 se mantienen compatibles. El dashboard conserva la carga de CSV local y la comparacion individual por producto, y suma un segundo cargador para listas de compra. El nuevo modulo funciona sin backend, sin credenciales y sin servicios pagos.

## Flujo actual

```text
data/sample/sepa/sepa_precios_simulado.csv
        -> scripts/03_filtrar_san_juan.py
        -> data/processed/precios_san_juan_sepa.csv
        -> scripts/04_matching_productos.py
        -> data/processed/precios_matcheados.csv
        + data/sample/lista_compra_demo.csv
        -> scripts/05_calcular_lista_compra.py
        -> data/processed/comparacion_lista_compra.csv
        -> data/processed/mejor_compra_por_producto.csv
        -> dashboard/index.html
```

## Artefactos Sprint 4

- `data/sample/lista_compra_demo.csv`
- `scripts/05_calcular_lista_compra.py`
- `tests/test_shopping_list.py`
- `data/processed/comparacion_lista_compra.csv` generado localmente
- `data/processed/mejor_compra_por_producto.csv` generado localmente
- `data/processed/lista_compra_reporte.json` generado localmente

## Decision tecnica

- Solucion local, costo 0 y auditable.
- La lista usa `grupo_comparacion` como clave de negocio.
- Las cantidades de lista se convierten a unidad base: `g` a `kg`, `ml`/`cc` a `l`.
- El costo por item se calcula con `precio_unitario_comparable * cantidad`.
- El ranking prioriza comercios con mayor cobertura de lista y luego menor costo total.
- La compra dividida elige el menor costo por item entre todos los comercios.
- Los outputs generados quedan en `data/processed/` y no se versionan.

## Resultados actuales

Con el sample SEPA y la lista demo:

- Precios matcheados: 32 filas.
- Grupos comparables: 7.
- Items de lista: 5.
- Comercios comparados: 7.
- Mejor comercio con cobertura completa: `Atomo Conviene`.
- Costo estimado mejor comercio: `9130.50`.
- Ahorro contra el comercio mas caro con cobertura completa: `488.50`.

Ranking de comercios con cobertura completa:

- `Atomo Conviene`: `9130.50`.
- `ChangoMas`: `9143.00`.
- `Vea`: `9450.00`.
- `Carrefour`: `9619.00`.

Mejor compra por producto:

- Aceite girasol 900ml: `Atomo Conviene`.
- Arroz 1kg: `Atomo Conviene`.
- Fideos spaghetti 500g: `ChangoMas`.
- Leche entera 1L: `ChangoMas`.
- Yerba Playadito 1kg: `ChangoMas`.

## Pruebas ejecutadas

```bash
python -m py_compile scripts/05_calcular_lista_compra.py
python scripts/05_calcular_lista_compra.py
python -m pytest
```

Resultados:

- Compilacion Python: OK.
- Calculo de lista: OK, 5 items y 7 comercios.
- `python -m pytest`: 20 passed.

## Riesgos y pendientes

- La lista depende de que el `grupo_comparacion` exista en los precios matcheados.
- Falta una interfaz para armar y guardar listas desde el dashboard sin editar CSV.
- Falta incorporar promociones, descuentos de tarjeta y restricciones por sucursal.
- La compra dividida no optimiza distancia, tiempo ni ruta todavia.

## Proximo sprint recomendado

Sprint 5 - Promociones, descuentos y planificacion de ruta.

Objetivo: integrar promociones por sector/tarjeta, calcular precio efectivo y sugerir ruta de compra considerando ahorro, faltantes y cercania.

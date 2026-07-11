# Proyecto Super San Juan

Comparador local de precios para supermercados, autoservicios y mayoristas de San Juan.

El proyecto mantiene dos caminos compatibles:

```text
Sprint 1 CSV demo:
data/sample/precios_demo.csv
        -> scripts/02_normalizar_precios.py
        -> data/processed/precios_normalizados.csv
        -> dashboard/index.html

Sprint 2 SEPA/manual:
data/sample/sepa/sepa_precios_simulado.csv o data/raw/sepa/manual/*.csv|*.zip
        -> scripts/01_descargar_o_importar_sepa.py
        -> scripts/03_filtrar_san_juan.py
        -> data/processed/precios_san_juan_sepa.csv
        -> dashboard/index.html

Sprint 3 matching:
data/processed/precios_san_juan_sepa.csv
        -> scripts/04_matching_productos.py
        -> data/processed/precios_matcheados.csv
        -> dashboard/index.html

Sprint 4 lista de compra:
data/processed/precios_matcheados.csv + data/sample/lista_compra_demo.csv
        -> scripts/05_calcular_lista_compra.py
        -> data/processed/comparacion_lista_compra.csv
        -> data/processed/mejor_compra_por_producto.csv
        -> dashboard/index.html

Sprint 5 lista visual:
data/processed/precios_matcheados.csv
        -> dashboard/index.html
        -> armar/editar/guardar/exportar lista desde el navegador
        -> ranking, faltantes, ahorro y compra dividida

Sprint 6 promociones:
data/processed/precios_matcheados.csv + data/sample/promociones_demo.csv
        -> scripts/06_aplicar_promociones.py
        -> data/processed/precios_con_promociones.csv
        -> scripts/05_calcular_lista_compra.py
        -> ranking usando precio efectivo cuando existe
        -> dashboard/index.html
```

## Requisitos

- Python 3.11 o superior.
- Navegador moderno.
- No requiere backend para el dashboard CSV.
- No requiere credenciales, servicios pagos ni APIs privadas.

Instalar dependencias del proyecto completo:

```bash
python -m pip install -r requirements.txt
```

## Sprint 1: CSV local demo

Normalizar datos demo:

```bash
python scripts/02_normalizar_precios.py
```

Salida esperada:

```text
data/processed/precios_normalizados.csv
```

Abrir dashboard:

1. Abrir `dashboard/index.html` con doble clic o desde el navegador.
2. Presionar "Seleccionar archivo".
3. Cargar `data/processed/precios_normalizados.csv`.
4. Buscar productos y comparar precios por comercio.

## Sprint 2: SEPA/manual San Juan

SEPA se integra como fuente inicial oficial/semirreal sin reemplazar el dashboard ni el flujo local del Sprint 1.

Investigar o dejar preparado el modo descarga:

```bash
python scripts/01_descargar_o_importar_sepa.py --mode download-plan
```

Importar un ZIP/CSV descargado manualmente:

```bash
python scripts/01_descargar_o_importar_sepa.py --mode manual --input data/sample/sepa/sepa_precios_simulado.csv
```

Filtrar San Juan y generar CSV compatible:

```bash
python scripts/03_filtrar_san_juan.py --input data/raw/sepa/manual/sepa_precios_simulado.csv
```

Salida esperada:

```text
data/processed/precios_san_juan_sepa.csv
data/processed/precios_san_juan_sepa_reporte.json
```

Luego abrir `dashboard/index.html` y cargar `data/processed/precios_san_juan_sepa.csv`.

## Sprint 3: matching de productos

El matching agrupa productos equivalentes o posibles equivalentes por nombre normalizado, marca, categoria y presentacion. Es una solucion local, auditable y progresiva: primero usa un diccionario editable y luego aplica reglas simples.

Generar precios matcheados:

```bash
python scripts/04_matching_productos.py
```

Salida esperada:

```text
data/processed/precios_matcheados.csv
data/processed/precios_matcheados_reporte.json
```

El CSV agrega:

- `cantidad_base`
- `unidad_base`
- `precio_unitario_comparable`
- `grupo_comparacion`
- `confianza_matching`

Luego abrir `dashboard/index.html` y cargar `data/processed/precios_matcheados.csv`.

## Sprint 4: listas de compra y ahorro

El modulo de lista calcula el costo total por comercio usando `grupo_comparacion` y `precio_unitario_comparable`. Tambien detecta faltantes y recomienda el comercio mas barato para cada item si se permite dividir la compra.

Lista demo versionable:

```text
data/sample/lista_compra_demo.csv
```

Calcular ranking de comercios y mejor compra por producto:

```bash
python scripts/05_calcular_lista_compra.py
```

Salidas esperadas:

```text
data/processed/comparacion_lista_compra.csv
data/processed/mejor_compra_por_producto.csv
data/processed/lista_compra_reporte.json
```

Uso en dashboard:

1. Abrir `dashboard/index.html`.
2. Cargar `data/processed/precios_matcheados.csv` en el selector de precios.
3. Cargar `data/sample/lista_compra_demo.csv` en el selector de lista.
4. Revisar ranking por comercio, cobertura, faltantes, ahorro y mejor compra por producto.

## Sprint 5: lista visual en dashboard

El dashboard permite armar la lista sin editar CSV manualmente. La interfaz usa el catalogo de `grupo_comparacion` detectado en `precios_matcheados.csv`, guarda la lista en `localStorage` y exporta un CSV compatible con `scripts/05_calcular_lista_compra.py`.

Uso recomendado:

1. Abrir `dashboard/index.html`.
2. Cargar `data/processed/precios_matcheados.csv` en "CSV de precios".
3. Buscar productos en "Armar lista".
4. Elegir cantidad, unidad y prioridad.
5. Presionar "Agregar" en los productos deseados.
6. Editar cantidades o eliminar items en "Lista actual".
7. Presionar "Calcular ranking".
8. Revisar mejor comercio, ahorro estimado, faltantes y mejor compra dividida.
9. Usar "Guardar" para conservar la lista en el navegador.
10. Usar "Exportar CSV" para generar una lista compatible con el script.

El dashboard tambien sigue aceptando `data/sample/lista_compra_demo.csv` desde el cargador de lista.

## Sprint 6: promociones y precio efectivo

El modulo de promociones calcula `precio_efectivo` sin reemplazar el precio original. Soporta descuentos por porcentaje, monto fijo, segunda unidad, precio especial y medio de pago. La regla inicial es auditable: las promociones no acumulables compiten entre si y se aplica la de mayor ahorro; las acumulables se aplican por prioridad y respetan topes.

Promociones demo versionables:

```text
data/sample/promociones_demo.csv
```

Generar precios con promociones:

```bash
python scripts/06_aplicar_promociones.py
```

Para pruebas reproducibles con las promociones demo del sprint se usa:

```bash
python scripts/06_aplicar_promociones.py --date 2026-07-11
```

`2026-07-11` es una fecha de prueba para validar la vigencia de `data/sample/promociones_demo.csv`. Si no se informa `--date`, el script usa la fecha actual del sistema.

Salida esperada:

```text
data/processed/precios_con_promociones.csv
data/processed/precios_con_promociones_reporte.json
```

Calcular lista usando precio efectivo:

```bash
python scripts/05_calcular_lista_compra.py --prices data/processed/precios_con_promociones.csv
```

Uso en dashboard:

1. Abrir `dashboard/index.html`.
2. Cargar `data/processed/precios_con_promociones.csv` en "CSV de precios".
3. Armar o cargar una lista.
4. Presionar "Calcular ranking".
5. Revisar precio original, precio efectivo, ahorro de promocion y ranking calculado con precio efectivo.

Si se carga `data/processed/precios_matcheados.csv`, el dashboard sigue usando precio de gondola.

## Datos versionables

- `data/sample/precios_demo.csv`: demo Sprint 1.
- `data/sample/sepa/sepa_precios_simulado.csv`: fuente tipo SEPA simulada para pruebas reproducibles.
- `data/sample/product_dictionary.csv`: diccionario editable de equivalencias Sprint 3.
- `data/sample/lista_compra_demo.csv`: lista demo versionable Sprint 4.
- `data/sample/promociones_demo.csv`: promociones demo versionables Sprint 6.

## Politica de datos

- No versionar archivos crudos reales ni pesados.
- Reservar `data/raw/` para datos reales descargados/importados localmente.
- Reservar `data/processed/` para salidas generadas reproducibles.
- No guardar secretos, tokens ni credenciales.

## Documentacion

- `docs/ROADMAP.md`
- `docs/DATA_CONTRACT.md`
- `docs/SEPA_STRUCTURE.md`
- `docs/TEST_PLAN.md`
- `docs/PROJECT_STATUS.md`
- `docs/CHANGELOG.md`
- `docs/DATA_RETENTION_POLICY.md`

## Proyecto completo existente

Ademas del dashboard standalone de Sprint 1/2, el repo conserva el sistema avanzado construido previamente:

- `app/index.html`: dashboard principal con JSON exportado.
- `app/promociones.html`: promociones, tarjetas y catalogos.
- `src/run_pipeline.py`: pipeline de fuentes oficiales.
- `database/precios_san_juan.sqlite`: base local ignorada por Git.
- `data/export/*.json`: exports locales ignorados por Git.

## Proximo sprint recomendado

Sprint 7: planificacion de ruta y cercania, sin perder trazabilidad de precio efectivo y promociones.

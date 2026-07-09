# Estado del proyecto

Actualizado: 2026-07-09.

## Sprint actual

Sprint 1 - Base funcional CSV local.

Objetivo: crear una base minima para comparar precios de supermercados/autoservicios usando un CSV local, normalizacion Python y dashboard sin backend.

## Diagnostico ejecutivo

El repo Git dedicado existe en:

```text
C:\Users\Rober\Desktop\Proyecto Super
```

Rama actual: `main`.

Observacion: `git log` indica que la rama aun no tiene commits visibles en este entorno y `git status` muestra el proyecto como no trackeado. No se hizo commit automatico.

## Estructura existente

Activos heredados del trabajo previo:

- `app/index.html`
- `app/promociones.html`
- `src/`
- `config/fuentes.yml`
- `database/precios_san_juan.sqlite`
- `data/export/*.json`
- `tests/`
- `docs/`

Nuevos artefactos Sprint 1:

- `data/sample/precios_demo.csv`
- `scripts/02_normalizar_precios.py`
- `data/processed/precios_normalizados.csv`
- `dashboard/index.html`

## Datos Sprint 1

CSV sample:

- Ruta: `data/sample/precios_demo.csv`.
- Registros demo: 31.
- Comercios: Vea, Carrefour, ChangoMas, Atomo Conviene y autoservicios grandes.
- Localidades: Capital, Rawson, Santa Lucia y Rivadavia.

CSV normalizado:

- Ruta: `data/processed/precios_normalizados.csv`.
- Generado por `scripts/02_normalizar_precios.py`.
- Incluye campos limpios para comercio, sucursal, producto, marca y categoria.

## Dashboard Sprint 1

Ruta:

```text
dashboard/index.html
```

Funciona sin backend mediante carga manual de CSV local.

Capacidades:

- Carga de CSV.
- Validacion de columnas.
- KPIs basicos.
- Busqueda de producto.
- Filtro por comercio.
- Comparacion por comercio.
- Tabla ordenada de menor a mayor precio.

## Pruebas Sprint 1

```bash
python scripts/02_normalizar_precios.py
python -m pytest
python -m http.server 8000
```

Resultados:

- `python scripts/02_normalizar_precios.py`: OK, 31 registros validos, 0 errores.
- `python -m py_compile scripts/02_normalizar_precios.py`: OK.
- Prueba columna faltante con CSV temporal: OK, devuelve error claro.
- Prueba precio invalido con CSV temporal: OK, excluye fila invalida y genera archivo de errores.
- `python -m pytest`: 6 passed.
- `http://127.0.0.1:8011/dashboard/`: HTTP 200 durante servidor temporal.
- Verificacion estructural del dashboard: contiene cargador CSV, parser CSV, KPIs, comparacion por comercio y tabla.
- Playwright no esta instalado localmente; no se automatizo el dialogo nativo de seleccion de archivo.

## Auditoria Sprint 1

Fecha: 2026-07-09.

Resultado:

- Todos los archivos prometidos existen.
- `scripts/02_normalizar_precios.py` corre sin errores.
- `data/processed/precios_normalizados.csv` tiene las columnas esperadas.
- Dashboard responde por HTTP local y contiene cargador CSV.
- Se verifico el JavaScript del dashboard con el CSV normalizado.
- KPIs coherentes: 31 filas, 7 productos, 7 comercios, precio promedio $2.378,40.
- Producto mas barato detectado: Fideos spaghetti en Changomas, $870.
- Busqueda `yerba`: 5 resultados correctos.
- Tabla de precios: ordenada de menor a mayor.
- Comparacion por comercio: promedios ordenados de menor a mayor.

Correccion aplicada:

- Se corrigio `dashboard/index.html` para parsear correctamente precios con punto decimal, por ejemplo `870.00`.
- Antes de la correccion, el dashboard podia interpretar `870.00` como `87000`.

## Cierre Git Sprint 1

Decision de versionado:

- Se eligio la opcion A recomendada: mover datos demo versionables a `data/sample/precios_demo.csv`.
- `data/raw/` queda reservado para datos crudos reales no versionados.
- `data/processed/precios_normalizados.csv` se genera localmente y queda ignorado como output reproducible.

## Riesgos y pendientes

- El dashboard carga CSV por selector de archivo; no lee automaticamente archivos locales por restricciones normales del navegador.
- Falta test automatizado especifico para el normalizador.
- Git aparece sin commit visible, aunque el usuario indico haber realizado un primer commit.
- El Sprint 1 usa datos ficticios; no debe confundirse con precios reales.

## Proximo sprint recomendado

Sprint 2 - Matching y equivalencias.

Objetivo: comparar productos equivalentes por nombre, marca, presentacion y unidad, evitando comparaciones erroneas.

# Plan de pruebas - Sprint 1

## 1. Normalizacion correcta del CSV

Comando:

```bash
python scripts/02_normalizar_precios.py
```

Resultado esperado:

- Se genera `data/processed/precios_normalizados.csv` desde `data/sample/precios_demo.csv`.
- El comando termina con codigo 0.
- Muestra cantidad de registros validos.

## 2. Error por columna faltante

Prueba manual:

```bash
python scripts/02_normalizar_precios.py --input data/sample/precios_demo_sin_columna.csv
```

Resultado esperado:

- El script informa `Faltan columnas obligatorias`.
- No genera salida incorrecta.

## 3. Validacion de precio

Caso:

- Precio vacio, texto no numerico, cero o negativo.

Resultado esperado:

- La fila se excluye.
- El error queda informado.
- Si hay errores, se genera `data/processed/precios_normalizados_errores.csv`.

## 4. Validacion de fecha

Caso:

- Fecha invalida.

Resultado esperado:

- La fila se excluye.
- El error queda informado.

## 5. Busqueda de producto en dashboard

Pasos:

1. Abrir `dashboard/index.html`.
2. Cargar `data/processed/precios_normalizados.csv`.
3. Buscar `yerba`, `cafe`, `leche`, `aceite`, `arroz` o `azucar`.

Resultado esperado:

- La tabla filtra resultados.
- Los KPIs se actualizan.

## 6. Comparacion por comercio

Pasos:

1. Cargar CSV normalizado.
2. Buscar un producto.
3. Revisar barras por comercio.

Resultado esperado:

- Se muestran comercios con promedio de precios filtrados.
- La tabla queda ordenada de menor a mayor precio.

## 7. Apertura del dashboard en navegador

Opciones:

```text
dashboard/index.html
```

o

```bash
python -m http.server 8000
```

```text
http://localhost:8000/dashboard/
```

Resultado esperado:

- El dashboard abre sin backend.
- El selector de archivo permite cargar CSV local.

## 8. Carga de salida normalizada

Archivo:

```text
data/processed/precios_normalizados.csv
```

Resultado esperado:

- KPIs visibles:
  - cantidad de productos;
  - cantidad de comercios;
  - precio promedio;
  - producto mas barato detectado.

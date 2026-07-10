# Plan de pruebas

Actualizado: 2026-07-09.

## Sprint 1: CSV local

### 1. Normalizacion correcta del CSV demo

Comando:

```bash
python scripts/02_normalizar_precios.py
```

Resultado esperado:

- Se genera `data/processed/precios_normalizados.csv`.
- El comando termina con codigo 0.
- Informa registros validos y errores.

### 2. Error por columna faltante

Prueba manual:

```bash
python scripts/02_normalizar_precios.py --input data/sample/precios_demo_sin_columna.csv
```

Resultado esperado:

- El script informa columnas faltantes.
- No genera salida incorrecta.

### 3. Validacion de precio y fecha

Casos:

- Precio vacio, texto no numerico, cero o negativo.
- Fecha invalida.

Resultado esperado:

- La fila se excluye.
- El error se informa.
- Si hay errores, se genera archivo de errores en `data/processed/`.

## Sprint 2: SEPA/manual

### 4. Modo descarga preparado

Comando:

```bash
python scripts/01_descargar_o_importar_sepa.py --mode download-plan
```

Resultado esperado:

- Se genera `data/raw/sepa/sepa_download_plan.json`.
- No descarga nada salvo que se use `--allow-download`.
- No requiere credenciales ni servicios pagos.

### 5. Importacion manual de CSV

Comando:

```bash
python scripts/01_descargar_o_importar_sepa.py --mode manual --input data/sample/sepa/sepa_precios_simulado.csv
```

Resultado esperado:

- Copia el archivo a `data/raw/sepa/manual/`.
- Genera `data/raw/sepa/sepa_import_manifest.json`.
- El contenido queda ignorado por Git.

### 6. Filtro San Juan

Comando:

```bash
python scripts/03_filtrar_san_juan.py --input data/raw/sepa/manual/sepa_precios_simulado.csv
```

Resultado esperado:

- Se genera `data/processed/precios_san_juan_sepa.csv`.
- Se genera `data/processed/precios_san_juan_sepa_reporte.json`.
- Localidades priorizadas: Capital, Rawson, Santa Lucia y Rivadavia.
- Filas fuera de San Juan quedan excluidas.
- La salida tiene las 10 columnas canonicas del dashboard.

### 7. ZIP tipo SEPA oficial

Prueba automatizada:

```bash
python -m pytest tests/test_sepa_ingestion.py
```

Resultado esperado:

- El test arma un ZIP con `comercio.csv`, `sucursales.csv` y `productos.csv`.
- El script une los archivos por IDs.
- Solo conserva la sucursal San Juan.

### 8. Error por campos minimos faltantes

Prueba automatizada:

```bash
python -m pytest tests/test_sepa_ingestion.py
```

Resultado esperado:

- El script falla con mensaje claro si no detecta producto, precio, comercio, sucursal o localidad.

## Dashboard

### 9. Busqueda de producto

Pasos:

1. Abrir `dashboard/index.html`.
2. Cargar `data/processed/precios_normalizados.csv` o `data/processed/precios_san_juan_sepa.csv`.
3. Buscar `yerba`, `cafe`, `leche`, `aceite`, `arroz` o `fideos`.

Resultado esperado:

- La tabla filtra resultados.
- Los KPIs se actualizan.

### 10. Comparacion por comercio

Pasos:

1. Cargar CSV normalizado.
2. Buscar un producto.
3. Revisar barras por comercio.

Resultado esperado:

- Se muestran comercios con promedio de precios filtrados.
- La tabla queda ordenada de menor a mayor precio.

### 11. Apertura del dashboard en navegador

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

## Suite minima actual

Comandos:

```bash
python -m py_compile scripts/01_descargar_o_importar_sepa.py scripts/02_normalizar_precios.py scripts/03_filtrar_san_juan.py
python scripts/02_normalizar_precios.py
python scripts/01_descargar_o_importar_sepa.py --mode download-plan
python scripts/01_descargar_o_importar_sepa.py --mode manual --input data/sample/sepa/sepa_precios_simulado.csv
python scripts/03_filtrar_san_juan.py --input data/raw/sepa/manual/sepa_precios_simulado.csv
python -m pytest
```

## Sprint 3: matching de productos

### 12. Compilacion del script de matching

Comando:

```bash
python -m py_compile scripts/04_matching_productos.py
```

Resultado esperado:

- El script compila sin errores.

### 13. Generacion de precios matcheados

Comando:

```bash
python scripts/04_matching_productos.py
```

Resultado esperado:

- Lee `data/processed/precios_san_juan_sepa.csv`.
- Usa `data/sample/product_dictionary.csv`.
- Genera `data/processed/precios_matcheados.csv`.
- Genera `data/processed/precios_matcheados_reporte.json`.

### 14. Equivalencias de unidades

Prueba automatizada:

```bash
python -m pytest tests/test_product_matching.py
```

Resultado esperado:

- `1 kg`, `1 kilo` y `1000 g` se normalizan a `1 kg`.
- `1 litro` y `1000 ml` se normalizan a `1 l`.
- `750 g` se convierte a `0.75 kg`.
- `900 ml` se convierte a `0.9 l`.

### 15. Precio unitario comparable

Prueba automatizada:

```bash
python -m pytest tests/test_product_matching.py
```

Resultado esperado:

- El precio comparable se calcula como `precio / cantidad_base`.
- El cafe de 750 g se expresa como precio por kg.
- El aceite de 900 ml se expresa como precio por litro.

### 16. Control de falsos positivos

Prueba automatizada:

```bash
python -m pytest tests/test_product_matching.py
```

Resultado esperado:

- Coca Cola comun 2.25 l no se agrupa con Coca Cola Zero 2.25 l.
- Leche entera 1 l no se agrupa con leche descremada 1 l.
- Arroz largo fino 1 kg no se agrupa con arroz integral 1 kg.

### 17. Dashboard con CSV matcheado

Pasos:

1. Abrir `dashboard/index.html`.
2. Cargar `data/processed/precios_matcheados.csv`.
3. Buscar `yerba`, `cafe`, `aceite` o `leche`.

Resultado esperado:

- Se muestra `grupo_comparacion`.
- Se muestra `precio_unitario_comparable`.
- Se muestra `confianza_matching`.
- El panel superior muestra el comercio mas barato por grupo.
- La tabla queda ordenada por precio comparable.

## Suite Sprint 3

Comandos:

```bash
python -m py_compile scripts/04_matching_productos.py
python scripts/04_matching_productos.py
python -m pytest
```

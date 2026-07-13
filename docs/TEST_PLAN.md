# Plan de pruebas

Actualizado: 2026-07-12.

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

## Sprint 4: listas de compra

### 18. Compilacion del script de lista

Comando:

```bash
python -m py_compile scripts/05_calcular_lista_compra.py
```

Resultado esperado:

- El script compila sin errores.

### 19. Calculo de ranking por comercio

Comando:

```bash
python scripts/05_calcular_lista_compra.py
```

Resultado esperado:

- Lee `data/processed/precios_matcheados.csv`.
- Lee `data/sample/lista_compra_demo.csv`.
- Genera `data/processed/comparacion_lista_compra.csv`.
- Genera `data/processed/mejor_compra_por_producto.csv`.
- Ordena comercios por mayor cobertura y menor costo total.

### 20. Deteccion de faltantes

Prueba automatizada:

```bash
python -m pytest tests/test_shopping_list.py
```

Resultado esperado:

- Un comercio sin un grupo comparable informa el item faltante.
- La cobertura queda por debajo de 100%.
- Ese comercio no supera a uno con cobertura completa solo por tener menor costo parcial.

### 21. Calculo de ahorro

Prueba automatizada:

```bash
python -m pytest tests/test_shopping_list.py
```

Resultado esperado:

- `diferencia_vs_mas_barato` compara contra el menor costo con igual cobertura maxima.
- `ahorro_vs_mas_caro` compara contra el mayor costo con igual cobertura maxima.
- `ahorro_vs_promedio` se calcula por item en la compra dividida.

### 22. Dashboard con modo lista

Pasos:

1. Abrir `dashboard/index.html`.
2. Cargar `data/processed/precios_matcheados.csv` en precios.
3. Cargar `data/sample/lista_compra_demo.csv` en lista.

Resultado esperado:

- Se mantiene la comparacion individual de productos Sprint 3.
- Se muestra ranking de comercios por costo total.
- Se muestra cobertura y faltantes por comercio.
- Se muestra la mejor compra por producto.
- La tabla de precios sigue ordenada por `precio_unitario_comparable`.

## Suite Sprint 4

Comandos:

```bash
python -m py_compile scripts/05_calcular_lista_compra.py
python scripts/05_calcular_lista_compra.py
python -m pytest
```

## Sprint 5: lista visual en dashboard

### 23. Estructura visual del dashboard

Prueba automatizada:

```bash
python -m pytest tests/test_dashboard_shopping_list_ui.py
```

Resultado esperado:

- Existen las secciones `Precios cargados`, `Armar lista`, `Lista actual`, `Ranking por comercio`, `Mejor compra dividida` y `Faltantes`.

### 24. Constructor de lista

Prueba automatizada:

```bash
python -m pytest tests/test_dashboard_shopping_list_ui.py
```

Resultado esperado:

- El JS embebido carga precios matcheados.
- Genera catalogo por `grupo_comparacion`.
- Agrega producto a lista.
- Edita cantidad.
- Elimina producto.
- Calcula ranking por comercio.
- Detecta faltantes.
- Calcula mejor compra dividida.

### 25. Persistencia local

Prueba automatizada:

```bash
python -m pytest tests/test_dashboard_shopping_list_ui.py
```

Resultado esperado:

- La lista se guarda en `localStorage`.
- La lista se recupera con la misma estructura.
- La lista guardada se puede limpiar.

### 26. Exportacion CSV

Prueba automatizada:

```bash
python -m pytest tests/test_dashboard_shopping_list_ui.py
```

Resultado esperado:

- El CSV exportado contiene `item_lista,grupo_comparacion,cantidad,unidad,prioridad`.
- El CSV exportado es compatible con `scripts/05_calcular_lista_compra.py`.

### 27. Validacion manual por navegador

Pasos:

1. Servir el proyecto con `python -m http.server 8026 --bind 127.0.0.1`.
2. Abrir `http://127.0.0.1:8026/dashboard/`.
3. Cargar `data/processed/precios_matcheados.csv`.
4. Buscar un producto en `Armar lista`.
5. Agregar un producto.
6. Editar cantidad.
7. Eliminar un producto.
8. Guardar lista.
9. Recuperar lista.
10. Exportar CSV.
11. Cargar `data/sample/lista_compra_demo.csv`.
12. Calcular ranking.

Resultado esperado:

- El dashboard abre sin backend.
- Se muestra mejor comercio.
- Se muestra ahorro estimado.
- Se muestran faltantes por comercio cuando corresponde.
- Se muestra mejor compra dividida por producto.

## Suite Sprint 5

Comandos:

```bash
python -m pytest
```

## Sprint 6: promociones y precio efectivo

### 28. Compilacion del script de promociones

Comando:

```bash
python -m py_compile scripts/06_aplicar_promociones.py
```

Resultado esperado:

- El script compila sin errores.

### 29. Generacion de precios con promociones

Comando:

```bash
python scripts/06_aplicar_promociones.py --date 2026-07-11
```

Resultado esperado:

- Lee `data/processed/precios_matcheados.csv`.
- Lee `data/sample/promociones_demo.csv`.
- Usa `2026-07-11` como fecha de prueba reproducible para las promociones demo.
- Genera `data/processed/precios_con_promociones.csv`.
- Genera `data/processed/precios_con_promociones_reporte.json`.
- Conserva `precio_original`.
- Calcula `precio_efectivo`, `ahorro_promocion` y `precio_unitario_efectivo`.

Decision de fecha:

- Si se informa `--date`, el script usa esa fecha para evaluar vigencia.
- Si se omite `--date`, el script usa la fecha actual del sistema.
- Para tests y cierres de sprint se usa `--date 2026-07-11` porque es una fecha de prueba estable para `data/sample/promociones_demo.csv`.

### 30. Reglas de promocion

Prueba automatizada:

```bash
python -m pytest tests/test_promotions.py
```

Resultado esperado:

- Carga promociones validas.
- Respeta vigencia por fecha y dia de semana.
- Excluye promociones vencidas.
- Excluye promociones futuras antes de `fecha_inicio`.
- Calcula descuento porcentual.
- Calcula descuento de monto fijo.
- Respeta tope de descuento.
- Aplica `precio_especial`.
- Calcula `segunda_unidad` como descuento promedio por unidad.
- Filtra por medio de pago cuando se informa.

### 31. Prioridad y acumulabilidad

Prueba automatizada:

```bash
python -m pytest tests/test_promotions.py
```

Resultado esperado:

- En promociones no acumulables, aplica solo la de mayor ahorro.
- En promociones acumulables, aplica por prioridad ascendente.
- El resultado final no baja de cero.

### 32. Ranking de lista con precio efectivo

Prueba automatizada:

```bash
python -m pytest tests/test_promotions.py
```

Resultado esperado:

- `scripts/05_calcular_lista_compra.py` usa `precio_efectivo` cuando existe.
- Un comercio mas caro en gondola puede quedar primero si la promocion lo vuelve mas barato.
- El reporte informa `price_mode = precio_efectivo`.

### 33. Dashboard con promociones

Pasos:

1. Servir el proyecto con `python -m http.server 8026 --bind 127.0.0.1`.
2. Abrir `http://127.0.0.1:8026/dashboard/`.
3. Cargar `data/processed/precios_con_promociones.csv`.
4. Cargar o armar una lista.
5. Calcular ranking.

Resultado esperado:

- La tabla muestra precio original.
- La tabla muestra precio efectivo.
- La tabla muestra ahorro por promocion.
- La tabla muestra descripcion de promocion aplicada.
- El ranking indica que usa precio efectivo.
- La mejor compra dividida usa precio efectivo.

## Suite Sprint 6

Comandos:

```bash
python -m py_compile scripts/06_aplicar_promociones.py
python scripts/06_aplicar_promociones.py --date 2026-07-11
python scripts/05_calcular_lista_compra.py --prices data/processed/precios_con_promociones.csv
python -m pytest
```

## Sprint 7: ruta y cercania

### 34. Compilacion del script de ruta

Comando:

```bash
python -m py_compile scripts/07_planificar_ruta.py
```

Resultado esperado:

- El script compila sin errores.

### 35. Generacion de recomendacion de ruta

Comandos:

```bash
python scripts/06_aplicar_promociones.py --date 2026-07-11
python scripts/05_calcular_lista_compra.py --prices data/processed/precios_con_promociones.csv
python scripts/07_planificar_ruta.py
```

Resultado esperado:

- Lee `data/processed/comparacion_lista_compra.csv`.
- Lee `data/processed/mejor_compra_por_producto.csv`.
- Lee `data/sample/sucursales_demo.csv`.
- Lee `data/sample/ubicacion_usuario_demo.csv`.
- Genera `data/processed/recomendacion_ruta.csv`.
- Genera `data/processed/ruta_compra_dividida.csv`.
- Genera `data/processed/ruta_reporte.json`.

### 36. Haversine y ranking por score

Prueba automatizada:

```bash
python -m pytest tests/test_route_planning.py
```

Resultado esperado:

- La distancia entre un mismo punto es 0.
- La distancia aproximada entre puntos de San Juan queda en rango razonable.
- `score_conveniencia = costo_total_estimado + distancia_km * costo_km_estimado`.
- El ranking por conveniencia prioriza cobertura y luego menor score.

### 37. Ruta dividida sugerida

Prueba automatizada:

```bash
python -m pytest tests/test_route_planning.py
```

Resultado esperado:

- Agrupa productos por `comercio_recomendado`.
- Selecciona sucursal cercana.
- Calcula distancia desde origen.
- Calcula distancia acumulada.
- Genera costo y ahorro estimado por parada.

### 38. Dashboard con ruta/cercania

Pasos:

1. Servir el proyecto con `python -m http.server 8026 --bind 127.0.0.1`.
2. Abrir `http://127.0.0.1:8026/dashboard/`.
3. Cargar `data/processed/precios_con_promociones.csv`.
4. Cargar `data/sample/lista_compra_demo.csv`.
5. Cargar `data/sample/sucursales_demo.csv`.
6. Cargar `data/sample/ubicacion_usuario_demo.csv` o ingresar coordenadas manuales.
7. Presionar `Calcular cercania`.

Resultado esperado:

- Se muestra distancia estimada por comercio/sucursal.
- Se muestra ranking por precio efectivo en el modulo de lista.
- Se muestra ranking por conveniencia precio + distancia.
- Se muestra recomendacion final.
- Se muestra ruta dividida sugerida.
- La interfaz aclara que la distancia es aproximada y no reemplaza navegacion real.
- Si se carga `precios_matcheados.csv` sin promociones, el dashboard sigue funcionando con precio de gondola.

## Suite Sprint 7

Comandos:

```bash
python -m py_compile scripts/07_planificar_ruta.py
python scripts/07_planificar_ruta.py
python -m pytest
```

## Sprint 8: Release MVP v1.0

### 39. Compilacion de todos los scripts

Comando:

```bash
python -m compileall scripts
```

Resultado esperado:

- Todos los scripts compilan sin errores.
- El comando es compatible con PowerShell porque no depende de expansion de comodines.

### 40. Flujo demo en un comando

Comando:

```bash
python scripts/08_generar_mvp_demo.py
```

Resultado esperado:

- Ejecuta normalizacion.
- Importa el sample SEPA/manual.
- Filtra San Juan.
- Genera matching.
- Aplica promociones con fecha demo `2026-07-11`.
- Calcula lista con precio efectivo.
- Planifica ruta.
- Verifica que existan los outputs principales.

### 41. Dashboard MVP completo

Pasos:

1. Servir el proyecto con `python -m http.server 8026 --bind 127.0.0.1`.
2. Abrir `http://127.0.0.1:8026/dashboard/`.
3. Cargar `data/processed/precios_con_promociones.csv`.
4. Cargar `data/sample/lista_compra_demo.csv`.
5. Cargar `data/sample/sucursales_demo.csv`.
6. Cargar `data/sample/ubicacion_usuario_demo.csv`.
7. Buscar productos.
8. Agregar producto a lista desde UI.
9. Editar cantidad.
10. Eliminar item.
11. Guardar y recuperar lista con `localStorage`.
12. Exportar CSV.
13. Calcular ranking.
14. Calcular cercania/ruta.

Resultado esperado:

- El dashboard muestra precio original, precio efectivo, ahorro de promocion y promo aplicada.
- El ranking usa precio efectivo.
- Se muestran faltantes y mejor compra dividida.
- Se muestra distancia aproximada, penalizacion, score y recomendacion final.
- Los mensajes de error son claros si faltan precios, lista, sucursales o ubicacion.

## Suite release MVP

Comandos:

```bash
python -m compileall scripts
python scripts/08_generar_mvp_demo.py
python -m pytest
```

## Sprint 9: Rediseno UI/UX dashboard

### 42. Estructura visual profesional

Validar en `dashboard/index.html`:

- header superior;
- sidebar de navegacion;
- secciones `Resumen`, `Precios`, `Lista de compra`, `Comparacion` y `Ruta/cercania`;
- KPIs visibles;
- cards y badges de estado;
- tablas legibles;
- responsive design.

### 43. Estados y acciones de sesion

Pasos:

1. Abrir dashboard por HTTP local.
2. Cargar precios, lista, sucursales y ubicacion.
3. Verificar que cada archivo muestre estado cargado.
4. Usar `Recalcular`.
5. Usar `Limpiar sesion`.

Resultado esperado:

- El usuario entiende que archivo falta o ya fue cargado.
- `Recalcular` actualiza ranking y ruta con los datos actuales.
- `Limpiar sesion` borra datos en pantalla y permite empezar de nuevo sin recargar pagina.

### 44. Compatibilidad MVP

Comandos:

```bash
python scripts/08_generar_mvp_demo.py
python -m pytest
```

Validacion manual:

- cargar `data/processed/precios_con_promociones.csv`;
- cargar `data/sample/lista_compra_demo.csv`;
- cargar `data/sample/sucursales_demo.csv`;
- cargar `data/sample/ubicacion_usuario_demo.csv`;
- armar lista desde UI;
- guardar, recuperar y exportar lista;
- calcular ranking;
- ver promociones, faltantes y mejor compra dividida;
- calcular cercania/ruta.

## Sprint 10: carga real controlada

### 45. Compilacion del validador

Comando:

```bash
python -m py_compile scripts/09_validar_precios_reales.py
```

Resultado esperado:

- El script compila sin errores.

### 46. Validacion de precios reales demo

Comando:

```bash
python scripts/09_validar_precios_reales.py --input data/sample/precios_reales_demo.csv
```

Resultado esperado:

- Genera `data/processed/precios_reales_validados.csv`.
- Genera `data/processed/reporte_validacion_precios_reales.csv`.
- Conserva al menos 20 filas validas.
- Reporta errores controlados: precio invalido, fecha invalida, localidad fuera de alcance, duplicado y precio sospechoso.

### 47. Casos automatizados de validacion real

Comando:

```bash
python -m pytest tests/test_real_data_validation.py
```

Resultado esperado:

- Valida plantilla.
- Detecta precios invalidos.
- Detecta fechas invalidas.
- Falla con reporte si faltan columnas.
- Detecta duplicados.
- Genera CSV validado y reporte.
- Confirma compatibilidad con `scripts/04_matching_productos.py`.

### 48. Dashboard con archivo real validado

Pasos:

1. Ejecutar el validador.
2. Ejecutar matching con `--input data/processed/precios_reales_validados.csv`.
3. Servir el proyecto con `python -m http.server 8026 --bind 127.0.0.1`.
4. Abrir `http://127.0.0.1:8026/dashboard/`.
5. Cargar `data/processed/precios_reales_matcheados.csv`.

Resultado esperado:

- El dashboard carga el CSV.
- Muestra KPIs, tabla y comparacion por comercio.
- Si se carga un CSV crudo con problemas, muestra avisos de calidad para precio invalido, fecha invalida, localidad fuera de alcance o duplicados.

## Suite Sprint 10

Comandos:

```bash
python -m compileall scripts
python scripts/09_validar_precios_reales.py --input data/sample/precios_reales_demo.csv
python -m pytest
```

## Sprint 11: calidad operativa diaria

### 49. Generacion de reportes de calidad

Comandos:

```bash
python scripts/09_validar_precios_reales.py --input data/sample/precios_reales_demo.csv
python scripts/10_generar_reporte_calidad_datos.py
```

Resultado esperado:

- Genera `data/processed/reporte_calidad_datos.csv`.
- Genera `data/processed/resumen_calidad_fuente.csv`.
- Calcula incidencias, duplicados, precios sospechosos, fechas y antiguedad.

### 50. Estados y score

Prueba automatizada:

```bash
python -m pytest tests/test_data_quality_operations.py
```

Resultado esperado:

- Valida estados `OK`, `REVISAR`, `INVALIDO` y `DESACTUALIZADO`.
- Valida calculo de antiguedad.
- Valida `score_calidad`.
- Confirma compatibilidad con el reporte de validacion Sprint 10.

### 51. Dashboard con calidad de datos

Pasos:

1. Servir el proyecto con `python -m http.server 8026 --bind 127.0.0.1`.
2. Abrir `http://127.0.0.1:8026/dashboard/`.
3. Cargar `data/processed/resumen_calidad_fuente.csv`.
4. Cargar `data/processed/reporte_calidad_datos.csv`.

Resultado esperado:

- Se muestra estado por comercio/sucursal.
- Se muestra score de calidad.
- Se muestra antiguedad de datos.
- Se muestra cantidad de incidencias.
- Se ve semaforo `OK`, `REVISAR`, `INVALIDO`, `DESACTUALIZADO`.

## Suite Sprint 11

Comandos:

```bash
python -m compileall scripts
python scripts/09_validar_precios_reales.py --input data/sample/precios_reales_demo.csv
python scripts/10_generar_reporte_calidad_datos.py
python -m pytest
```

## Sprint 12: consolidacion multiarchivo

### 52. Descubrimiento y validacion individual

```bash
python -m pytest tests/test_multifile_consolidation.py
```

Resultado esperado:

- Descubre recursivamente los cinco CSV de `data/sample/multifile/` en orden estable.
- Acepta distinto orden de columnas con el mismo contrato logico.
- Reporta el duplicado interno, la fila invalida y el precio sospechoso controlados.

### 53. Consolidacion, conflictos y manifiesto

```bash
python scripts/11_consolidar_relevamientos.py --input data/sample/multifile
```

Resultado esperado:

- Genera `precios_reales_consolidados.csv`, `reporte_consolidacion.csv` y `manifiesto_consolidacion.csv`.
- Procesa 5 archivos y 15 filas.
- Consolida 12 filas unicas.
- Conserva la correccion de Vea Centro a `$3150.00` y marca el conflicto.

### 54. Compatibilidad aguas abajo y dashboard

```bash
python scripts/04_matching_productos.py --input data/processed/precios_reales_consolidados.csv --output data/processed/precios_reales_consolidados_matcheados.csv
python scripts/10_generar_reporte_calidad_datos.py --prices data/processed/precios_reales_consolidados.csv --validation-report data/processed/reporte_consolidacion.csv
python -m http.server 8026 --bind 127.0.0.1
```

Abrir `http://127.0.0.1:8026/dashboard/`, cargar `precios_reales_consolidados_matcheados.csv`, cargar la lista demo y calcular ranking. El resultado debe usar 12 filas sin duplicar la correccion y el flujo v1.3.0 debe seguir operativo.

## Suite Sprint 12

```bash
python -m compileall scripts
python scripts/11_consolidar_relevamientos.py --input data/sample/multifile
python scripts/04_matching_productos.py --input data/processed/precios_reales_consolidados.csv --output data/processed/precios_reales_consolidados_matcheados.csv
python -m pytest
```

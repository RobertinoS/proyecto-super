# Proyecto Super San Juan

Comparador local de precios para supermercados, autoservicios y mayoristas de San Juan.

## MVP v1.0

Objetivo: permitir que una persona use datos CSV locales para comparar precios, promociones, listas de compra y conveniencia por distancia aproximada sin depender de backend, credenciales, APIs pagas ni Codex.

El MVP permite:

- importar o simular datos tipo SEPA/manual;
- filtrar precios de San Juan;
- agrupar productos equivalentes por `grupo_comparacion`;
- calcular precio unitario comparable;
- aplicar promociones demo y precio efectivo;
- armar o cargar una lista de compra;
- calcular ranking por comercio, ahorro y faltantes;
- sugerir compra dividida por producto;
- estimar conveniencia por distancia con Haversine;
- usar el dashboard local desde el navegador.

Sprint 10 agrega una operacion real controlada para cargar precios manuales o semimanuales por comercio/sucursal, validarlos y convertirlos en CSV limpio compatible con matching, promociones, listas y dashboard.

Sprint 12 agrega consolidacion diaria multiarchivo: descubre CSV en forma recursiva, valida cada archivo, resuelve duplicados de manera determinista y genera una base unica trazable para el flujo analitico.

Sprint 13 integra el modelo visual de Site con toda la funcionalidad v1.4.0. El dashboard oficial usa ahora una interfaz clara verde/lima, resumen ejecutivo, mejor feedback, accesibilidad basica y responsive validado, sin depender del sitio publicado ni de un proceso de build.

## Inicio rapido

Desde `C:\Users\Rober\Desktop\Proyecto Super`:

```bash
python -m pip install -r requirements.txt
python scripts/08_generar_mvp_demo.py
python -m http.server 8026 --bind 127.0.0.1
```

Abrir:

```text
http://127.0.0.1:8026/dashboard/
```

En el dashboard cargar estos archivos:

```text
data/processed/precios_con_promociones.csv
data/sample/lista_compra_demo.csv
data/sample/sucursales_demo.csv
data/sample/ubicacion_usuario_demo.csv
```

Luego usar `Calcular ranking` y `Calcular cercania`.

## Carga real controlada

Usar la plantilla versionable:

```text
data/sample/precios_reales_template.csv
```

Completar una copia con precios reales y guardarla en `data/raw/precios_reales/manual/` o una carpeta local equivalente no versionada. Ejemplo de nombre:

```text
vea_capital_20260712_gondola.csv
```

Validar:

```bash
python scripts/09_validar_precios_reales.py --input data/sample/precios_reales_demo.csv
```

Salidas:

```text
data/processed/precios_reales_validados.csv
data/processed/reporte_validacion_precios_reales.csv
```

Integrar con el flujo existente:

```bash
python scripts/04_matching_productos.py --input data/processed/precios_reales_validados.csv --output data/processed/precios_reales_matcheados.csv --report data/processed/precios_reales_matcheados_reporte.json
python scripts/06_aplicar_promociones.py --prices data/processed/precios_reales_matcheados.csv --output data/processed/precios_reales_con_promociones.csv --report data/processed/precios_reales_promociones_reporte.json --date 2026-07-11
python scripts/05_calcular_lista_compra.py --prices data/processed/precios_reales_con_promociones.csv --comparison-output data/processed/comparacion_lista_reales.csv --best-output data/processed/mejor_compra_reales.csv --report data/processed/lista_reales_reporte.json
```

Guia operativa:

```text
docs/GUIA_CARGA_PRECIOS_REALES.md
```

Generar reportes de calidad operativa:

```bash
python scripts/10_generar_reporte_calidad_datos.py
```

Salidas:

```text
data/processed/reporte_calidad_datos.csv
data/processed/resumen_calidad_fuente.csv
```

Guias Sprint 11:

```text
docs/OPERACION_DIARIA_PRECIOS.md
docs/NAMING_CONVENTION.md
```

## Consolidacion diaria multiarchivo

Guardar los relevamientos reales fuera de Git usando esta estructura:

```text
data/raw/precios_reales/manual/{comercio}/{sucursal}/{YYYY-MM-DD}/
```

Probar el flujo reproducible de Sprint 12:

```bash
python scripts/11_consolidar_relevamientos.py --input data/sample/multifile
```

Para una operacion real, reemplazar `data/sample/multifile` por `data/raw/precios_reales/manual`. El comando genera:

```text
data/processed/precios_reales_consolidados.csv
data/processed/reporte_consolidacion.csv
data/processed/manifiesto_consolidacion.csv
```

Continuar con matching y calidad:

```bash
python scripts/04_matching_productos.py --input data/processed/precios_reales_consolidados.csv --output data/processed/precios_reales_consolidados_matcheados.csv
python scripts/10_generar_reporte_calidad_datos.py --prices data/processed/precios_reales_consolidados.csv --validation-report data/processed/reporte_consolidacion.csv
```

El dashboard carga `data/processed/precios_reales_consolidados_matcheados.csv` como cualquier archivo de precios matcheados. La clave de duplicado es `comercio + sucursal + producto + marca + presentacion + fecha_relevamiento`. La regla inicial conserva el registro del ultimo archivo procesado segun el orden lexicografico de su ruta relativa; el ganador conserva `archivo_origen` y queda marcado con `estado_registro = CONSOLIDADO_CONFLICTO` y `conflicto_detectado = SI`.

Para correcciones sucesivas usar prefijos ordenables `01_`, `02_`, `03_`: `01_` es la carga inicial, `02_` la primera correccion y `03_` una correccion posterior. Nunca sobrescribir el archivo previo.

## Estructura de carpetas

```text
dashboard/          Dashboard HTML standalone.
scripts/            Flujo local de procesamiento y release demo.
data/sample/        Datos demo versionables.
data/raw/           Datos crudos locales ignorados por Git.
data/processed/     Outputs generados ignorados por Git.
docs/               Documentacion tecnica, uso y release.
tests/              Pruebas automatizadas.
```

## Flujo completo MVP

El comando recomendado para generar todos los outputs demo es:

```bash
python scripts/08_generar_mvp_demo.py
```

Ese script ejecuta:

```text
scripts/02_normalizar_precios.py
scripts/01_descargar_o_importar_sepa.py --mode manual
scripts/03_filtrar_san_juan.py
scripts/04_matching_productos.py
scripts/06_aplicar_promociones.py --date 2026-07-11
scripts/05_calcular_lista_compra.py --prices data/processed/precios_con_promociones.csv
scripts/07_planificar_ruta.py
```

Outputs principales:

```text
data/processed/precios_normalizados.csv
data/processed/precios_san_juan_sepa.csv
data/processed/precios_matcheados.csv
data/processed/precios_con_promociones.csv
data/processed/comparacion_lista_compra.csv
data/processed/mejor_compra_por_producto.csv
data/processed/recomendacion_ruta.csv
data/processed/ruta_compra_dividida.csv
```

`2026-07-11` es la fecha estable de prueba para que las promociones demo sean reproducibles. Para otra fecha:

```bash
python scripts/08_generar_mvp_demo.py --date 2026-07-12
```

Validacion tecnica de release:

```bash
python -m compileall scripts
python scripts/08_generar_mvp_demo.py
python -m pytest
```

## Uso del dashboard

1. Servir el proyecto: `python -m http.server 8026 --bind 127.0.0.1`.
2. Abrir `http://127.0.0.1:8026/dashboard/`.
3. Usar la navegacion lateral: `Resumen`, `Datos y productos`, `Mi lista`, `Comparacion`, `Calidad` y `Ruta`.
4. Cargar `data/processed/precios_con_promociones.csv` en `CSV de precios`.
5. Cargar `data/sample/lista_compra_demo.csv` o armar una lista desde `Armar lista`.
6. Guardar o recuperar listas con los botones de `Lista actual`.
7. Presionar `Calcular ranking` o `Recalcular`.
8. Cargar `data/sample/sucursales_demo.csv`.
9. Cargar `data/sample/ubicacion_usuario_demo.csv` o ingresar coordenadas manuales.
10. Presionar `Calcular cercania`.
11. Revisar ranking por comercio, ahorro, faltantes, mejor compra dividida y score de conveniencia.

El dashboard muestra el estado de cada archivo cargado y permite `Limpiar sesion` para empezar de nuevo sin recargar la pagina.

La cabecera muestra un resumen ejecutivo con mejor comercio, costo, ahorro, cobertura, incidencias de calidad y recomendacion de ruta. Las acciones permanecen deshabilitadas hasta que existan los datos necesarios y `Limpiar sesion` solicita confirmacion.

## Limitaciones conocidas

- Los datos demo son ficticios/simulados y sirven para validar flujo, no para decision real.
- `data/raw/` puede recibir archivos manuales reales, pero esos archivos no se versionan.
- La distancia usa Haversine en linea recta; no calcula tiempos reales, calles, transito ni horarios.
- El matching es auditable y simple; puede requerir ampliar `data/sample/product_dictionary.csv`.
- Las promociones demo no reemplazan condiciones reales de cada cadena.
- No hay backend ni multiusuario; `localStorage` queda solo en el navegador local.
- La prioridad entre archivos duplicados depende del nombre/ruta: usar prefijos ordenables o el sufijo `_corregido` segun `docs/NAMING_CONVENTION.md`.

## Proximos pasos recomendados

- Incorporar fuentes oficiales/manuales reales por cadena y localidad.
- Agregar preferencia de usuario: maximo de paradas, medio de pago, distancia maxima y tolerancia a faltantes.
- Separar datos reales de datos demo con un procedimiento operativo diario.
- Evaluar una bandeja de revision manual para conflictos y precios sospechosos antes de publicar datos.
- Calibrar `costo_km_estimado` y validar coordenadas reales de sucursales.

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

Sprint 7 ruta/cercania:
data/processed/comparacion_lista_compra.csv + data/processed/mejor_compra_por_producto.csv
        + data/sample/sucursales_demo.csv + data/sample/ubicacion_usuario_demo.csv
        -> scripts/07_planificar_ruta.py
        -> data/processed/recomendacion_ruta.csv
        -> data/processed/ruta_compra_dividida.csv
        -> dashboard/index.html

Sprint 10 carga real controlada:
data/sample/precios_reales_template.csv o data/sample/precios_reales_demo.csv
        -> scripts/09_validar_precios_reales.py
        -> data/processed/precios_reales_validados.csv
        -> scripts/04_matching_productos.py --input data/processed/precios_reales_validados.csv
        -> dashboard/index.html

Sprint 11 calidad operativa:
data/processed/precios_reales_validados.csv + data/processed/reporte_validacion_precios_reales.csv
        -> scripts/10_generar_reporte_calidad_datos.py
        -> data/processed/reporte_calidad_datos.csv
        -> data/processed/resumen_calidad_fuente.csv
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

## Sprint 7: ruta y cercania

El modulo de ruta agrega una decision simple de conveniencia: combina costo total, cobertura de lista y distancia aproximada desde una ubicacion de usuario. No usa Google Maps API, servicios pagos ni credenciales.

Datos demo versionables:

```text
data/sample/sucursales_demo.csv
data/sample/ubicacion_usuario_demo.csv
```

Antes de planificar ruta, generar lista con precio efectivo:

```bash
python scripts/06_aplicar_promociones.py --date 2026-07-11
python scripts/05_calcular_lista_compra.py --prices data/processed/precios_con_promociones.csv
```

Generar recomendacion de ruta:

```bash
python scripts/07_planificar_ruta.py
```

Salidas esperadas:

```text
data/processed/recomendacion_ruta.csv
data/processed/ruta_compra_dividida.csv
data/processed/ruta_reporte.json
```

Regla de score inicial:

```text
score_conveniencia = costo_total_estimado + penalizacion_distancia
penalizacion_distancia = distancia_km * costo_km_estimado
```

El valor demo de `costo_km_estimado` es `180` pesos por km. Es configurable:

```bash
python scripts/07_planificar_ruta.py --costo-km-estimado 220
```

La distancia se calcula con Haversine, es decir, distancia aproximada en linea recta. No reemplaza navegacion real ni tiempos de transito.

Uso en dashboard:

1. Abrir `dashboard/index.html`.
2. Cargar `data/processed/precios_con_promociones.csv` o `data/processed/precios_matcheados.csv`.
3. Cargar o armar una lista.
4. Cargar `data/sample/sucursales_demo.csv`.
5. Cargar `data/sample/ubicacion_usuario_demo.csv` o ingresar latitud/longitud manual.
6. Presionar "Calcular cercania".
7. Revisar ranking por conveniencia y ruta dividida sugerida.

## Datos versionables

- `data/sample/precios_demo.csv`: demo Sprint 1.
- `data/sample/sepa/sepa_precios_simulado.csv`: fuente tipo SEPA simulada para pruebas reproducibles.
- `data/sample/product_dictionary.csv`: diccionario editable de equivalencias Sprint 3.
- `data/sample/lista_compra_demo.csv`: lista demo versionable Sprint 4.
- `data/sample/promociones_demo.csv`: promociones demo versionables Sprint 6.
- `data/sample/sucursales_demo.csv`: sucursales demo con coordenadas Sprint 7.
- `data/sample/ubicacion_usuario_demo.csv`: ubicacion de usuario demo Sprint 7.

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

Sprint 10: preparacion para datos reales operativos, fuentes oficiales/manuales por cadena, preferencias de usuario y calibracion de distancia/costo.

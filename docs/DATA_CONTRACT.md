# Contrato de datos

## Sprint 16 - Revision y dataset privado

La migracion `003_review_and_private_publication.sql` agrega contratos cloud
solo para el proyecto aislado `proyecto-super-staging`:

| Estructura | Identidad | Regla |
|---|---|---|
| `review_queue` | `id`, `idempotency_key` | incidencia humana por corrida/observacion; estados controlados y RLS |
| `review_decisions` | `id`, `idempotency_key` | auditoria append-only de accion, responsable, valor anterior y correccion |
| `dataset_approvals` | `scrape_run_id` unico | unica decision de dataset por corrida, idempotente |
| `operational_alerts` | `id`, `idempotency_key` | alerta operacional con severidad y acknowledgement |
| `private_datasets` | `id`, corrida + checksum | indice durable de manifiesto privado aprobado o dry run |

Estados de revision: `PENDING`, `IN_REVIEW`, `APPROVED`, `REJECTED`,
`CORRECTED`, `DISMISSED`.

Estados de aprobacion: `PENDING_REVIEW`, `READY_FOR_APPROVAL`, `APPROVED`,
`REJECTED`, `REVOKED`.

Un dataset privado solo se produce tras `APPROVED`. En dry run se genera un
manifiesto logico con checksum, pero no se escribe Storage. Si se habilita en
una futura ventana controlada, sus rutas son
`published/YYYY/MM/DD/run_id/precios_aprobados.csv` y
`published/YYYY/MM/DD/run_id/manifiesto.json`; el bucket sigue privado.

## Sprint 15 - Persistencia e idempotencia staging

- `execution_id` identifica el evento del orquestador y es unico.
- `run_id` es UUID deterministico derivado de `execution_id`; sobrevive a
  reintentos y reinicios.
- `trigger_type=manual_staging` se acepta en API. Para mantener inmutable la
  restriccion de `001`, se persiste como `trigger_type=manual` y
  `trigger_context=manual_staging`, agregado por `002`.
- `raw_hash` se calcula sin timestamp de extraccion para que un reintento del
  mismo contenido conserve identidad. La unicidad es `(run_id, raw_hash)`.
- `app_env=staging` distingue las corridas y `updated_at` registra cambios.
- Eventos repetidos se deduplican por `(execution_id, event_type, status)`.
- `dry_run=true` permite guardar trazabilidad privada en staging, pero nunca
  escribir un dataset publicado.

## Sprint 14 - Observacion cloud oficial

Cada adaptador cloud intenta producir:

| Columna | Regla |
|---|---|
| `comercio`, `sucursal`, `localidad` | identidad declarada; no inferir sucursal fisica |
| `canal_precio` | `ONLINE`, `TIENDA_FISICA`, `CATALOGO`, `MANUAL` o `CONTROL` |
| `producto`, `marca`, `categoria`, `presentacion` | descripcion normalizada y trazable |
| `sku`, `ean` | identificadores oficiales si estan publicados |
| `precio_regular`, `precio_promocional`, `precio_efectivo` | numeros positivos; no mezclar condiciones |
| `condicion_promocion`, `medio_pago` | texto oficial o vacio; no inferir |
| `stock_publicado` | valor expuesto por canal; no garantiza gondola |
| `fecha_hora_extraccion` | ISO 8601 UTC |
| `url_origen`, `archivo_origen`, `extractor_version` | trazabilidad |
| `raw_hash` | SHA-256 para idempotencia dentro de la corrida |

El pipeline agrega `precio`, `fecha_relevamiento`, `fuente` y `quality_status`, manteniendo las columnas canonicas del MVP. Para Vea Sprint 14: `canal_precio=ONLINE`, `sucursal=Online nacional`; no equivale a precio de tienda fisica San Juan.

Actualizado: 2026-07-12.

## Columnas canonicas del dashboard

El dashboard standalone `dashboard/index.html` valida estas columnas minimas:

| Columna | Tipo esperado | Regla |
|---|---|---|
| `comercio` | texto | obligatorio |
| `sucursal` | texto | obligatorio |
| `localidad` | texto | obligatorio |
| `producto` | texto | obligatorio |
| `marca` | texto | puede estar vacio |
| `categoria` | texto | obligatorio |
| `presentacion` | texto | obligatorio |
| `precio` | numero/texto numerico | obligatorio, mayor a cero |
| `fecha_relevamiento` | fecha | ISO `YYYY-MM-DD` recomendado |
| `fuente` | texto | obligatorio |

## Sprint 1: CSV demo

Entrada versionable:

```text
data/sample/precios_demo.csv
```

Normalizador:

```text
scripts/02_normalizar_precios.py
```

Salida generada:

```text
data/processed/precios_normalizados.csv
```

Columnas generadas por Sprint 1:

- `comercio`
- `comercio_limpio`
- `sucursal`
- `sucursal_limpia`
- `localidad`
- `producto`
- `producto_limpio`
- `marca`
- `marca_limpia`
- `categoria`
- `categoria_limpia`
- `presentacion`
- `precio`
- `fecha_relevamiento`
- `fuente`

## Sprint 2: SEPA/manual

Entrada versionable de prueba:

```text
data/sample/sepa/sepa_precios_simulado.csv
```

Entrada manual real o semirreal ignorada por Git:

```text
data/raw/sepa/manual/*.csv
data/raw/sepa/manual/*.zip
```

Scripts:

```text
scripts/01_descargar_o_importar_sepa.py
scripts/03_filtrar_san_juan.py
```

Salida generada compatible con dashboard:

```text
data/processed/precios_san_juan_sepa.csv
```

Columnas generadas:

- `comercio`
- `sucursal`
- `localidad`
- `producto`
- `marca`
- `categoria`
- `presentacion`
- `precio`
- `fecha_relevamiento`
- `fuente`

## Mapeo SEPA a contrato normalizado

| Campo normalizado | Campos SEPA o aliases aceptados | Regla |
|---|---|---|
| `comercio` | `comercio_bandera_nombre`, `bandera_descripcion`, `comercio`, `cadena`, `nombre_comercio`, `comercio_razon_social` | prioriza bandera/nombre comercial |
| `sucursal` | `sucursales_nombre`, `sucursal_nombre`, `sucursal`, `nombre_sucursal`, `direccion`, `domicilio`, `id_sucursal` | texto visible de sucursal |
| `localidad` | `sucursales_localidad`, `localidad`, `ciudad`, `municipio`, `departamento` | usada para filtro San Juan |
| `producto` | `productos_descripcion`, `producto_nombre`, `nombre_producto`, `producto_descripcion`, `descripcion`, `producto` | descripcion comercial |
| `marca` | `productos_marca`, `marca`, `marca_nombre` | se permite vacio |
| `categoria` | `categoria`, `rubro`, `familia`, `clase` | si falta, usa `Sin categoria` |
| `presentacion` | `presentacion`, `productos_cantidad_presentacion` + `productos_unidad_medida_presentacion`, `cantidad_presentacion`, `unidad_presentacion` | si falta, intenta inferir desde producto |
| `precio` | `productos_precio_lista`, `precio`, `precio_lista`, `precio_venta`, `precio_unitario` | numerico mayor a cero |
| `fecha_relevamiento` | `fecha_relevamiento`, `fecha`, `fecha_precio`, `fecha_vigencia`, `capture_date`, fallback del script | ISO `YYYY-MM-DD` |
| `fuente` | `fuente`, `source`, `origen`, fallback `sepa_manual` | identifica origen |

Campos usados para unir paquetes SEPA separados:

- `id_comercio`
- `id_bandera`
- `id_sucursal`
- `id_producto`

Campos usados para provincia:

- `sucursales_provincia`
- `provincia`
- `provincia_nombre`
- `id_provincia`
- `cod_provincia`

Valores aceptados para San Juan:

- `AR-J`
- `San Juan`
- `J`
- `70`

Localidades prioritarias:

- Capital
- Rawson
- Santa Lucia
- Rivadavia

## Reglas de calidad

Precio valido:

- Debe convertirse a numero.
- Debe ser mayor a cero.
- Se guarda con dos decimales.

Fecha valida:

- Se acepta `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY` y `YYYYMMDD`.
- Se guarda como ISO `YYYY-MM-DD`.

Columnas/campos minimos Sprint 2:

- producto
- precio
- comercio
- sucursal
- localidad

Fila invalida:

- Se excluye de la salida.
- Se informa en `data/processed/precios_san_juan_sepa_errores.csv` cuando corresponde.
- El resumen queda en `data/processed/precios_san_juan_sepa_reporte.json`.

## Ejemplo salida compatible

```csv
comercio,sucursal,localidad,producto,marca,categoria,presentacion,precio,fecha_relevamiento,fuente
Vea,Capital Centro,Capital,Yerba mate suave,Playadito,Almacen,1 kg,3490.00,2026-07-09,sepa_simulado
```

## Sprint 3: matching de productos

Entrada esperada:

```text
data/processed/precios_san_juan_sepa.csv
```

Diccionario editable:

```text
data/sample/product_dictionary.csv
```

Salida generada:

```text
data/processed/precios_matcheados.csv
```

Columnas nuevas:

| Columna | Tipo esperado | Regla |
|---|---|---|
| `producto_normalizado` | texto | nombre canonico para comparar |
| `marca_normalizada` | texto | marca en minusculas, sin tildes |
| `categoria_normalizada` | texto | categoria en minusculas, sin tildes |
| `presentacion_normalizada` | texto | cantidad y unidad base |
| `cantidad_base` | numero | cantidad comparable |
| `unidad_base` | texto | `kg`, `l` o `un` |
| `precio_unitario_comparable` | numero | `precio / cantidad_base` |
| `grupo_comparacion` | texto | identificador estable del grupo equivalente |
| `confianza_matching` | numero | 0 a 1, mayor es mas confiable |

El dashboard debe seguir aceptando CSVs Sprint 1/Sprint 2. Si detecta columnas Sprint 3, ordena por `precio_unitario_comparable` y muestra `grupo_comparacion` y `confianza_matching`.

## Diccionario de productos

Columnas:

- `producto_original`
- `producto_normalizado`
- `categoria_normalizada`
- `marca_normalizada`
- `unidad_base`
- `cantidad_base`
- `grupo_comparacion`

Ejemplo:

```csv
producto_original,producto_normalizado,categoria_normalizada,marca_normalizada,unidad_base,cantidad_base,grupo_comparacion
yerba mate,yerba mate suave,almacen,playadito,kg,1,yerba_mate_playadito_1kg
```

## Normalizacion Sprint 3

Reglas cubiertas:

- minusculas/mayusculas;
- tildes;
- espacios extra;
- simbolos innecesarios;
- `kg`, `kilo`, `kilos`, `1000 g`;
- `g`, `gr`, `gramos`;
- `l`, `litro`, `litros`, `1000 ml`;
- `ml`, `cc`;
- `x`, `por`, `pack`.

Precio comparable:

- peso: precio por `kg`;
- volumen: precio por `l`;
- unidades o packs: precio por `un`.

## Sprint 4: listas de compra

Entrada de precios:

```text
data/processed/precios_matcheados.csv
```

Entrada de lista demo versionable:

```text
data/sample/lista_compra_demo.csv
```

Script:

```text
scripts/05_calcular_lista_compra.py
```

Salidas generadas:

```text
data/processed/comparacion_lista_compra.csv
data/processed/mejor_compra_por_producto.csv
data/processed/lista_compra_reporte.json
```

### Lista de compra

Columnas minimas:

| Columna | Tipo esperado | Regla |
|---|---|---|
| `item_lista` | texto | texto visible cargado por el usuario |
| `grupo_comparacion` | texto | debe existir en `precios_matcheados.csv` para comparar |
| `cantidad` | numero/texto numerico | mayor a cero |
| `unidad` | texto | `kg`, `g`, `l`, `ml`, `cc`, `un` y aliases |
| `prioridad` | texto | valor informativo para futuras reglas |

Regla de cantidad:

- `g` se convierte a `kg`.
- `ml` y `cc` se convierten a `l`.
- `kg`, `l` y `un` quedan como unidad base.

Ejemplo:

```csv
item_lista,grupo_comparacion,cantidad,unidad,prioridad
Fideos spaghetti 500g,fideos_spaghetti_matarazzo_500g,500,g,media
```

### Comparacion por comercio

Archivo:

```text
data/processed/comparacion_lista_compra.csv
```

Columnas:

| Columna | Tipo esperado | Regla |
|---|---|---|
| `comercio` | texto | comercio comparado |
| `productos_encontrados` | entero | cantidad de items de lista con oferta comparable |
| `productos_faltantes` | texto | `0` o detalle separado por punto y coma |
| `cobertura_lista_pct` | numero | porcentaje de items encontrados |
| `costo_total_estimado` | numero | suma del menor costo por grupo dentro del comercio; usa `precio_efectivo` cuando existe |
| `diferencia_vs_mas_barato` | numero/vacio | diferencia contra el comercio mas barato con la mayor cobertura |
| `ahorro_vs_mas_caro` | numero/vacio | ahorro contra el comercio mas caro con la mayor cobertura |
| `ranking_precio` | entero | orden final, prioriza cobertura y luego precio |

### Mejor compra por producto

Archivo:

```text
data/processed/mejor_compra_por_producto.csv
```

Columnas:

| Columna | Tipo esperado | Regla |
|---|---|---|
| `item_lista` | texto | item original de la lista |
| `grupo_comparacion` | texto | grupo usado para comparar |
| `comercio_recomendado` | texto | comercio con menor costo para ese item |
| `producto_encontrado` | texto | producto real tomado del CSV de precios |
| `precio_final` | numero/vacio | costo estimado para la cantidad pedida |
| `precio_unitario_comparable` | numero/vacio | precio por unidad base del producto elegido |
| `ahorro_vs_promedio` | numero/vacio | diferencia contra el promedio de ofertas encontradas |
| `confianza_matching` | numero/vacio | confianza heredada del matching Sprint 3 |

## Sprint 5: lista visual y persistencia local

El dashboard no cambia el contrato de salida del script. La mejora esta en la interfaz:

- permite crear y editar listas desde `dashboard/index.html`;
- usa `grupo_comparacion` desde `precios_matcheados.csv`;
- guarda la lista en `localStorage`;
- exporta CSV compatible con `scripts/05_calcular_lista_compra.py`;
- sigue aceptando `data/sample/lista_compra_demo.csv`.

### CSV exportado desde dashboard

El boton `Exportar CSV` genera las mismas columnas minimas del Sprint 4:

```csv
item_lista,grupo_comparacion,cantidad,unidad,prioridad
```

Reglas:

- `cantidad` se exporta como numero en unidad base.
- `unidad` se exporta como `kg`, `l` o `un`.
- `grupo_comparacion` debe coincidir con un grupo presente en `precios_matcheados.csv`.

### localStorage

Clave:

```text
proyecto-super-lista-compra-v1
```

Estructura guardada:

```json
[
  {
    "item_lista": "Yerba Playadito 1 kg",
    "grupo_comparacion": "yerba_mate_playadito_1kg",
    "cantidad": 1,
    "unidad": "kg",
    "prioridad": "alta"
  }
]
```

La persistencia es local al navegador del usuario. No se envia informacion a ningun backend.

## Sprint 6: promociones y precio efectivo

Entrada de precios:

```text
data/processed/precios_matcheados.csv
```

Entrada demo versionable:

```text
data/sample/promociones_demo.csv
```

Script:

```text
scripts/06_aplicar_promociones.py
```

Salida generada:

```text
data/processed/precios_con_promociones.csv
data/processed/precios_con_promociones_reporte.json
```

### Promociones

Columnas minimas de `data/sample/promociones_demo.csv`:

| Columna | Tipo esperado | Regla |
|---|---|---|
| `promo_id` | texto | identificador estable de la promocion |
| `comercio` | texto | comercio objetivo; vacio aplica a todos |
| `grupo_comparacion` | texto | grupo objetivo; vacio aplica a todo el comercio |
| `tipo_promocion` | texto | `descuento_porcentaje`, `descuento_monto_fijo`, `segunda_unidad`, `precio_especial`, `descuento_medio_pago` |
| `descripcion` | texto | texto visible para dashboard |
| `descuento_pct` | numero/vacio | porcentaje de descuento |
| `descuento_monto` | numero/vacio | monto fijo o precio especial final segun tipo |
| `tope_descuento` | numero/vacio | maximo descuento por fila; `0` o vacio sin tope |
| `medio_pago` | texto/vacio | medio de pago requerido o sugerido |
| `dia_semana` | texto/vacio | `todos` o dia especifico |
| `fecha_inicio` | fecha | ISO `YYYY-MM-DD` recomendado |
| `fecha_fin` | fecha | ISO `YYYY-MM-DD` recomendado |
| `acumulable` | texto | `si` o `no` |
| `prioridad` | entero | menor numero se aplica primero en acumulables |

### Reglas Sprint 6

- Promocion por comercio completo: `comercio` con `grupo_comparacion` vacio.
- Promocion por producto comparable: `grupo_comparacion` informado.
- Promocion por medio de pago: `medio_pago` informado.
- Vigencia: `fecha_inicio`, `fecha_fin` y `dia_semana`.
- `scripts/06_aplicar_promociones.py --date YYYY-MM-DD` evalua vigencia con fecha explicita.
- Si se omite `--date`, el script evalua vigencia con la fecha actual del sistema.
- Si `acumulable = no`, se aplica solo la promocion de mayor ahorro.
- Si `acumulable = si`, se aplican promociones acumulables por prioridad ascendente, respetando topes.
- `segunda_unidad` se calcula como descuento promedio por unidad. Ejemplo: segunda al 50% equivale a 25% por unidad.
- `precio_especial` interpreta `descuento_monto` como precio final especial.

### Salida con promociones

Columnas nuevas en `data/processed/precios_con_promociones.csv`:

| Columna | Tipo esperado | Regla |
|---|---|---|
| `precio_original` | numero | precio de gondola original |
| `precio_efectivo` | numero | precio final luego de promociones aplicables |
| `ahorro_promocion` | numero | diferencia entre original y efectivo |
| `promo_id_aplicada` | texto/vacio | promo aplicada o promos acumuladas separadas por `+` |
| `promo_aplicada` | texto/vacio | descripcion visible de la promo |
| `medio_pago_promocion` | texto/vacio | medio de pago asociado cuando corresponda |
| `precio_unitario_efectivo` | numero | `precio_efectivo / cantidad_base` |

### Compatibilidad con lista y dashboard

`scripts/05_calcular_lista_compra.py` acepta:

- `data/processed/precios_matcheados.csv`: usa `precio` y `precio_unitario_comparable`.
- `data/processed/precios_con_promociones.csv`: usa `precio_efectivo` y `precio_unitario_efectivo`.

`dashboard/index.html` detecta automaticamente si el CSV tiene columnas de promociones. En ese caso muestra precio original, precio efectivo, ahorro y descripcion de promocion, y calcula el ranking con precio efectivo.

## Sprint 7: ruta y cercania

Entradas generadas esperadas:

```text
data/processed/comparacion_lista_compra.csv
data/processed/mejor_compra_por_producto.csv
```

Entradas demo versionables:

```text
data/sample/sucursales_demo.csv
data/sample/ubicacion_usuario_demo.csv
```

Script:

```text
scripts/07_planificar_ruta.py
```

Salidas generadas:

```text
data/processed/recomendacion_ruta.csv
data/processed/ruta_compra_dividida.csv
data/processed/ruta_reporte.json
```

### Sucursales

Columnas minimas de `data/sample/sucursales_demo.csv`:

| Columna | Tipo esperado | Regla |
|---|---|---|
| `comercio` | texto | debe coincidir con `comercio` de los precios/lista |
| `sucursal` | texto | nombre visible de sucursal |
| `localidad` | texto | Capital, Rawson, Santa Lucia, Rivadavia u otra |
| `direccion` | texto | referencia visible |
| `latitud` | numero | coordenada decimal |
| `longitud` | numero | coordenada decimal |
| `zona` | texto | etiqueta operativa |
| `horario_referencia` | texto | dato informativo |

### Ubicacion usuario

Columnas minimas de `data/sample/ubicacion_usuario_demo.csv`:

| Columna | Tipo esperado | Regla |
|---|---|---|
| `nombre_ubicacion` | texto | etiqueta visible |
| `latitud` | numero | coordenada decimal |
| `longitud` | numero | coordenada decimal |
| `localidad` | texto | localidad de referencia |
| `descripcion` | texto | detalle informativo |

El dashboard tambien permite ingresar latitud y longitud manuales. Si se cargan coordenadas manuales, tienen prioridad sobre el CSV de ubicacion.

### Recomendacion ruta

Archivo:

```text
data/processed/recomendacion_ruta.csv
```

Columnas:

| Columna | Tipo esperado | Regla |
|---|---|---|
| `comercio` | texto | comercio evaluado |
| `sucursal` | texto | sucursal evaluada |
| `localidad` | texto | localidad de la sucursal |
| `costo_total_estimado` | numero | costo de lista por comercio |
| `ahorro_vs_mas_caro` | numero/vacio | ahorro informado por Sprint 4/6 |
| `cobertura_lista_pct` | numero | cobertura de lista |
| `distancia_km` | numero | distancia Haversine aproximada |
| `penalizacion_distancia` | numero | `distancia_km * costo_km_estimado` |
| `score_conveniencia` | numero | `costo_total_estimado + penalizacion_distancia` |
| `recomendacion` | texto | recomendacion legible |

Regla inicial:

```text
score_conveniencia = costo_total_estimado + penalizacion_distancia
penalizacion_distancia = distancia_km * costo_km_estimado
```

Valor demo:

```text
costo_km_estimado = 180
```

La distancia usa Haversine en linea recta. Es aproximada y no reemplaza navegacion real.

### Ruta compra dividida

Archivo:

```text
data/processed/ruta_compra_dividida.csv
```

Columnas:

| Columna | Tipo esperado | Regla |
|---|---|---|
| `orden_sugerido` | entero | orden de visita sugerido |
| `comercio` | texto | comercio recomendado para esos productos |
| `sucursal` | texto | sucursal elegida por cercania aproximada |
| `localidad` | texto | localidad de la sucursal |
| `productos_a_comprar` | texto | items agrupados separados por punto y coma |
| `costo_estimado` | numero | suma de `precio_final` para esos items |
| `distancia_desde_origen_km` | numero | distancia directa desde ubicacion de usuario |
| `distancia_acumulada_km` | numero | distancia acumulada en la ruta sugerida |
| `ahorro_estimado` | numero | suma de ahorro contra promedio de compra dividida |

El orden de ruta dividida usa una heuristica simple de vecino mas cercano entre comercios recomendados. No optimiza transito, sentidos de calle ni horarios.

## Sprint 8: release MVP v1.0

Script orquestador:

```text
scripts/08_generar_mvp_demo.py
```

El script no crea un contrato nuevo; ejecuta el flujo completo con los contratos ya definidos:

```text
precios_demo.csv
sepa_precios_simulado.csv
precios_san_juan_sepa.csv
precios_matcheados.csv
precios_con_promociones.csv
comparacion_lista_compra.csv
mejor_compra_por_producto.csv
recomendacion_ruta.csv
ruta_compra_dividida.csv
```

Fecha demo por defecto:

```text
2026-07-11
```

Esa fecha se usa solo para que las promociones demo sean reproducibles. Puede cambiarse con:

```bash
python scripts/08_generar_mvp_demo.py --date YYYY-MM-DD
```

Archivos que una persona debe cargar en el dashboard para validar el MVP completo:

```text
data/processed/precios_con_promociones.csv
data/sample/lista_compra_demo.csv
data/sample/sucursales_demo.csv
data/sample/ubicacion_usuario_demo.csv
```

Los outputs de `data/processed/` siguen siendo generados y no versionables. Los inputs de `data/sample/` son demo versionables.

## Sprint 10: carga real controlada

Plantilla versionable:

```text
data/sample/precios_reales_template.csv
```

Demo versionable con errores controlados:

```text
data/sample/precios_reales_demo.csv
```

Validador:

```text
scripts/09_validar_precios_reales.py
```

Salidas generadas:

```text
data/processed/precios_reales_validados.csv
data/processed/reporte_validacion_precios_reales.csv
```

### Columnas de entrada real/manual

| Columna | Tipo esperado | Regla |
|---|---|---|
| `comercio` | texto | obligatorio |
| `sucursal` | texto | obligatorio |
| `localidad` | texto | obligatorio; alcance inicial `Capital`, `Rawson`, `Santa Lucia`, `Rivadavia` |
| `direccion` | texto | referencia de sucursal |
| `producto` | texto | obligatorio |
| `marca` | texto | puede estar vacio |
| `categoria` | texto | obligatorio |
| `presentacion` | texto | obligatorio |
| `precio` | numero/texto numerico | obligatorio, mayor a cero |
| `fecha_relevamiento` | fecha | `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY` o `YYYYMMDD` |
| `fuente` | texto | `manual_gondola`, `manual_ticket`, `web_oficial` u origen equivalente |
| `observacion` | texto | opcional |

### Salida validada

`precios_reales_validados.csv` conserva las columnas canonicas del dashboard y agrega trazabilidad:

- `comercio`
- `sucursal`
- `localidad`
- `producto`
- `marca`
- `categoria`
- `presentacion`
- `precio`
- `fecha_relevamiento`
- `fuente`
- `direccion`
- `observacion`

Las 10 primeras columnas canonicas son compatibles con:

- `scripts/04_matching_productos.py --input data/processed/precios_reales_validados.csv`
- `scripts/06_aplicar_promociones.py --prices ...`
- `scripts/05_calcular_lista_compra.py --prices ...`
- `dashboard/index.html`

### Reporte de validacion

`reporte_validacion_precios_reales.csv` usa:

| Columna | Regla |
|---|---|
| `fila` | numero de linea CSV, contando encabezado |
| `campo` | campo afectado |
| `tipo_error` | `columna_faltante`, `campo_obligatorio`, `precio_invalido`, `fecha_invalida`, `localidad_fuera_alcance`, `duplicado`, `precio_sospechoso` |
| `valor_detectado` | valor original detectado |
| `sugerencia` | accion recomendada |

Las filas con errores fatales se excluyen. `precio_sospechoso` se reporta como alerta y la fila se conserva para revision operativa.

## Sprint 11: calidad operativa diaria

Entradas generadas:

```text
data/processed/precios_reales_validados.csv
data/processed/reporte_validacion_precios_reales.csv
```

Script:

```text
scripts/10_generar_reporte_calidad_datos.py
```

Salidas:

```text
data/processed/reporte_calidad_datos.csv
data/processed/resumen_calidad_fuente.csv
```

### Estructura operativa raw

Los archivos reales crudos deben guardarse fuera de Git:

```text
data/raw/precios_reales/manual/{comercio}/{sucursal}/{YYYY-MM-DD}/
```

Convencion:

```text
precios_{comercio}_{sucursal}_{localidad}_{YYYY-MM-DD}_{fuente}.csv
```

### reporte_calidad_datos.csv

| Columna | Regla |
|---|---|
| `archivo_origen` | archivo validado evaluado |
| `comercio` | comercio evaluado |
| `sucursal` | sucursal evaluada |
| `localidad` | localidad de la sucursal |
| `total_filas` | filas validas + filas observadas con incidencia |
| `filas_validas` | filas presentes en `precios_reales_validados.csv` |
| `filas_invalidas` | filas con incidencias no sospechosas |
| `incidencias` | cantidad total de incidencias asignadas |
| `duplicados` | incidencias `duplicado` |
| `precios_sospechosos` | incidencias `precio_sospechoso` |
| `fecha_min` | menor fecha valida del grupo |
| `fecha_max` | mayor fecha valida del grupo |
| `antiguedad_dias` | dias desde `fecha_max` hasta la fecha de calculo |
| `estado_calidad` | `OK`, `REVISAR`, `INVALIDO`, `DESACTUALIZADO` |

### resumen_calidad_fuente.csv

| Columna | Regla |
|---|---|
| `comercio` | comercio evaluado |
| `sucursal` | sucursal evaluada |
| `localidad` | localidad |
| `productos_validos` | productos validos unicos |
| `categorias_cubiertas` | categorias unicas |
| `ultima_fecha_relevamiento` | mayor fecha valida |
| `antiguedad_dias` | dias desde ultima fecha |
| `score_calidad` | 0 a 100 |
| `estado_operativo` | estado operativo equivalente a calidad |

### Estados

- `OK`: sin errores fatales y antiguedad menor o igual a 7 dias.
- `REVISAR`: tiene duplicados o precios sospechosos.
- `INVALIDO`: tiene errores fatales relevantes.
- `DESACTUALIZADO`: antiguedad mayor a 7 dias.

## Sprint 12: consolidacion multiarchivo diaria

Entrada:

```text
data/raw/precios_reales/manual/{comercio}/{sucursal}/{YYYY-MM-DD}/*.csv
```

El sample reproducible equivalente esta en `data/sample/multifile/`. Todos los CSV deben cumplir las 12 columnas de entrada real/manual de Sprint 10, aunque pueden presentarlas en distinto orden.

### precios_reales_consolidados.csv

Conserva `fila_origen` y las 12 columnas de la salida validada, y agrega:

| Columna | Regla |
|---|---|
| `archivo_origen` | ruta relativa del CSV dentro de la carpeta de entrada |
| `fecha_procesamiento` | fecha/hora ISO 8601 de la ejecucion |
| `estado_registro` | `VALIDO` o `CONSOLIDADO_CONFLICTO` |
| `conflicto_detectado` | `SI` si el registro reemplazo un duplicado de otro archivo; `NO` en otro caso |

La clave de duplicado entre archivos es `comercio + sucursal + producto + marca + presentacion + fecha_relevamiento`, normalizada sin distinguir mayusculas ni tildes. El ultimo archivo segun orden lexicografico de ruta relativa reemplaza al anterior.

### reporte_consolidacion.csv

| Columna | Regla |
|---|---|
| `archivo_origen` | ruta relativa procesada |
| `filas_leidas` | filas de datos del CSV |
| `filas_validas` | filas aceptadas por el validador individual |
| `filas_invalidas` | filas excluidas por errores fatales, incluidos duplicados internos |
| `duplicados_internos` | repeticiones detectadas dentro del mismo CSV |
| `duplicados_entre_archivos` | registros reemplazados por conflicto con un archivo previo |
| `precios_sospechosos` | alertas de rango; la fila se conserva |
| `estado_archivo` | `OK`, `REVISAR` o `INVALIDO` |
| `mensaje` | resumen legible de incidencias |
| `comercio`, `sucursal`, `localidad` | contexto adicional para integrar calidad de datos |

### manifiesto_consolidacion.csv

Incluye `ejecucion_id`, `fecha_hora`, `carpeta_origen`, `archivos_procesados`, `filas_totales`, `filas_consolidadas`, `incidencias_totales` y `resultado`.

`precios_reales_consolidados.csv` es compatible como entrada de matching. `reporte_consolidacion.csv` es aceptado por `scripts/10_generar_reporte_calidad_datos.py` como alternativa al reporte fila por fila de Sprint 10.

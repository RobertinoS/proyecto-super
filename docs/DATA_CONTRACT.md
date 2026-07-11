# Contrato de datos

Actualizado: 2026-07-11.

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

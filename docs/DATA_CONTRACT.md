# Contrato de datos

Actualizado: 2026-07-09.

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

# Contrato de datos - Sprint 1

## Archivo sample

Ruta:

```text
data/sample/precios_demo.csv
```

Columnas obligatorias:

| Columna | Tipo esperado | Regla |
|---|---|---|
| `comercio` | texto | obligatorio |
| `sucursal` | texto | obligatorio |
| `localidad` | texto | obligatorio |
| `producto` | texto | obligatorio |
| `marca` | texto | puede estar vacio, pero se normaliza |
| `categoria` | texto | obligatorio |
| `presentacion` | texto | obligatorio |
| `precio` | numero/texto numerico | obligatorio, mayor a cero |
| `fecha_relevamiento` | fecha | `YYYY-MM-DD`, `DD/MM/YYYY` o `DD-MM-YYYY` |
| `fuente` | texto | obligatorio |

## Archivo normalizado generado

Ruta:

```text
data/processed/precios_normalizados.csv
```

Columnas generadas:

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

## Reglas de calidad

Precio valido:

- Debe convertirse a numero.
- Debe ser mayor a cero.
- Se guarda con dos decimales.

Fecha valida:

- Debe convertirse a ISO `YYYY-MM-DD`.

Texto limpio:

- Minusculas.
- Sin acentos.
- Sin simbolos innecesarios.
- Espacios normalizados.

Fila invalida:

- Se excluye de `precios_normalizados.csv`.
- Se informa por consola.
- Si hay errores, se genera `data/processed/precios_normalizados_errores.csv`.

## Ejemplo raw

```csv
comercio,sucursal,localidad,producto,marca,categoria,presentacion,precio,fecha_relevamiento,fuente
Vea,Capital Centro,Capital,Yerba mate suave,Playadito,Almacen,1 kg,3490.00,2026-07-09,csv_demo_local
```

## Ejemplo normalizado

```csv
comercio,comercio_limpio,sucursal,sucursal_limpia,localidad,producto,producto_limpio,marca,marca_limpia,categoria,categoria_limpia,presentacion,precio,fecha_relevamiento,fuente
Vea,vea,Capital Centro,capital centro,Capital,Yerba mate suave,yerba mate suave,Playadito,playadito,Almacen,almacen,1 kg,3490.00,2026-07-09,csv_demo_local
```

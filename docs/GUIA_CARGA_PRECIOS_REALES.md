# Guia de carga de precios reales

Sprint 10 agrega una operacion real controlada para cargar precios manuales o semimanuales sin scraping automatico, sin backend y sin credenciales.

## Archivo recomendado

Usar como base:

```text
data/sample/precios_reales_template.csv
```

Guardar cada relevamiento real fuera de `data/sample/`, por ejemplo en:

```text
data/raw/precios_reales/manual/vea_capital_20260712_gondola.csv
data/raw/precios_reales/manual/carrefour_rawson_20260712_ticket.csv
```

`data/raw/` esta ignorado por Git para evitar versionar datos crudos reales.

## Columnas

- `comercio`: nombre comercial visible, por ejemplo `Vea`.
- `sucursal`: nombre o referencia de sucursal, por ejemplo `Av Libertador`.
- `localidad`: `Capital`, `Rawson`, `Santa Lucia` o `Rivadavia` en esta etapa.
- `direccion`: direccion o referencia de la sucursal.
- `producto`: descripcion tal como aparece en ticket, gondola o web.
- `marca`: marca visible; puede quedar vacia si no figura.
- `categoria`: rubro simple, por ejemplo `Almacen`, `Lacteos`, `Bebidas`.
- `presentacion`: cantidad comercial, por ejemplo `1 kg`, `900 ml`, `4 un`.
- `precio`: precio final de gondola o publicado, sin descuento de tarjeta salvo que sea el precio informado.
- `fecha_relevamiento`: fecha del dato, ideal `YYYY-MM-DD`.
- `fuente`: origen del dato, por ejemplo `manual_gondola`, `manual_ticket`, `web_oficial`.
- `observacion`: aclaracion breve opcional.

## Ejemplos validos

```csv
comercio,sucursal,localidad,direccion,producto,marca,categoria,presentacion,precio,fecha_relevamiento,fuente,observacion
Vea,Av Libertador,Capital,Av. Libertador 1250,Yerba Mate Playadito 1 kg,Playadito,Almacen,1 kg,3290,2026-07-12,manual_gondola,precio visto en gondola
Carrefour,Hiper Rawson,Rawson,Av. Mendoza Sur 410,Aceite Girasol Natura 900 ml,Natura,Almacen,900 ml,2650,2026-07-12,manual_ticket,ticket de compra
```

## Fuentes aceptadas

- Ticket propio: cargar precio, fecha y comercio/sucursal del ticket.
- Gondola: cargar precio observado, fecha y direccion/sucursal.
- Web oficial: cargar precio publicado por la cadena e indicar `web_oficial`.
- Relevamiento manual: cargar solo productos vistos y verificables.

## Errores comunes

- Precio con texto, por ejemplo `abc`.
- Fecha inexistente, por ejemplo `31/02/2026`.
- Localidad fuera del alcance inicial, por ejemplo `Mendoza`.
- Producto duplicado en la misma sucursal, fecha, marca y presentacion.
- Precio demasiado bajo o alto para ser razonable.
- Mezclar promociones de tarjeta dentro de `precio`; esas condiciones deben cargarse luego como promociones.

## Datos que no ingresar

- Datos personales de clientes, tarjetas, telefonos o documentos.
- Fotos, links privados, credenciales o tokens.
- Informacion que no pueda trazarse a ticket, gondola, web oficial o relevamiento.
- Archivos grandes o crudos reales dentro de `data/sample/`.

## Validar una carga

Desde:

```text
C:\Users\Rober\Desktop\Proyecto Super
```

Ejecutar:

```bash
python scripts/09_validar_precios_reales.py --input data/raw/precios_reales/manual/archivo_real.csv
```

Salidas:

```text
data/processed/precios_reales_validados.csv
data/processed/reporte_validacion_precios_reales.csv
```

El archivo validado queda listo para matching:

```bash
python scripts/04_matching_productos.py --input data/processed/precios_reales_validados.csv --output data/processed/precios_reales_matcheados.csv
```

Luego se puede cargar `data/processed/precios_reales_matcheados.csv` en el dashboard.

## Trazabilidad

Mantener una convencion de nombres:

```text
comercio_localidad_fecha_fuente.csv
```

Ejemplos:

```text
vea_capital_20260712_gondola.csv
carrefour_rawson_20260712_ticket.csv
changomas_capital_20260712_web.csv
```

Conservar el reporte de validacion para revisar que filas se excluyeron o quedaron como alerta.

# Guia de uso MVP v1.0

Esta guia explica como usar el MVP local del Proyecto Super San Juan sin tocar codigo.

## 1. Generar datos demo

Abrir una terminal en:

```text
C:\Users\Rober\Desktop\Proyecto Super
```

Ejecutar:

```bash
python scripts/08_generar_mvp_demo.py
```

Esto genera los CSV necesarios en `data/processed/`.

## 2. Abrir dashboard

En la misma carpeta ejecutar:

```bash
python -m http.server 8026 --bind 127.0.0.1
```

Abrir en el navegador:

```text
http://127.0.0.1:8026/dashboard/
```

## 3. Cargar precios

El dashboard esta organizado en una navegacion lateral:

- `Resumen`
- `Precios`
- `Lista de compra`
- `Comparacion`
- `Ruta/cercania`

Primer archivo a cargar:

```text
data/processed/precios_con_promociones.csv
```

Ese archivo incluye precio de gondola, precio efectivo y ahorro por promocion.

Tambien se puede cargar:

```text
data/processed/precios_matcheados.csv
```

En ese caso el dashboard compara precio de gondola, sin promociones.

Para usar precios reales manuales, primero validar la carga:

```bash
python scripts/09_validar_precios_reales.py --input data/sample/precios_reales_demo.csv
python scripts/04_matching_productos.py --input data/processed/precios_reales_validados.csv --output data/processed/precios_reales_matcheados.csv
```

Luego cargar en el dashboard:

```text
data/processed/precios_reales_matcheados.csv
```

Si el archivo real se carga crudo y tiene columnas faltantes, precios invalidos, fechas invalidas, localidades fuera de alcance o duplicados, el dashboard muestra avisos. Para operacion controlada siempre conviene usar el validador antes de cargar.

## 4. Armar lista

Hay dos opciones:

1. Cargar una lista demo:

```text
data/sample/lista_compra_demo.csv
```

2. Armar la lista desde la interfaz:

- buscar un producto o grupo en `Armar lista`;
- indicar cantidad;
- elegir unidad;
- elegir prioridad;
- presionar `Agregar`;
- editar cantidad o eliminar items en `Lista actual`.

La lista se puede guardar en el navegador con `Guardar`, recuperar con `Recuperar` y exportar con `Exportar CSV`.

Tambien se puede usar `Recalcular` para actualizar los paneles con los datos cargados y `Limpiar sesion` para borrar la sesion local y empezar de nuevo.

## 5. Calcular ranking

Presionar:

```text
Calcular ranking
```

Interpretacion:

- `Mejor comercio`: comercio con mejor costo entre los que cubren mas items.
- `Ahorro estimado`: diferencia contra el comercio mas caro comparable.
- `Cobertura`: porcentaje de la lista encontrado por comercio.
- `Faltantes`: productos que no se encontraron en ese comercio.
- `Mejor compra dividida`: comercio recomendado para cada item si se permite comprar en mas de un lugar.

## 6. Calcular promociones

Si se carga `precios_con_promociones.csv`, el dashboard usa precio efectivo automaticamente.

Ver:

- `Precio original`: precio de gondola.
- `Precio efectivo`: precio luego de promocion.
- `Ahorro promo`: descuento aplicado.
- `Promocion`: descripcion de la promo usada.

## 7. Calcular ruta y cercania

Cargar sucursales:

```text
data/sample/sucursales_demo.csv
```

Cargar ubicacion:

```text
data/sample/ubicacion_usuario_demo.csv
```

Tambien se puede ingresar latitud y longitud manual.

Presionar:

```text
Calcular cercania
```

Interpretacion:

- `Distancia`: distancia aproximada en linea recta.
- `Penalizacion`: distancia multiplicada por costo por km.
- `Score`: costo total + penalizacion por distancia.
- `Recomendacion`: mejor balance entre precio, cobertura y cercania.
- `Ruta dividida`: orden sugerido si se compra en varios comercios.

La distancia es aproximada y no reemplaza una app de navegacion.

## 8. Archivos principales

Para uso completo del MVP:

```text
data/processed/precios_con_promociones.csv
data/sample/lista_compra_demo.csv
data/sample/sucursales_demo.csv
data/sample/ubicacion_usuario_demo.csv
```

Para exportar una lista propia:

```text
lista_compra_exportada.csv
```

Ese CSV es compatible con `scripts/05_calcular_lista_compra.py`.

## 9. Carga real controlada

Guia completa:

```text
docs/GUIA_CARGA_PRECIOS_REALES.md
```

Plantilla:

```text
data/sample/precios_reales_template.csv
```

Demo con errores controlados:

```text
data/sample/precios_reales_demo.csv
```

Reporte de validacion:

```text
data/processed/reporte_validacion_precios_reales.csv
```

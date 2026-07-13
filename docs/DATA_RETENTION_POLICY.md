# Politica de retencion y limpieza - datos

Actualizado: 2026-07-12.

## Objetivo

Definir reglas para almacenamiento, limpieza y trazabilidad de archivos crudos, samples y salidas procesadas del Proyecto Super San Juan.

## Reglas generales

1. Los archivos crudos reales no deben versionarse en Git.
2. `data/raw/` se usa solo para archivos originales descargados o cargados manualmente antes del procesamiento.
3. `data/raw/sepa/` se usa para ZIP/CSV SEPA reales o semirreales importados localmente.
4. `data/processed/` se usa para salidas generadas reproducibles.
5. `data/sample/` se usa para datos demo o simulados versionables.
6. No se deben guardar credenciales, tokens, claves API ni informacion sensible.
7. Si un archivo crudo contiene datos duplicados, corruptos o fuera de alcance, debe eliminarse luego de inventario.

## Datos versionables permitidos

- `data/sample/precios_demo.csv`: dataset demo Sprint 1.
- `data/sample/sepa/sepa_precios_simulado.csv`: dataset tipo SEPA simulado Sprint 2.
- `data/sample/product_dictionary.csv`: diccionario demo editable Sprint 3.
- `data/sample/lista_compra_demo.csv`: lista demo Sprint 4.
- `data/sample/promociones_demo.csv`: promociones demo Sprint 6.
- `data/sample/sucursales_demo.csv`: sucursales demo Sprint 7.
- `data/sample/ubicacion_usuario_demo.csv`: ubicacion demo Sprint 7.
- `data/sample/precios_reales_template.csv`: plantilla versionable Sprint 10.
- `data/sample/precios_reales_demo.csv`: demo realista con errores controlados Sprint 10.
- `data/sample/multifile/`: relevamientos ficticios multiarchivo Sprint 12.
- `.gitkeep` en carpetas vacias necesarias.

## Datos no versionables

- `data/raw/*`
- `data/raw/sepa/manual/*`
- `data/raw/sepa/extracted/*`
- `data/raw/precios_reales/*`
- `data/raw/precios_reales/manual/*`
- `data/processed/*`
- `data/export/*`
- `database/*.sqlite`
- `logs/*`

## Convencion de nombres recomendada

Para archivos crudos:

```text
fuente_localidad_fecha_descripcion.ext
```

Ejemplos:

```text
sepa_san_juan_20260709_minoristas.zip
carrefour_san_juan_20260709_catalogo.json
vea_capital_20260712_gondola.csv
carrefour_rawson_20260712_ticket.csv
precios_vea_sucursal_centro_capital_2026-07-12_manual.csv
```

## Retencion sugerida

- Raw SEPA/manual: conservar solo lo necesario para reproducir la ultima corrida validada.
- Processed: regenerar cuando sea necesario; no versionar outputs.
- Samples: mantener chicos, ficticios o simulados y aptos para pruebas.
- Manifiestos y reportes en `data/processed/`: regenerables; no versionar aunque contengan trazabilidad de una corrida real.

## Limpieza

Antes de borrar datos:

1. Inventariar ruta, fecha, tamano y motivo.
2. Confirmar que no es sample versionable.
3. Confirmar que la salida procesada puede regenerarse o que ya no se necesita.

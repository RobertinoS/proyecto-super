# Operacion diaria de precios reales

Este procedimiento ordena la carga manual o semimanual de precios reales por comercio, sucursal y fecha. No usa scraping automatico, backend, APIs pagas ni credenciales.

## Estructura operativa

Los archivos reales crudos deben guardarse en `data/raw/`, que esta ignorado por Git:

```text
data/raw/precios_reales/
data/raw/precios_reales/manual/
data/raw/precios_reales/manual/{comercio}/{sucursal}/{YYYY-MM-DD}/
```

Ejemplo:

```text
data/raw/precios_reales/manual/vea/sucursal_centro/2026-07-12/precios_vea_sucursal_centro_capital_2026-07-12_manual.csv
```

No guardar CSV reales crudos en `data/sample/`.

## Carga de precios

1. Copiar la plantilla `data/sample/precios_reales_template.csv`.
2. Completar una fila por producto relevado.
3. Guardar el archivo en la carpeta operativa del comercio, sucursal y fecha.
4. Usar nombres definidos en `docs/NAMING_CONVENTION.md`.

Fuentes aceptadas:

- `manual_gondola`: relevamiento en gondola.
- `manual_ticket`: ticket propio o verificado.
- `web_oficial`: catalogo o precio publicado por la cadena.
- `manual_relevamiento`: carga manual con respaldo operativo.

## Validar relevamiento

Comando:

```bash
python scripts/09_validar_precios_reales.py --input data/raw/precios_reales/manual/vea/sucursal_centro/2026-07-12/precios_vea_sucursal_centro_capital_2026-07-12_manual.csv
```

Salidas:

```text
data/processed/precios_reales_validados.csv
data/processed/reporte_validacion_precios_reales.csv
```

## Revisar errores

Abrir:

```text
data/processed/reporte_validacion_precios_reales.csv
```

Tipos principales:

- `precio_invalido`: corregir precio.
- `fecha_invalida`: corregir fecha.
- `localidad_fuera_alcance`: revisar si corresponde al alcance actual.
- `duplicado`: revisar si es el mismo producto repetido.
- `precio_sospechoso`: verificar contra ticket, gondola o fuente.

## Generar calidad de datos

Despues de validar:

```bash
python scripts/10_generar_reporte_calidad_datos.py
```

Salidas:

```text
data/processed/reporte_calidad_datos.csv
data/processed/resumen_calidad_fuente.csv
```

## Criterios operativos

Archivo aprobado:

- `estado_calidad = OK`.
- Sin errores fatales.
- Antiguedad menor o igual a 7 dias.

Archivo a corregir:

- `estado_calidad = REVISAR`.
- Tiene duplicados o precios sospechosos.
- Puede usarse solo si la revision manual confirma que el dato es valido.

Archivo invalido:

- `estado_calidad = INVALIDO`.
- Tiene errores fatales relevantes.
- Debe corregirse y validarse de nuevo antes de usarse para decision.

Archivo desactualizado:

- `estado_calidad = DESACTUALIZADO`.
- Antiguedad mayor a 7 dias.
- Debe relevarse nuevamente.

Archivo a descartar:

- No se puede trazar a ticket, gondola, web oficial o relevamiento.
- Tiene datos personales o privados.
- Pertenece a otra provincia o una localidad fuera del alcance operativo.
- No puede corregirse con evidencia confiable.

## Checklist diario

- Crear carpeta del dia por comercio/sucursal.
- Cargar CSV con la plantilla vigente.
- Validar con `scripts/09_validar_precios_reales.py`.
- Revisar el reporte de validacion.
- Corregir errores fatales.
- Generar reportes de calidad.
- Cargar `resumen_calidad_fuente.csv` y `reporte_calidad_datos.csv` en el dashboard.
- Usar para decisiones solo fuentes `OK` o `REVISAR` ya revisadas.

## Checklist semanal

- Revisar fuentes `DESACTUALIZADO`.
- Revisar comercios/sucursales con baja cobertura.
- Ampliar categorias faltantes.
- Depurar archivos crudos que ya no sean necesarios.
- Documentar cambios operativos en `docs/PROJECT_STATUS.md`.

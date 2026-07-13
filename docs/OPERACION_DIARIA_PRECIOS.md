# Operacion diaria de precios reales

## Extension cloud Sprint 14

El flujo manual de este documento sigue vigente. La automatizacion cloud piloto opera en paralelo y no reemplaza relevamientos fisicos:

```text
GitHub Actions -> n8n -> FastAPI -> Vea ONLINE -> Supabase -> aprobacion -> dataset
```

- UptimeRobot solo comprueba `/healthz` de n8n.
- GitHub Actions dispara una vez al dia.
- FastAPI puede dormir y n8n la despierta con `/health`.
- Durante Sprint 14 `SOURCE_MODE=fixture` para validacion y `ENABLE_PUBLICATION=false`.
- Una corrida live debe etiquetarse `ONLINE` y no mezclarse con `manual_gondola`.
- Revisar calidad y aprobar explicitamente antes de publicar.
- Ante fuente vacia, error, duplicado o calidad insuficiente, no publicar.

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

## Validar un relevamiento aislado

Comando:

```bash
python scripts/09_validar_precios_reales.py --input data/raw/precios_reales/manual/vea/sucursal_centro/2026-07-12/precios_vea_sucursal_centro_capital_2026-07-12_manual.csv
```

Salidas:

```text
data/processed/precios_reales_validados.csv
data/processed/reporte_validacion_precios_reales.csv
```

Este comando sigue disponible para revisar un solo CSV. En la operacion diaria con varios archivos usar la consolidacion.

## Consolidar la jornada

Procesar todos los CSV ubicados bajo la carpeta operativa:

```bash
python scripts/11_consolidar_relevamientos.py --input data/raw/precios_reales/manual
```

El descubrimiento es recursivo y el orden de procesamiento es lexicografico por ruta relativa. Las salidas son:

```text
data/processed/precios_reales_consolidados.csv
data/processed/reporte_consolidacion.csv
data/processed/manifiesto_consolidacion.csv
```

Regla inicial de duplicados:

- La clave es `comercio + sucursal + producto + marca + presentacion + fecha_relevamiento`.
- Los duplicados dentro de un archivo son excluidos por el validador individual.
- Entre archivos se conserva el ultimo registro procesado.
- El ganador queda con `estado_registro = CONSOLIDADO_CONFLICTO` y `conflicto_detectado = SI`.
- El ganador conserva su ruta relativa en `archivo_origen`.
- La prioridad se controla con prefijos ordenables: `01_` para la carga inicial, `02_` para la primera correccion y `03_` para una correccion posterior; ver `docs/NAMING_CONVENTION.md`.

Antes de usar la base, revisar `reporte_consolidacion.csv`. `REVISAR` permite corregir el archivo de origen y repetir la ejecucion; `INVALIDO` indica que el archivo no aporto filas utilizables.

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

Despues de validar un archivo individual:

```bash
python scripts/10_generar_reporte_calidad_datos.py
```

Despues de consolidar varios archivos:

```bash
python scripts/10_generar_reporte_calidad_datos.py --prices data/processed/precios_reales_consolidados.csv --validation-report data/processed/reporte_consolidacion.csv
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
- Consolidar la carpeta diaria con `scripts/11_consolidar_relevamientos.py`.
- Revisar `reporte_consolidacion.csv` y `manifiesto_consolidacion.csv`.
- Corregir errores fatales.
- Ejecutar matching sobre `precios_reales_consolidados.csv`.
- Generar reportes de calidad.
- Cargar `resumen_calidad_fuente.csv` y `reporte_calidad_datos.csv` en el dashboard.
- Usar para decisiones solo fuentes `OK` o `REVISAR` ya revisadas.

## Checklist semanal

- Revisar fuentes `DESACTUALIZADO`.
- Revisar comercios/sucursales con baja cobertura.
- Ampliar categorias faltantes.
- Depurar archivos crudos que ya no sean necesarios.
- Documentar cambios operativos en `docs/PROJECT_STATUS.md`.

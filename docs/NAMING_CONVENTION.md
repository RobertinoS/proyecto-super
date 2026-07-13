# Convencion de nombres

## Objetivo

Mantener archivos reales ordenados por comercio, sucursal, localidad, fecha y fuente, sin versionar datos crudos.

## Formato recomendado

```text
precios_{comercio}_{sucursal}_{localidad}_{YYYY-MM-DD}_{fuente}.csv
```

Ejemplo:

```text
precios_vea_sucursal_centro_capital_2026-07-12_manual.csv
```

## Componentes

- `comercio`: nombre normalizado sin espacios ni acentos. Ejemplo: `vea`, `carrefour`, `changomas`.
- `sucursal`: referencia estable. Ejemplo: `sucursal_centro`, `hiper_rawson`.
- `localidad`: `capital`, `rawson`, `santa_lucia`, `rivadavia`.
- `YYYY-MM-DD`: fecha de relevamiento.
- `fuente`: `manual`, `ticket`, `gondola`, `web_oficial`.

## Rutas

Guardar en:

```text
data/raw/precios_reales/manual/{comercio}/{sucursal}/{YYYY-MM-DD}/
```

Ejemplos:

```text
data/raw/precios_reales/manual/vea/sucursal_centro/2026-07-12/precios_vea_sucursal_centro_capital_2026-07-12_manual.csv
data/raw/precios_reales/manual/carrefour/hiper_rawson/2026-07-12/precios_carrefour_hiper_rawson_rawson_2026-07-12_ticket.csv
```

## Reglas

- Usar minusculas.
- Reemplazar espacios por `_`.
- Evitar acentos, simbolos y caracteres especiales.
- No incluir nombres de personas, telefonos, tarjetas ni datos privados.
- No sobrescribir relevamientos anteriores; crear una carpeta por fecha.
- Si una carga se corrige, guardar nueva version con sufijo claro, por ejemplo `_corregido`.

## Archivos procesados

Los outputs se generan en `data/processed/` y no se versionan:

```text
precios_reales_validados.csv
reporte_validacion_precios_reales.csv
reporte_calidad_datos.csv
resumen_calidad_fuente.csv
```

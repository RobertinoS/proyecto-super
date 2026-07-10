# Estructura esperada SEPA - Sprint 2

Actualizado: 2026-07-09.

## Fuentes oficiales revisadas

- Dataset oficial minorista: https://datos.produccion.gob.ar/dataset/sepa-precios
- Dataset oficial mayorista: https://datos.produccion.gob.ar/dataset/precios-claros-sepa-mayoristas
- Pagina oficial de acceso: https://www.argentina.gob.ar/economia/industria-y-comercio/defensadelconsumidor/precios-sepa
- Metadata tecnica minorista: Anexo II publicado como recurso PDF del dataset minorista.

## Lectura ejecutiva

SEPA es una fuente oficial abierta para precios informados por comercios. El portal oficial publica recursos ZIP diarios para minoristas y mayoristas. La metadata del dataset minorista indica que un paquete SEPA esperado contiene tres archivos CSV principales:

- `comercio.csv`: informacion del comercio y sus banderas comerciales.
- `sucursales.csv`: informacion de sucursales y ubicacion.
- `productos.csv`: productos comercializados por sucursal y precios.

La especificacion tecnica indica que los archivos son CSV en UTF-8 y usan barra vertical (`|`) como separador. El script del Sprint 2 tambien soporta coma, punto y coma, tab y pipe para tolerar descargas, reprocesos o CSVs consolidados.

## Campos SEPA relevantes

### comercio.csv

Campos esperados para identificar comercio y bandera:

- `id_comercio`
- `id_bandera`
- `comercio_cuit`
- `comercio_razon_social`
- `comercio_bandera_nombre`
- `comercio_bandera_url`
- `comercio_ultima_actualizacion`
- `comercio_version_sepa`

### sucursales.csv

Campos esperados para ubicacion:

- `id_comercio`
- `id_bandera`
- `id_sucursal`
- `sucursales_nombre`
- `sucursales_tipo`
- `sucursales_calle`
- `sucursales_numero`
- `sucursales_latitud`
- `sucursales_longitud`
- `sucursales_localidad`
- `sucursales_provincia`

### productos.csv

Campos esperados para producto y precio:

- `id_comercio`
- `id_bandera`
- `id_sucursal`
- `id_producto`
- `productos_descripcion`
- `productos_cantidad_presentacion`
- `productos_unidad_medida_presentacion`
- `productos_marca`
- `productos_precio_lista`
- `productos_precio_referencia`
- `productos_cantidad_referencia`
- `productos_unidad_medida_referencia`

## Decision Sprint 2

El flujo queda preparado para dos escenarios:

1. CSV consolidado semirreal o manual, como `data/sample/sepa/sepa_precios_simulado.csv`.
2. ZIP tipo SEPA con uno o varios CSV internos.

Para no romper Sprint 1, el dashboard sigue cargando CSV local con selector de archivo. Sprint 2 solo agrega un generador compatible:

```text
data/raw/sepa/manual/*.csv|*.zip
        -> scripts/03_filtrar_san_juan.py
        -> data/processed/precios_san_juan_sepa.csv
        -> dashboard/index.html
```

## Compatibilidad y limites

- No se usan credenciales, APIs privadas ni servicios pagos.
- `data/raw/sepa/` queda ignorado por Git porque puede contener archivos oficiales grandes.
- El sample SEPA versionable vive en `data/sample/sepa/`.
- Si el ZIP oficial cambia nombres de columnas, el script falla con error claro y se ajusta el mapa de aliases.
- SEPA se usa como fuente inicial oficial/semioficial, no como reemplazo definitivo de scrapers oficiales por cadena.

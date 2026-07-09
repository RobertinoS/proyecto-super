# Política de retención y limpieza - data/raw

## Objetivo

Definir reglas para el almacenamiento, limpieza y trazabilidad de archivos crudos utilizados en el Proyecto Super San Juan.

La carpeta `data/raw` se utiliza únicamente para almacenar archivos originales descargados o cargados manualmente antes de su procesamiento.

Los datos de ejemplo versionables deben vivir en:

```text
data/sample/
```

## Reglas generales

1. Los archivos crudos no deben versionarse en Git.
2. La carpeta `data/raw` debe conservar únicamente archivos necesarios para reprocesamiento, auditoría inmediata o validación.
3. Todo archivo procesado debe generar una salida normalizada en `data/processed`.
4. Si un archivo crudo contiene datos duplicados, corruptos o fuera del alcance del proyecto, debe eliminarse.
5. No se deben guardar credenciales, tokens, claves API ni información sensible dentro de `data/raw`.
6. `data/sample/precios_demo.csv` es el dataset demo versionable del Sprint 1.

## Convención de nombres

Los archivos crudos deberán nombrarse con el siguiente formato:

```text
fuente_localidad_fecha_descripcion.ext

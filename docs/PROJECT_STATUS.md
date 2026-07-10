# Estado del proyecto

Actualizado: 2026-07-09.

## Sprint actual

Sprint 2 - Ingestion SEPA/manual para San Juan.

Rama:

```text
sprint-2-sepa-ingestion
```

Objetivo: integrar una fuente real o semirreal de precios para San Juan, priorizando SEPA como fuente inicial, sin romper el dashboard funcional del Sprint 1.

## Diagnostico ejecutivo

El repo Git dedicado esta en:

```text
C:\Users\Rober\Desktop\Proyecto Super
```

El Sprint 1 quedo cerrado en `main` con commit limpio y el Sprint 2 se trabaja en una rama nueva. El dashboard local `dashboard/index.html` no fue reemplazado; sigue funcionando con CSV local y ahora tambien puede cargar el CSV generado por el flujo SEPA/manual.

## Base Sprint 1 preservada

Activos clave:

- `data/sample/precios_demo.csv`
- `scripts/02_normalizar_precios.py`
- `dashboard/index.html`
- `data/processed/precios_normalizados.csv` generado localmente

Capacidades:

- Carga manual de CSV.
- Validacion de columnas.
- KPIs basicos.
- Busqueda de producto.
- Filtro por comercio.
- Comparacion por comercio.
- Tabla ordenada de menor a mayor precio.

## Avance Sprint 2

Fuentes oficiales investigadas:

- Dataset oficial SEPA minorista.
- Dataset oficial SEPA mayorista.
- Metadata tecnica minorista con estructura de paquetes SEPA.

Decision tecnica:

- Mantener costo 0.
- No usar credenciales ni APIs privadas.
- Agregar modo manual para ZIP/CSV descargado.
- Agregar modo `download-plan` preparado para descarga futura.
- Usar `data/sample/sepa/` para datos simulados versionables.
- Usar `data/raw/sepa/` para archivos reales no versionados.

Nuevos artefactos:

- `data/sample/sepa/sepa_precios_simulado.csv`
- `scripts/01_descargar_o_importar_sepa.py`
- `scripts/03_filtrar_san_juan.py`
- `tests/test_sepa_ingestion.py`
- `docs/SEPA_STRUCTURE.md`

Salida Sprint 2:

```text
data/processed/precios_san_juan_sepa.csv
```

Reporte:

```text
data/processed/precios_san_juan_sepa_reporte.json
```

## Validaciones Sprint 2

El filtro San Juan:

- Lee CSV, TXT, directorios o ZIP.
- Soporta delimitadores coma, punto y coma, tab y pipe.
- Une archivos tipo SEPA separados por `id_comercio`, `id_bandera`, `id_sucursal`.
- Valida campos minimos.
- Convierte precio a numero.
- Valida fecha o usa fallback.
- Excluye filas fuera de San Juan.
- Prioriza Capital, Rawson, Santa Lucia y Rivadavia.
- Genera errores claros cuando corresponde.

## Datos Sprint 2

Archivo tipo SEPA simulado:

```text
data/sample/sepa/sepa_precios_simulado.csv
```

Contenido:

- 34 filas fuente.
- 32 filas San Juan generadas.
- 2 filas fuera de San Juan excluidas.
- Comercios: Vea, Carrefour, ChangoMas, Atomo Conviene y autoservicios grandes.
- Localidades: Capital, Rawson, Santa Lucia y Rivadavia.

## Pruebas ejecutadas

Comandos:

```bash
python -m py_compile scripts/01_descargar_o_importar_sepa.py scripts/02_normalizar_precios.py scripts/03_filtrar_san_juan.py
python scripts/02_normalizar_precios.py
python scripts/01_descargar_o_importar_sepa.py --mode download-plan
python scripts/01_descargar_o_importar_sepa.py --mode manual --input data/sample/sepa/sepa_precios_simulado.csv
python scripts/03_filtrar_san_juan.py --input data/raw/sepa/manual/sepa_precios_simulado.csv
python -m pytest
```

Resultados:

- Compilacion Python: OK.
- `scripts/02_normalizar_precios.py`: OK, 31 registros validos, 0 errores.
- `scripts/01_descargar_o_importar_sepa.py --mode download-plan`: OK, genera manifiesto sin descargar.
- `scripts/01_descargar_o_importar_sepa.py --mode manual`: OK, copia sample a `data/raw/sepa/manual/`.
- `scripts/03_filtrar_san_juan.py`: OK, 34 filas leidas, 32 San Juan, 2 fuera de provincia excluidas, 0 errores.
- `python -m pytest`: 10 passed.
- Dashboard: abre por HTTP local, contiene cargador y filtros; el parser del dashboard lee `precios_san_juan_sepa.csv` con 32 filas, 7 productos, 7 comercios, promedio 2414.23, busqueda `yerba` con 6 resultados y orden ascendente correcto.

## Riesgos y pendientes

- SEPA depende de datos declarados por comercios; debe auditarse contra paginas oficiales de cadenas cuando sea posible.
- El flujo de descarga automatica queda preparado pero no activo por defecto.
- El dashboard carga archivos por selector debido a restricciones normales del navegador.
- Falta matching avanzado de productos equivalentes y precio por unidad comparable.
- Falta scoring de ahorro por lista de compra y ruta.

## Proximo sprint recomendado

Sprint 3 - Matching, equivalencias y ahorro por lista.

Objetivo: construir diccionario/catalogo propio de productos, normalizar presentaciones, comparar precio por unidad y calcular ahorro por lista de compra y comercio/ruta.

# Proyecto Super San Juan

Comparador local de precios para supermercados, autoservicios y mayoristas de San Juan.

El proyecto mantiene dos caminos compatibles:

```text
Sprint 1 CSV demo:
data/sample/precios_demo.csv
        -> scripts/02_normalizar_precios.py
        -> data/processed/precios_normalizados.csv
        -> dashboard/index.html

Sprint 2 SEPA/manual:
data/sample/sepa/sepa_precios_simulado.csv o data/raw/sepa/manual/*.csv|*.zip
        -> scripts/01_descargar_o_importar_sepa.py
        -> scripts/03_filtrar_san_juan.py
        -> data/processed/precios_san_juan_sepa.csv
        -> dashboard/index.html
```

## Requisitos

- Python 3.11 o superior.
- Navegador moderno.
- No requiere backend para el dashboard CSV.
- No requiere credenciales, servicios pagos ni APIs privadas.

Instalar dependencias del proyecto completo:

```bash
python -m pip install -r requirements.txt
```

## Sprint 1: CSV local demo

Normalizar datos demo:

```bash
python scripts/02_normalizar_precios.py
```

Salida esperada:

```text
data/processed/precios_normalizados.csv
```

Abrir dashboard:

1. Abrir `dashboard/index.html` con doble clic o desde el navegador.
2. Presionar "Seleccionar archivo".
3. Cargar `data/processed/precios_normalizados.csv`.
4. Buscar productos y comparar precios por comercio.

## Sprint 2: SEPA/manual San Juan

SEPA se integra como fuente inicial oficial/semirreal sin reemplazar el dashboard ni el flujo local del Sprint 1.

Investigar o dejar preparado el modo descarga:

```bash
python scripts/01_descargar_o_importar_sepa.py --mode download-plan
```

Importar un ZIP/CSV descargado manualmente:

```bash
python scripts/01_descargar_o_importar_sepa.py --mode manual --input data/sample/sepa/sepa_precios_simulado.csv
```

Filtrar San Juan y generar CSV compatible:

```bash
python scripts/03_filtrar_san_juan.py --input data/raw/sepa/manual/sepa_precios_simulado.csv
```

Salida esperada:

```text
data/processed/precios_san_juan_sepa.csv
data/processed/precios_san_juan_sepa_reporte.json
```

Luego abrir `dashboard/index.html` y cargar `data/processed/precios_san_juan_sepa.csv`.

## Datos versionables

- `data/sample/precios_demo.csv`: demo Sprint 1.
- `data/sample/sepa/sepa_precios_simulado.csv`: fuente tipo SEPA simulada para pruebas reproducibles.

## Politica de datos

- No versionar archivos crudos reales ni pesados.
- Reservar `data/raw/` para datos reales descargados/importados localmente.
- Reservar `data/processed/` para salidas generadas reproducibles.
- No guardar secretos, tokens ni credenciales.

## Documentacion

- `docs/ROADMAP.md`
- `docs/DATA_CONTRACT.md`
- `docs/SEPA_STRUCTURE.md`
- `docs/TEST_PLAN.md`
- `docs/PROJECT_STATUS.md`
- `docs/CHANGELOG.md`
- `docs/DATA_RETENTION_POLICY.md`

## Proyecto completo existente

Ademas del dashboard standalone de Sprint 1/2, el repo conserva el sistema avanzado construido previamente:

- `app/index.html`: dashboard principal con JSON exportado.
- `app/promociones.html`: promociones, tarjetas y catalogos.
- `src/run_pipeline.py`: pipeline de fuentes oficiales.
- `database/precios_san_juan.sqlite`: base local ignorada por Git.
- `data/export/*.json`: exports locales ignorados por Git.

## Proximo sprint recomendado

Sprint 3: matching de productos, equivalencias por unidad/presentacion y ranking de ahorro por lista de compra.

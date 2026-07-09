# Proyecto Super San Juan

Comparador local de precios para supermercados, autoservicios y mayoristas de San Juan.

El Sprint 1 deja una base funcional minima usando CSV local:

```text
data/sample/precios_demo.csv
        -> scripts/02_normalizar_precios.py
        -> data/processed/precios_normalizados.csv
        -> dashboard/index.html
```

## Requisitos

- Python 3.11 o superior.
- Navegador moderno.
- No requiere backend para el dashboard CSV.

Instalar dependencias del proyecto completo:

```bash
python -m pip install -r requirements.txt
```

## Sprint 1: flujo CSV local

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

Tambien puede servirse localmente:

```bash
python -m http.server 8000
```

Abrir:

```text
http://localhost:8000/dashboard/
```

## Datos demo

El archivo `data/sample/precios_demo.csv` contiene datos ficticios pero realistas para San Juan, con comercios como Vea, Carrefour, ChangoMas, Atomo Conviene y autoservicios grandes.

Columnas obligatorias:

- `comercio`
- `sucursal`
- `localidad`
- `producto`
- `marca`
- `categoria`
- `presentacion`
- `precio`
- `fecha_relevamiento`
- `fuente`

## Proyecto completo existente

Ademas del Sprint 1, el repo conserva el sistema avanzado construido previamente:

- `app/index.html`: dashboard principal con JSON exportado.
- `app/promociones.html`: promociones, tarjetas y catalogos.
- `src/run_pipeline.py`: pipeline de fuentes oficiales.
- `database/precios_san_juan.sqlite`: base local.
- `data/export/*.json`: exports para dashboards existentes.

## Documentacion

- `docs/ROADMAP.md`
- `docs/DATA_CONTRACT.md`
- `docs/TEST_PLAN.md`
- `docs/PROJECT_STATUS.md`
- `docs/CHANGELOG.md`
- `docs/DATA_RETENTION_POLICY.md`

## Politica de datos

- No versionar archivos crudos pesados.
- Reservar `data/raw/` para datos reales no versionados.
- Versionar `data/sample/precios_demo.csv` como demo controlado.
- Generar `data/processed/precios_normalizados.csv` localmente; no versionarlo salvo decision futura.
- No guardar secretos, tokens ni credenciales.

## Proximo sprint recomendado

Sprint 2: mejorar matching de productos, presentaciones y equivalencias para comparar productos de forma mas precisa.

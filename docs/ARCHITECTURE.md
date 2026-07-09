# Arquitectura

## Vista general

```text
Fuentes oficiales
  - ecommerce/API publica
  - HTML publico
  - catalogos y redes oficiales
        |
        v
src/scrapers/*
        |
        v
normalizacion y carga SQLite
        |
        v
database/precios_san_juan.sqlite
        |
        v
src/export_dashboard.py
        |
        v
data/export/*.json
        |
        v
app/index.html
app/promociones.html
```

## Capas

### Configuracion

- `config/fuentes.yml`: inventario de fuentes oficiales, estado, prioridad y confianza.
- `.env.example`: variables locales sin secretos.

### Extraccion

- `src/run_pipeline.py`: orquestador.
- `src/source_discovery.py`: auditoria HTTP de fuentes.
- `src/scrapers/`: scrapers y monitores por fuente.
- `data/raw/`: capturas crudas, pesado y no versionable.
- `data/processed/`: CSVs procesados y diagnosticos.

### Persistencia

- `database/precios_san_juan.sqlite`: base local.
- Tablas principales: `sources`, `stores`, `products`, `prices`, `scrape_runs`.

### Export

- `src/export_dashboard.py`: genera JSON para UI.
- `data/export/precios_actuales.json`.
- `data/export/productos.json`.
- `data/export/sucursales.json`.
- `data/export/fuentes.json`.
- `data/export/auditoria.json`.
- `data/export/promociones.json`.
- `data/export/tarjetas.json`.
- `data/export/catalogos_oficiales.json`.

### Aplicacion

- `app/index.html`: comparador, filtros, lista de compra, ahorro y ruta economica.
- `app/promociones.html`: promociones, tarjetas y catalogos.
- Usa Tailwind y Chart.js por CDN.

### Automatizacion

- `run_update.bat`: actualizacion local.
- `scripts/register_update_task.ps1`: registra tarea programada.

## Estado de fuentes

Precio estructurado implementado:

- Atomo Conviene.
- ChangoMas / MasOnline.
- Vea.
- Carrefour.
- Maxiconsumo.

Catalogos/promociones/canales oficiales:

- La Anonima.
- Yaguar.
- Makro.
- Cafe America.
- Cabral.
- La Cumbre.
- La Nobleza.
- La Estrella.
- Basualdo.

## Riesgos tecnicos

- Git esta inicializado en el Desktop completo, no en el directorio del proyecto.
- `data/raw` pesa cerca de 200 MB y crece con cada corrida.
- La base SQLite es artefacto activo y pesa cerca de 15 MB.
- El dashboard depende de JSON exportados; abrir HTML directo puede fallar por CORS/local fetch.
- Algunas fuentes requieren ubicacion, JS o solo publican flyers.

## Reglas de cambio

- Cambios de contrato deben actualizar `DATA_CONTRACT.md`.
- Cambios de UX deben actualizar `TEST_PLAN.md`.
- Cambios de fuentes deben actualizar `config/fuentes.yml`, `docs/SOURCES.md` y auditoria.
- Cambios de automatizacion deben actualizar `docs/PROJECT_STATUS.md`.

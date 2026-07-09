# AGENTS.md

Reglas permanentes para trabajar en Proyecto Super.

## Objetivo del proyecto

Construir un comparador local de precios, promociones, tarjetas y rutas de compra para supermercados, autoservicios y mayoristas grandes de San Juan, Argentina.

El usuario debe poder buscar productos, armar listas con cantidad, guardar compras frecuentes, comparar supermercados, ver promociones, estimar ahorro y planificar una ruta de compra eficiente.

## Stack permitido

- Python local.
- SQLite como base principal.
- Pandas para ETL acotado.
- JSON local para dashboard.
- HTML, JavaScript, Tailwind CSS y Chart.js por CDN.
- pytest.
- Windows Task Scheduler, `.bat` y `.ps1`.
- Scraping responsable de fuentes publicas y oficiales.

No usar servicios pagos, cloud, proxies pagos, Google Sheets ni credenciales privadas sin aprobacion explicita.

## Comandos operativos

Instalar:

```bash
python -m pip install -r requirements.txt
```

Actualizar datos:

```bash
python src/run_pipeline.py --all
```

Exportar dashboard:

```bash
python src/run_pipeline.py --export
```

Ejecutar tests:

```bash
python -m pytest
```

Abrir dashboard:

```bash
python -m http.server 8000
```

URLs locales:

```text
http://localhost:8000/app/
http://localhost:8000/app/promociones.html
```

## Archivos criticos

No tocar sin objetivo claro y prueba posterior:

- `app/index.html`
- `app/promociones.html`
- `src/run_pipeline.py`
- `src/export_dashboard.py`
- `src/database.py`
- `src/normalize.py`
- `src/search_engine.py`
- `src/basket_optimizer.py`
- `src/scrapers/`
- `config/fuentes.yml`
- `database/precios_san_juan.sqlite`
- `data/export/*.json`

## Politica de scraping

- Priorizar API publica oficial, HTML oficial y catalogos oficiales.
- No usar login privado, cookies personales, captcha, paywall ni bypass agresivo.
- Usar timeouts, User-Agent claro, retries moderados y pausa entre requests.
- Guardar raw y processed separados.
- No inventar precios.
- Etiquetar fuente, URL, fecha y `confidence_score`.
- PedidosYa, mapas y directorios sirven para descubrimiento, no como precio final salvo decision explicita.

## Politica de datos

- No mezclar precio lista, promo general y promo condicional sin etiqueta.
- No comparar productos distintos como equivalentes sin regla documentada.
- Mantener trazabilidad por `source_id`.
- Separar fuentes vigentes de historicas.
- Exportar JSON liviano y estable para el dashboard.

## Politica de limpieza

- No borrar ni mover archivos sin inventario previo.
- Registrar candidatos en `docs/LEGACY_INVENTORY.md`.
- No borrar `data/export` porque alimenta el dashboard.
- No borrar la base sin backup y aprobacion.
- `data/raw` puede crecer: limpiar solo en sprint de mantenimiento aprobado.

## Politica de Git/checkpoints

- Antes de cambios, revisar `git rev-parse --show-toplevel` y `git status`.
- No hacer commit si el repo apunta al Desktop completo o incluye archivos personales.
- No hacer `git reset --hard` ni revertir cambios del usuario.
- Proponer checkpoints despues de verificar que no hay basura, secretos ni archivos gigantes.

## Trabajo por sprints

Cada sprint debe definir:

- objetivo de negocio;
- archivos permitidos;
- entregables;
- pruebas minimas;
- criterio de aceptacion;
- riesgos y bloqueos.

No avanzar al sprint siguiente sin cerrar el actual.

## Definicion de terminado

Un cambio esta terminado cuando:

- cumple el alcance del sprint;
- no toca archivos fuera de alcance;
- tiene documentacion actualizada;
- `python -m pytest` pasa o se documenta el bloqueo;
- si aplica, `python src/run_pipeline.py --export` pasa;
- el dashboard local responde o se documenta el bloqueo;
- queda claro el siguiente paso.

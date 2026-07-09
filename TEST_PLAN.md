# Plan de pruebas

## Pruebas unitarias

Comando:

```bash
python -m pytest
```

Cobertura actual:

- Normalizacion de texto, precios y presentaciones.
- Insercion basica en SQLite.
- Similitud de busqueda.

Agregar en Sprint 1:

- Contrato de `data/export/*.json`.
- Validacion de precios sospechosos.
- Validacion de categorias y fuentes.

## Pruebas de pipeline

Comandos:

```bash
python src/run_pipeline.py --export
python src/run_pipeline.py --scrape all --export
```

Validar:

- No falla si una fuente no trae registros.
- `data/export/precios_actuales.json` existe.
- `data/export/fuentes.json` tiene fuentes oficiales.
- `data/export/auditoria.json` actualiza conteos.
- No reaparece una fuente retirada.

## Pruebas de dashboard

Servidor:

```bash
python -m http.server 8000
```

URLs:

```text
http://localhost:8000/app/
http://localhost:8000/app/promociones.html
```

Validar:

- Carga sin errores visibles.
- Muestra KPIs.
- Filtros por cadena, categoria y ciudad.
- Tabla de precios.
- Graficos o fallback si Chart.js falla.
- Modo oscuro.
- Responsive desktop/mobile.

## Pruebas de matching y lista

Casos manuales obligatorios:

- `yerba mate 1kg x1`
- `cafe 750g x2`
- `leche larga vida 1l x3`
- `aceite girasol 900ml x1`
- `arroz largo fino 1kg x2`
- `azucar 1kg x1`

Validar:

- La cantidad multiplica subtotal.
- Producto faltante se informa.
- No se elige producto claramente incompatible.
- Se puede guardar y cargar lista.
- Se puede borrar lista.

## Pruebas de promociones

Validar:

- Promociones por sector.
- Promociones por cadena.
- Catalogos oficiales aparecen como catalogo, no precio final.
- Tarjetas/medios de pago se separan de descuentos por producto.
- Promocion condicional se etiqueta.

## Pruebas de filtros

Validar:

- No hay cadenas duplicadas por diferencias de nombre.
- No hay categorias duplicadas por acentos o mayusculas.
- Busqueda + filtros combinados no rompen la tabla.
- Reset manual posible recargando o limpiando campos.

## Pruebas de scraping responsable

Validar por fuente:

- Timeout razonable.
- Error capturado en `scrape_runs`.
- Raw guardado en `data/raw/<fuente>/`.
- Processed guardado en `data/processed/<fuente>/`.
- No usa credenciales ni cookies privadas.

## Pruebas de automatizacion

Comandos:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\register_update_task.ps1 -StartTime 07:00 -RepeatHours 5
```

Validar:

- La tarea existe.
- Ejecuta `run_update.bat`.
- No requiere ventana interactiva para terminar.
- Logs o auditoria permiten saber si fallo.

## Pruebas responsive

Validar manualmente:

- 390x844 mobile.
- 768x1024 tablet.
- 1366x768 desktop.
- 1920x1080 desktop.

Flujos:

- Buscar producto.
- Aplicar filtros.
- Armar lista.
- Ver ruta.
- Abrir promociones.
- Cambiar modo oscuro.

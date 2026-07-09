# Roadmap

## Sprint 1 - Base funcional CSV local

Objetivo: crear un flujo minimo para comparar precios usando CSV local, sin backend.

Entregables:

- `data/sample/precios_demo.csv`.
- `scripts/02_normalizar_precios.py`.
- `data/processed/precios_normalizados.csv`.
- `dashboard/index.html`.
- Documentacion actualizada.

Criterio de aceptacion:

- El script normaliza el CSV demo.
- El dashboard abre en navegador.
- El dashboard carga `data/processed/precios_normalizados.csv`.
- Se ven KPIs, busqueda, comparacion por comercio y tabla ordenada por precio.

## Sprint 2 - Matching y equivalencias

Objetivo: comparar productos equivalentes con mayor precision.

Entregables:

- Reglas de normalizacion de presentacion.
- Precio por unidad comparable.
- Tests para productos frecuentes.

## Sprint 3 - Calidad de datos

Objetivo: detectar datos invalidos o sospechosos antes de mostrarlos.

Entregables:

- Validador de contrato.
- Reporte de errores.
- Tests de columnas, precios y fechas.

## Sprint 4 - Listas de compra

Objetivo: permitir que el usuario cargue cantidades, guarde listas y estime totales.

Entregables:

- Modelo de lista.
- UI de listas.
- Persistencia local.

## Sprint 5 - Promociones y tarjetas

Objetivo: separar precio lista, promo general, promo condicional y beneficios de pago.

Entregables:

- Contrato de promociones.
- Reglas de tarjetas.
- Vista de promociones.

## Sprint 6 - Fuentes oficiales y automatizacion

Objetivo: integrar fuentes oficiales con actualizaciones controladas.

Entregables:

- Scrapers responsables.
- Logs.
- Tarea programada.
- Auditoria por fuente.

## Sprint 7 - Ruta de compra y distancia

Objetivo: sugerir ruta considerando ahorro y distancia.

Entregables:

- Sucursales con coordenadas.
- Calculo de distancia.
- Ahorro estimado neto.

## Sprint 8 - UI/UX premium y empaquetado

Objetivo: dejar el producto listo para demo/cliente.

Entregables:

- Refinamiento visual.
- Responsive audit.
- Limpieza legacy aprobada.
- Guia de uso final.

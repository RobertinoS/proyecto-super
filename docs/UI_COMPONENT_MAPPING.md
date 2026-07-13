# Mapeo de componentes UI

Actualizado: 2026-07-13.

Este documento mapea la funcionalidad estable de v1.4.0 contra su ubicacion en la interfaz integrada.

| Funcionalidad | ID o contrato funcional | Nueva ubicacion visual |
|---|---|---|
| Carga de precios | `fileInput`, `priceFileState`, `fileError` | Datos, card `Precios` |
| Carga de listas | `listInput`, `listFileState`, `listError` | Datos, card `Lista` |
| Carga de sucursales | `branchInput`, `branchFileState`, `branchError` | Datos, card `Sucursales` |
| Carga de ubicacion | `userLocationInput`, `locationFileState`, `userLocationError` | Datos, card `Ubicacion` |
| Reportes de calidad | `qualitySummaryInput`, `qualityReportInput` | Calidad, bloque de fuentes |
| Estados de archivos | `*FileState` | Badges visibles dentro de cada card de carga |
| Busqueda de productos | `searchInput` | Productos, barra principal de filtros |
| Filtro por comercio | `commerceFilter` | Productos, barra principal de filtros |
| Armado de lista | `builderSearchInput`, `productCandidates` | Mi lista, catalogo lateral |
| Cantidad, unidad y prioridad | `defaultQuantityInput`, `defaultUnitSelect`, `defaultPrioritySelect` | Mi lista, controles de alta |
| Edicion y eliminacion | `shoppingListRows` | Mi lista, tabla editable |
| localStorage | `saveListButton`, `restoreListButton`, `clearStoredListButton` | Mi lista, toolbar de acciones |
| Exportacion CSV | `exportListButton` | Mi lista, accion secundaria destacada |
| Promociones | `promo_aplicada`, `precio_efectivo`, `ahorro_promocion` | Comparacion y tabla de precios |
| Ranking por comercio | `listRankingRows`, `coveragePill` | Comparacion, panel principal |
| Faltantes | `missingRows`, `missingPill` | Comparacion, bloque de alertas |
| Mejor compra dividida | `splitRows`, `splitPill` | Comparacion, tabla secundaria |
| Calidad de datos | `qualityRows`, `qualityPill` | Calidad, semaforo operativo |
| Score de calidad | `score_calidad` | Calidad, columna y KPI de resumen |
| Antiguedad | `antiguedad_dias` | Calidad, columna con estado |
| Estados operativos | `OK`, `REVISAR`, `INVALIDO`, `DESACTUALIZADO` | Badges verde, ambar, rojo y gris |
| Consolidacion | Columnas canonicas y matching de `precios_reales_consolidados_matcheados.csv` | Carga de precios; no necesita control separado |
| Coordenadas manuales | `manualLatInput`, `manualLonInput` | Ruta, bloque `Origen` |
| Cercania | `calculateRouteButton`, Haversine | Ruta, accion principal |
| Ranking de ruta | `routeRows`, `routePill` | Ruta, tabla de conveniencia |
| Ruta dividida | `splitRouteRows`, `splitRoutePill` | Ruta, tabla de paradas |
| Score de conveniencia | `kpiRouteScore`, `score_conveniencia` | Resumen ejecutivo y Ruta |
| Mejor comercio | `kpiBestCommerce` | Resumen ejecutivo |
| Costo estimado | `kpiBestListCost` | Resumen ejecutivo |
| Ahorro | `kpiListSavings` | Resumen ejecutivo |
| Cobertura | `cobertura_lista_pct` / ranking | Resumen ejecutivo y Comparacion |
| Recomendacion de ruta | `kpiRouteBest`, `kpiRouteDistance` | Resumen ejecutivo y Ruta |
| Mensajes de error | `fileError`, `listError`, `branchError`, `userLocationError`, errores de calidad | Debajo del control afectado y toast operativo |
| Procesamiento | `statusBox`, acciones de carga/calculo | Barra de estado y loaders discretos |
| Recalculo global | `recalculateAllButton` | Header, accion primaria |
| Limpieza de sesion | `clearSessionButton` | Header, accion secundaria con confirmacion |

## Navegacion oficial

- `Resumen`: estado general, KPIs y flujo recomendado.
- `Datos`: todos los archivos y sus estados.
- `Productos`: busqueda, filtros, comparacion y tabla.
- `Mi lista`: catalogo, editor y persistencia.
- `Comparacion`: ranking, promociones, faltantes y compra dividida.
- `Calidad`: cobertura, score, antiguedad e incidencias.
- `Ruta`: origen, cercania, conveniencia y paradas.

## Selectores protegidos

Los IDs existentes son contrato de compatibilidad. Las pruebas deben fallar si el dashboard oficial elimina cualquiera de los controles, contenedores de resultados o KPIs utilizados por el dashboard v1.4.0.

La candidata supero la validacion y el mapeo aplica al dashboard oficial `dashboard/index.html`. La copia temporal `dashboard/v2/` fue eliminada despues de comprobar igualdad de hash.

# Plan de integracion visual Site

Actualizado: 2026-07-13.

## Objetivo

Integrar la direccion visual de `design_reference/site_model/` con toda la funcionalidad estable de Proyecto Super v1.4.0. Durante la implementacion, `dashboard/index.html` permanecio como fuente de verdad hasta que una candidata temporal alcanzo paridad funcional y supero las pruebas.

## Inventario del dashboard funcional

`dashboard/index.html` es una aplicacion local sin backend. Contiene HTML, CSS y JavaScript embebidos y ofrece:

- carga CSV de precios, lista, sucursales, ubicacion y dos reportes de calidad;
- validacion de columnas, precios, fechas, localidades y duplicados;
- busqueda y filtros por comercio y rango de precio;
- KPIs, comparacion individual y tabla de precios;
- armado, edicion, eliminacion, persistencia local y exportacion de listas;
- promociones, precio original, precio efectivo y ahorro;
- ranking por comercio, cobertura, faltantes y compra dividida;
- calidad de datos con score, antiguedad, incidencias y estados operativos;
- cercania Haversine, penalizacion, score de conveniencia y ruta dividida;
- mensajes operativos, recarga de archivos y limpieza de sesion.

La API de prueba `globalThis.__proyectoSuperDashboard` expone funciones puras para validar parsing, listas, ranking, promociones, calidad y rutas.

## Inventario del modelo visual Site

Archivos encontrados:

- `design_reference/site_model/html.txt`: HTML renderizado de una vista de resumen.
- `design_reference/site_model/Captura de pantalla 2026-07-12 234419.jpg`: cabecera, filtros, metricas, comparacion e insight.
- `design_reference/site_model/Captura de pantalla 2026-07-12 234446.jpg`: tabla de productos.

Elementos reutilizables:

- sidebar verde profundo con marca compacta y estado al pie;
- contenido sobre fondo gris marfil claro;
- encabezado editorial compacto con eyebrow;
- filtros agrupados en una superficie blanca;
- cards de metricas con acentos verde, azul y ambar;
- barras horizontales para comparar comercios;
- card destacada para recomendacion o hallazgo;
- tablas blancas, ligeras y escaneables;
- espaciado generoso y bordes discretos.

El HTML de referencia depende de assets compilados que no estan incluidos. Por eso se usa como referencia visual, no como runtime ni como fuente funcional.

## Diferencias

| Area | Dashboard v1.4.0 | Modelo Site |
|---|---|---|
| Alcance | Flujo completo de precios, lista, calidad y ruta | Resumen, filtros y tabla de productos |
| Apariencia | Tema oscuro BI con muchas secciones visibles | Tema claro, verde/lima, mas aire y jerarquia |
| Navegacion | Seis anclas funcionales | Cuatro destinos conceptuales |
| Datos | CSV local y calculos reales | Datos visuales renderizados |
| Estado | Mensajes y pills funcionales | Estado simple al pie del sidebar |
| Responsive | Responsive existente | Referencia principalmente desktop |
| Dependencias | Ninguna obligatoria | Assets compilados no disponibles |

## Riesgos de regresion

- perder IDs usados por JavaScript o tests;
- duplicar IDs al crear un resumen ejecutivo;
- ocultar controles necesarios en mobile;
- reducir legibilidad de tablas extensas;
- alterar contratos CSV o calculos al reorganizar la interfaz;
- introducir dependencia del sitio publicado o de assets remotos;
- promover la candidata antes de probar archivos demo y consolidados.

## Estrategia

1. Crear una candidata temporal en `dashboard/v2/index.html` como copia funcional aislada.
2. Conservar el JavaScript y todos los IDs/selectores funcionales.
3. Rehacer la capa visual con CSS local inspirado en Site.
4. Reordenar solo bloques HTML cuando no cambie su contrato funcional.
5. Agregar feedback visual y estados deshabilitados con cambios JavaScript pequenos y auditables.
6. Probar candidata y actual en paralelo por HTTP.
7. Validar desktop, mobile, consola, CSV demo, consolidado, calidad, ranking y rutas.
8. Promover la candidata a `dashboard/index.html` solo si alcanza paridad completa. Git conserva la version anterior; no se crean copias legacy desordenadas.

## Arquitectura frontend

Se mantiene un unico HTML oficial. Separar el JavaScript de 1.300 lineas en varios modulos simultaneamente al rediseno aumentaria el riesgo y obligaria a cambiar las pruebas actuales. La separacion progresiva queda diferida hasta contar con pruebas de navegador mas amplias. La candidata temporal no requirio build ni dependencias y se elimino despues de la promocion para evitar duplicacion.

## Archivos a modificar

- `dashboard/v2/index.html` solo durante la etapa candidata temporal;
- `dashboard/index.html` solo despues de aprobar la candidata;
- `tests/test_dashboard_site_integration.py`;
- `README.md`;
- `docs/GUIA_USO_MVP.md`;
- `docs/PROJECT_STATUS.md`;
- `docs/TEST_PLAN.md`;
- `docs/CHANGELOG.md`;
- este plan y `docs/UI_COMPONENT_MAPPING.md`.

## Archivos que no se modifican

- `scripts/01_*.py` a `scripts/11_*.py`;
- contratos CSV y datos de `data/sample/`;
- outputs ignorados de `data/processed/`;
- datos reales de `data/raw/`;
- logica de matching, promociones, lista, calidad y rutas en Python;
- el modelo original dentro de `design_reference/site_model/`.

## Criterios de aceptacion

- direccion visual reconocible respecto del modelo Site;
- paridad funcional completa con v1.4.0;
- todos los IDs y selectores requeridos disponibles;
- ejecucion local sin sitio publicado, backend ni build;
- feedback claro, contraste legible y navegacion por teclado razonable;
- responsive sin solapamientos en desktop y mobile;
- archivos demo, consolidado multiarchivo y reportes de calidad funcionales;
- suite existente y nuevas pruebas aprobadas;
- consola del navegador sin errores;
- promocion controlada a `dashboard/index.html` solo despues de validar.

## Resultado de integracion

La candidata cumplio los criterios y fue promovida a `dashboard/index.html`.

`dashboard/v2/index.html` tenia el mismo hash SHA-256 que el dashboard promovido. Fue eliminado junto con la carpeta vacia; Git conserva el proceso y `dashboard/index.html` queda como unica version oficial.

- IDs funcionales conservados: todos los de v1.4.0.
- Suite completa: 51 passed.
- Demo promocionado: 32 filas, 7 comercios y ranking efectivo.
- Consolidado: 12 filas, 2 comercios y conflicto resuelto sin duplicar resultados.
- Calidad: resumen y detalle de 4 grupos.
- Ruta demo: 12 recomendaciones.
- Responsive: 1440x1000 y 390x844 sin desbordes.
- Consola: sin errores.
- Dependencias externas obligatorias: ninguna.

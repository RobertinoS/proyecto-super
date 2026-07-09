# Backlog priorizado

| ID | Prioridad | Modulo | Descripcion | Impacto de negocio | Complejidad | Dependencias | Criterio de aceptacion |
|---|---|---|---|---|---|---|---|
| B-001 | P0 | Datos | Validar contrato de `data/export/*.json` antes de publicar dashboard | Evita decisiones con datos rotos | Media | DATA_CONTRACT | Tests fallan si falta campo critico |
| B-002 | P0 | Fuentes | Separar explicitamente fuentes con precio vigente, catalogo y referencia secundaria | Mejora confianza del usuario | Baja | config/fuentes.yml | Dashboard y docs muestran nivel de fuente |
| B-003 | P0 | Calidad | Detectar precios sospechosos por rango, cero, nulos o outliers por categoria | Evita recomendaciones falsas | Media | export/schema | Reporte con filas sospechosas |
| B-004 | P0 | Matching | Mejorar matching de productos por marca, unidad y presentacion | Ahorro calculado mas confiable | Alta | normalize/search | No compara 500g contra 1kg sin normalizar |
| B-005 | P0 | Tests | Agregar tests de export y contrato | Reduce regresiones | Media | DATA_CONTRACT | `pytest` cubre JSON minimo |
| B-006 | P1 | Listas | Consolidar manejo de item + cantidad en motor Python y dashboard | Mejora planificacion real | Media | matching | Cantidad afecta totales en todos los caminos |
| B-007 | P1 | UX | Evitar filtros duplicados por categoria/cadena/ciudad | Mejora usabilidad | Baja | export canonical | Opciones unicas y ordenadas |
| B-008 | P1 | Categorias | Normalizar categorias a taxonomia corta | Mejora comparacion por sector | Media | DATA_CONTRACT | Productos caen en categorias esperadas |
| B-009 | P1 | Promociones | Separar promo general, combo, volumen y condicional | Evita confusion de ahorro | Media | export promos | Promo condicional siempre etiquetada |
| B-010 | P1 | Tarjetas | Extraer bancos, tarjetas, cuotas y topes cuando esten disponibles | Mayor valor para decision | Alta | fuentes/catalogos | Tarjetas tienen entidad, condicion y vigencia |
| B-011 | P1 | Ruta | Crear archivo de sucursales con coordenadas oficiales | Permite rutas reales | Media | auditoria fuentes | `config/locales_san_juan.yml` validado |
| B-012 | P1 | Ruta | Agregar distancia estimada y costo de traslado | Recomendacion mas realista | Alta | locales_san_juan | Ruta muestra ahorro neto aproximado |
| B-013 | P1 | Automatizacion | Mejorar logs por scraper y resumen diario | Facilita mantenimiento | Media | run_pipeline | Log incluye fuente, estado, records, error |
| B-014 | P1 | Scraping | Auditar tienda de La Cumbre y Cabral por precio estructurado | Amplia cobertura local | Alta | fuentes oficiales | Diagnostico tecnico por fuente |
| B-015 | P1 | Catalogos | Parsear PDFs/flyers oficiales con texto u OCR local | Captura promociones locales | Alta | catalog links | Promos salen con fuente y confianza |
| B-016 | P2 | Dashboard | Mejorar visual BI/SaaS sin cambiar arquitectura | Aumenta adopcion | Media | contrato estable | UI validada desktop/mobile |
| B-017 | P2 | Busqueda | Agregar sugerencias por diccionario propio | Reduce friccion | Media | matching | Autocomplete no duplica productos |
| B-018 | P2 | Persistencia | Exportar/importar listas guardadas | Facilita uso recurrente | Baja | UX listas | Usuario recupera listas entre navegadores |
| B-019 | P2 | Monitoreo | Reporte de fuentes caidas o sin datos recientes | Evita usar datos viejos | Media | scrape_runs | Dashboard muestra freshness por fuente |
| B-020 | P2 | Seguridad | Automatizar escaneo de secretos y archivos grandes | Reduce riesgo operativo | Baja | Git limpio | Checklist ejecutable |
| B-021 | P3 | Legacy | Limpiar `data/raw` antiguo con politica de retencion | Reduce peso del proyecto | Baja | aprobacion usuario | Archivos movidos/borrados con inventario |
| B-022 | P3 | Packaging | Crear script de setup local | Facilita entrega | Media | sprints estables | Setup instala y valida en Windows |
| B-023 | P3 | Docs | Mantener changelog por sprint | Trazabilidad | Baja | disciplina Sprint | Cada sprint tiene entrada |
| B-024 | P3 | Performance | Reducir peso de JSON visible con indices/busqueda local optimizada | Mejora carga dashboard | Media | contrato estable | Dashboard carga mas rapido sin perder datos |

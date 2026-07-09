# Estrategia de fuentes oficiales

Actualizado: 2026-07-08.

## Regla central

El comparador debe decidir compras con datos de fuentes oficiales. SEPA / Precios Claros queda fuera del pipeline. Directorios, Google Maps, buscadores, PedidosYa y agregadores sirven para descubrir locales o contrastar presencia, pero no para fijar precios finales salvo revision manual y trazabilidad explicita.

## Prioridad de extraccion

1. API publica del ecommerce oficial.
2. HTML publico del ecommerce oficial.
3. Catalogo PDF o imagen oficial por sucursal/provincia.
4. Pagina oficial de ofertas y promociones bancarias.
5. Canal oficial verificable de la cadena: web propia, Instagram/Facebook oficial, Linktree oficial, WhatsApp Channel publico.
6. Agregador/directorio solo como pista de descubrimiento.

## Fuentes implementadas

| Cadena | Metodo actual | Estado |
|---|---|---|
| Vea | API publica VTEX `api/catalog_system/pub/products/search` | Implementado |
| Carrefour | API publica VTEX `api/catalog_system/pub/products/search` | Implementado |
| ChangoMas / MasOnline | API publica VTEX por `productClusterIds` historicos | Implementado |
| Atomo Conviene | HTML oficial `.card-body`, `.product-title`, `.price` | Implementado |
| Maxiconsumo San Juan | HTML Magento oficial `sucursal_san_juan` | Implementado |
| La Anonima San Juan | Sucursal oficial y catalogos | Catalogo oficial |
| Yaguar San Juan | Pagina oficial San Juan, catalogos y promociones bancarias | Catalogo oficial |
| Cafe America Mayorista | Pagina oficial y ofertas publicas | Catalogo oficial |
| Makro San Juan | Pagina oficial de ofertas San Juan | Catalogo oficial |
| Cabral Mayorista | Web oficial y sucursales oficiales | Pendiente precios |
| La Cumbre Sanjuanina | Web oficial y tienda propia enlazada | Pendiente precios |
| La Nobleza Mayorista | Instagram/Facebook oficiales | Pendiente flyers |
| La Estrella Mayorista | Instagram/Facebook oficiales | Pendiente flyers |
| Basualdo Mayorista | Linktree oficial con folleto nacional | Catalogo oficial |

## Pendientes recomendados

1. Probar si la tienda de La Cumbre expone HTML/JSON publico con precios.
2. Buscar tienda, folleto o publicaciones oficiales scrapeables de Cabral.
3. Descargar flyers oficiales de La Nobleza y La Estrella y aplicar OCR local marcado con menor confianza.
4. Convertir folletos de Yaguar, Makro, La Anonima y Basualdo en productos/promos estructurados si el PDF/imagen trae precios legibles.
5. Crear `config/locales_san_juan.yml` con sucursales oficiales y coordenadas para mejorar rutas.

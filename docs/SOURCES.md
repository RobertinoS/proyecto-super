# Fuentes

Actualizado: 2026-07-08.

## Politica actual

El dashboard usa como fuente operativa solo paginas oficiales, tiendas oficiales, catalogos oficiales o canales sociales oficiales verificables. SEPA / Precios Claros fue retirado del pipeline, de la configuracion y de la base sincronizada.

PedidosYa, GEOSanJuan, buscadores, Google Maps y directorios similares se usan solo como descubrimiento o contraste de presencia/localidad. No se consideran fuente primaria de precio final.

## Resumen tecnico

| Fuente | URL | Metodo | Estado | Precios estructurados | Promos/catalogos | Confianza |
|---|---|---|---|---:|---:|---:|
| Atomo Conviene | https://www.atomoconviene.com/atomo-ecommerce | HTML oficial | Implementado | si | si | 88 |
| ChangoMas / MasOnline | https://www.masonline.com.ar/ | API publica VTEX | Implementado | si | si | 95 |
| Vea | https://www.vea.com.ar/ | API publica VTEX | Implementado | si | si | 95 |
| Carrefour | https://www.carrefour.com.ar/ | API publica VTEX | Implementado | si | si | 95 |
| Maxiconsumo San Juan | https://www.maxiconsumo.com/sucursal_san_juan | HTML Magento oficial | Implementado | si | si | 72 |
| La Anonima San Juan | https://www.laanonima.com.ar/empresa/sucursales/381-san-juan | Sucursal/catalogo oficial | Verificada, catalogo | no | si | 88 |
| Yaguar San Juan | https://yaguar.com.ar/san-juan/catalogos-y-ofertas/ | Catalogos oficiales | Catalogo | no | si | 88 |
| Cafe America | https://www.americamayorista.com/ | Web/ofertas oficiales | Catalogo | no | si | 82 |
| Makro San Juan | https://makro.com.ar/ofertas/san-juan/ | Catalogo oficial | Catalogo | no | si | 78 |
| Cabral Mayorista | https://cabralmayorista.com/ | Web oficial + redes | Verificada, pendiente precios | no | si | 82 |
| La Cumbre Sanjuanina | https://lacumbresanjuanina.com.ar/ | Web oficial + tienda propia | Verificada, pendiente precios | no | si | 82 |
| La Nobleza Mayorista | https://www.instagram.com/lanoblezamayorista/ | Redes oficiales | Verificada, pendiente flyers | no | si | 68 |
| La Estrella Mayorista | https://www.instagram.com/laestrellamayorista.ar/ | Redes oficiales | Verificada, pendiente flyers | no | si | 65 |
| Basualdo Mayorista | https://linktr.ee/basualdomayorista | Linkhub/redes/folleto oficial | Catalogo | no | si | 70 |

## Fuentes con precio estructurado

Vea, Carrefour y MasOnline usan endpoints publicos de ecommerce oficial. Atomo y Maxiconsumo se procesan desde HTML oficial con parsing conservador. Cada registro mantiene `source_id`, URL, fecha de captura y `confidence_score`.

## Fuentes de catalogos, promociones y tarjetas

Yaguar, Makro, Cafe America, La Anonima, Cabral, La Cumbre, La Nobleza, La Estrella y Basualdo se monitorean para enlaces oficiales de catalogo, promociones, sucursales, tiendas o redes. Mientras no haya producto-precio estructurado, el dashboard los muestra como material de decision/promocion y no como precio comparable automatico.

## Locales detectados para backlog

GEOSanJuan lista 58 items en la categoria Supermercados y Mayoristas, incluyendo Cabral, Cafe America, Carrefour, ChangoMas, La Nobleza, Maxiconsumo, Makro, Yaguar, Vea, Atomo, Roberto Basualdo, Super Libertad/Hiper Libertad, Supermercado Espeleta, Polar, Verano, tu Super y Tulum Market. Es util para cobertura geográfica, pero cada local debe pasar por verificacion oficial antes de entrar al dashboard.

## Uso de PedidosYa

PedidosYa puede aportar presencia de tiendas y categorias visibles, por ejemplo Hiper Libertad San Juan. Se mantiene como referencia secundaria porque no siempre representa el canal oficial de precios de la cadena, puede tener precios de delivery y suele requerir renderizado/control de disponibilidad por zona.

## Politica de scraping aplicada

- User-Agent identificable.
- Timeouts.
- Reintentos moderados.
- Pausa entre requests.
- Cache raw en `data/raw/<fuente>/`.
- Salida procesada en `data/processed/<fuente>/`.
- Sin login, cookies privadas, captcha, paywall, proxies ni endpoints internos.

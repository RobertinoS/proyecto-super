# Auditoria de fuentes San Juan

Actualizado: 2026-07-08.

## Criterio

Una cadena entra al comparador automatico solo si tiene fuente oficial de precio o catalogo/promocion verificable. Los directorios y marketplaces se usan para descubrir, no para decidir precio final.

## Fuentes confirmadas o candidatas

| Cadena/local | Evidencia principal | Tipo | Estado operativo | Proximo paso |
|---|---|---|---|---|
| Atomo Conviene | https://www.atomoconviene.com/atomo-ecommerce | Ecommerce oficial | Precio implementado | Refinar sucursal/localidad |
| ChangoMas / MasOnline | https://www.masonline.com.ar/ | Ecommerce oficial | Precio implementado | Validar CP/sucursal San Juan |
| Vea | https://www.vea.com.ar/ | Ecommerce oficial | Precio implementado | Validar CP/sucursal San Juan |
| Carrefour | https://www.carrefour.com.ar/ | Ecommerce oficial | Precio implementado | Validar sucursal 123 San Juan |
| Maxiconsumo | https://www.maxiconsumo.com/sucursal_san_juan | Ecommerce oficial | Precio implementado | Controlar cambios HTML |
| La Anonima | https://www.laanonima.com.ar/empresa/sucursales/381-san-juan | Sucursal oficial | Catalogo/promos | Probar seleccion de sucursal y precios |
| Yaguar | https://yaguar.com.ar/san-juan/catalogos-y-ofertas/ | Catalogo oficial | Catalogo/promos | Parsear PDF/imagenes |
| Makro | https://makro.com.ar/ofertas/san-juan/ | Catalogo oficial | Catalogo/promos | Parsear PDF/imagenes |
| Cafe America | https://www.americamayorista.com/ | Web/ofertas oficiales | Catalogo/promos | Revisar pagina de ofertas y redes |
| Cabral Mayorista | https://cabralmayorista.com/sucursales/ | Web oficial | Verificado, pendiente precio | Buscar folletos o endpoint oficial |
| La Cumbre Sanjuanina | https://lacumbresanjuanina.com.ar/ | Web oficial + tienda | Verificado, pendiente precio | Auditar tienda propia enlazada |
| La Nobleza | https://www.instagram.com/lanoblezamayorista/ | Red oficial | Verificado, pendiente OCR | Descargar flyers oficiales si son publicos |
| La Estrella | https://www.instagram.com/laestrellamayorista.ar/ | Red oficial | Verificado, pendiente OCR | Descargar flyers oficiales si son publicos |
| Basualdo | https://linktr.ee/basualdomayorista | Linkhub oficial | Catalogo/promos | Parsear folleto nacional y validar vigencia San Juan |

## Cobertura descubierta por directorio

GEOSanJuan lista 58 items en Supermercados y Mayoristas. Entre los relevantes para el backlog aparecen Cabral Express, Cabral Mayorista, Cafe America, Carrefour Market, ChangoMas, Hiper ChangoMas, La Nobleza, Maxiconsumo, Makro, Yaguar, Roberto Basualdo, Super Libertad/Hiper Libertad, varias sucursales Vea, varias Atomo, Espeleta, Polar, Verano, tu Super y Tulum Market.

Accion: crear una segunda etapa de verificacion para los locales sin fuente oficial clara. Hasta entonces no entran al calculo automatico.

## PedidosYa

PedidosYa muestra al menos presencia de Hiper Libertad San Juan. Puede servir para confirmar categorias/tienda y eventualmente comparar disponibilidad delivery, pero no como verdad principal de precio porque los precios pueden variar por comision, delivery o zona.

## Decisiones tomadas

- SEPA / Precios Claros retirado de `config/fuentes.yml`, `run_pipeline.py`, tests y parser.
- La base se sincroniza con las fuentes configuradas y elimina registros de fuentes retiradas.
- El dashboard exporta solo fuentes oficiales/canales oficiales configurados.

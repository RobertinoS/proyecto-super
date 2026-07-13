# Auditoria de fuentes oficiales para piloto cloud

Fecha tecnica: 2026-07-13. Se realizaron consultas minimas, secuenciales y con User-Agent identificable. No se uso login, CAPTCHA, Playwright, cookies privadas ni scraping masivo.

## Matriz ejecutiva

| Cadena | San Juan | Acceso | Datos | Proteccion observada | Dificultad | Conclusion |
|---|---|---|---|---|---|---|
| Atomo | cadena presente, pero ecommerce auditado entrega/retiro en Mendoza | HTML publico | nombre, precio, stock, promo | `robots.txt` devolvio homepage, no reglas legibles | media, alto riesgo de atribucion geografica | no recomendable para piloto San Juan |
| Vea | sitio oficial publica region San Juan | JSON VTEX publico sin login | SKU, EAN, marca, categorias, precio, stock, promos | robots no bloquea endpoint; sin CAPTCHA | baja-media | **viable con condiciones; piloto** |
| Carrefour | sucursal oficial San Juan, General Acha 32 norte | web publica; endpoint catalogo respondio 403 al auditor | sitio muestra productos, API no accesible de forma estable | robots y control 403 | media-alta | viable con condiciones, no piloto |
| ChangoMas | cadena nacional; sucursal/CP San Juan pendiente de evidencia tecnica estable | JSON VTEX publico sin login | SKU, EAN, marca, categorias, precio, stock | robots no bloquea API; sin CAPTCHA | baja-media | viable con condiciones |

## Atomo

- Oficial: [Atomo Online](https://atomoconviene.com/atomo-ecommerce/).
- Acceso sin login: catalogo visible; checkout requiere cuenta/domicilio.
- Sucursal/domicilio: la tienda auditada muestra retiro en Juan M. Estrada 1136, Guaymallen, Mendoza; no se encontro selector reproducible de San Juan.
- HTML/JSON: respuesta publica renderiza tarjetas con `product-title`; la cabecera fue atipica (`application/json` con HTML).
- Paginacion y busqueda: categorias y `?page=N`; ofertas publicas.
- Campos: producto, presentacion en nombre, precio, stock visible; SKU/EAN no comprobados en esta auditoria.
- Promociones: las [preguntas frecuentes](https://atomoconviene.com/atomo-ecommerce/content/14-preguntas-frecuentes) declaran stock online y ofertas; los [terminos](https://atomoconviene.com/atomo-ecommerce/content/3-terminos-y-condiciones) describen precio vigente, promociones por volumen y condiciones.
- Robots/terminos: `/robots.txt` no entrego un archivo robots valido; no se interpreta como permiso amplio.
- Riesgo: alto riesgo de atribuir a San Juan precios de ecommerce Mendoza.
- Conclusion: no recomendable como piloto San Juan hasta hallar storefront/sucursal oficial local.

## Vea

- Oficial: [Vea](https://www.vea.com.ar/).
- Presencia San Juan: la pagina oficial de [horarios regionales](https://www.vea.com.ar/horarios-especiales-fiestas) incluye SAN JUAN.
- Acceso: catalogo y endpoint VTEX publico sin login ni cookies privadas.
- Endpoint auditado: `https://www.vea.com.ar/api/catalog_system/pub/products/search/almacen?_from=0&_to=0` respondio HTTP 206 con JSON.
- Campos observados: `productId`, `productName`, marca, categorias, SKU, EAN, `Price`, `ListPrice`, stock y teasers.
- Renderizado/paginacion: storefront JavaScript; API paginada con `_from`/`_to`.
- Promociones/medio de pago: teasers e installments pueden existir; deben conservarse como condicion, no inferirse.
- Sucursal: el endpoint auditado no prueba precio de una sucursal fisica. Se etiqueta `canal_precio=ONLINE`, `sucursal=Online nacional`.
- Calidad: se observo un `ListPrice` desproporcionado; el adaptador descarta lista mayor a 5x `Price` y usa `Price` como regular, dejando el control sujeto a tests.
- Robots: [robots.txt](https://www.vea.com.ar/robots.txt) no bloquea el endpoint de catalogo; si cambian las reglas se detiene el extractor.
- Conclusion: viable con condiciones y mejor candidato por estructura, bajo costo y relevancia.

## Carrefour

- Oficial: [Carrefour Argentina](https://www.carrefour.com.ar/).
- Presencia: el listado oficial de [sucursales](https://comerciante.carrefour.com.ar/sucursales) incluye SAN JUAN, General Acha 32 norte.
- Acceso: web publica; consulta minima al endpoint VTEX de catalogo devolvio HTTP 403 con User-Agent identificable.
- Datos potenciales: storefront muestra producto, marca, categoria y precios; endpoint no fue consumido tras el 403.
- Robots: [robots.txt](https://www.carrefour.com.ar/robots.txt) bloquea login, checkout, busca y vistas internas; no bloquea explicitamente catalog API, pero el 403 se respeta.
- Sucursal/canal: requiere confirmar seleccion de tienda/CP y trade policy.
- Conclusion: viable con condiciones, no recomendable como piloto hasta disponer de un acceso publico estable sin evasion.

## ChangoMas / MasOnline

- Oficial: [MasOnline](https://www.masonline.com.ar/) y [sucursales](https://www.masonline.com.ar/sucursales/).
- Acceso: endpoint VTEX publico sin login ni cookies privadas.
- Endpoint auditado: `https://www.masonline.com.ar/api/catalog_system/pub/products/search?_from=0&_to=0` respondio HTTP 206 con JSON.
- Campos: producto, marca, categorias, SKU, EAN, `Price`, `ListPrice`, stock y teasers.
- Seleccion: el [contacto oficial](https://www.masonline.com.ar/contacto) indica seleccion de sucursal para PickUp; falta reproducir una sucursal San Juan sin estado privado.
- Robots: [robots.txt](https://www.masonline.com.ar/robots.txt) no bloquea el endpoint; bloquea cuenta, login y checkout.
- Conclusion: viable con condiciones; segundo candidato una vez resuelta la sucursal.

## Seleccion del piloto

Vea obtiene la mejor combinacion reproducible: fuente oficial, presencia San Juan documentada, JSON publico, sin login/CAPTCHA, estructura rica y sin navegador automatizado. La limitacion se hace explicita: el piloto representa precio `ONLINE`, no precio fisico por sucursal. Publicar para decisiones reales exige validar cobertura por CP/sucursal y revisar terminos vigentes.

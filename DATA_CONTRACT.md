# Contrato de datos

Este contrato define los campos minimos que deben respetar la base, el export JSON y el dashboard.

## Fuente

Campo minimo:

- `source_id`: string estable.
- `name`: nombre visible.
- `source_type`: `official_ecommerce`, `official_catalog`, `official_social`, `official_website_store`, `official_linkhub_social` u otro documentado.
- `base_url`: URL principal.
- `status`: `implemented`, `catalog_only`, `source_verified_pending_prices`, `source_verified_catalog_only`, `disabled`.
- `has_prices`: boolean.
- `has_promotions`: boolean.
- `confidence_score`: entero 0-100.
- `notes`: texto breve.

Reglas:

- Una fuente sin precio estructurado no debe alimentar comparacion automatica de precio.
- Directorios, mapas y marketplaces son referencia secundaria salvo aprobacion explicita.

## Sucursal

Campo minimo:

- `store_id`: string estable.
- `source_id`: fuente.
- `chain`: cadena.
- `branch_name`: sucursal.
- `province`: debe ser `San Juan` para datos locales.
- `city`: ciudad/departamento si se conoce.
- `address`: direccion.
- `latitude`, `longitude`: opcional hasta Sprint 5.
- `active`: boolean.

Reglas:

- Si falta coordenada, no calcular distancia real.
- Si la fuente depende de ubicacion, marcarlo en `sources.requires_location`.

## Producto

Campo minimo:

- `product_id`: string estable.
- `source_product_id`: id externo si existe.
- `ean`: opcional.
- `name_raw`: nombre original.
- `name_clean`: nombre normalizado.
- `brand`: marca si se detecta.
- `category`: categoria normalizada.
- `presentation_qty`: cantidad original.
- `presentation_unit`: unidad original.
- `normalized_unit`: `kg`, `l`, `un` u otra documentada.
- `source_id`: fuente.
- `search_key`: clave de busqueda.

Reglas:

- Producto valido requiere nombre no vacio.
- Para comparar por unidad, debe existir presentacion comparable.
- No inferir equivalencia fuerte solo por texto parecido.

Ejemplo:

```json
{
  "name_raw": "Cafe Molido 750 g",
  "name_clean": "cafe molido 750 g",
  "brand": "GENERIC",
  "presentation_qty": 750,
  "presentation_unit": "g",
  "normalized_unit": "kg"
}
```

## Precio

Campo minimo:

- `capture_date`: fecha ISO.
- `source_id`: fuente.
- `store_id`: sucursal si existe.
- `product_id`: producto.
- `chain`: cadena.
- `branch_name`: sucursal.
- `city`: ciudad.
- `product_name_raw`: nombre original.
- `product_name_clean`: nombre limpio.
- `brand`: marca.
- `category`: categoria.
- `price_list`: precio lista.
- `price_promo_1`: promo general.
- `promo_1_text`: texto promo general.
- `price_promo_2`: promo condicional.
- `promo_2_text`: texto promo condicional.
- `best_general_price`: mejor precio no condicional.
- `best_conditional_price`: mejor precio condicional.
- `reference_price`: precio por kg/l/un cuando sea posible.
- `reference_unit`: unidad de referencia.
- `url`: fuente exacta.
- `confidence_score`: entero 0-100.

Reglas de calidad:

- Precio valido: numero positivo y razonable para la categoria.
- Precio sospechoso: nulo, cero, negativo, extremadamente bajo o alto contra pares.
- `best_general_price` no debe usar promo condicional.
- `best_conditional_price` debe mostrarse con condicion.
- Todo precio debe conservar fuente y fecha.

## Promocion

Campo minimo:

- `source_id`.
- `chain`.
- `category`.
- `product_name`.
- `price_list`.
- `best_price`.
- `conditional_price`.
- `discount_amount`.
- `discount_pct`.
- `promo_text`.
- `offer_type`: `precio`, `volumen`, `tarjeta`, `catalogo`, `otro`.
- `url`.
- `capture_date`.

Reglas:

- Promocion condicional no se mezcla con precio final general.
- Catalogos oficiales pueden aparecer sin precio estructurado.
- Vigencia debe agregarse cuando la fuente la exponga.

## Tarjeta o medio de pago

Campo minimo:

- `chain`.
- `source_id`.
- `title`.
- `category`.
- `product_name`.
- `discount_pct`.
- `conditional_price`.
- `url`.
- `confidence_score`.
- `capture_date`.

Reglas:

- Debe distinguir banco, tarjeta, billetera, cuotas y tope si se conocen.
- Si faltan condiciones, mostrar como enlace oficial a revisar.

## Lista de compra

Campo minimo:

- `list_id`: id local.
- `name`: nombre de lista.
- `items`: lista.
- `created_at`.
- `updated_at`.

Item minimo:

- `term`: texto ingresado.
- `qty`: cantidad positiva.
- `unit_preference`: opcional.
- `brand_preference`: opcional.

Reglas:

- Cantidad debe multiplicar subtotal.
- Item sin match debe informarse como faltante.

Ejemplo:

```json
{
  "name": "Compra mensual",
  "items": [
    {"term": "cafe 750g", "qty": 2},
    {"term": "leche larga vida 1l", "qty": 3}
  ]
}
```

## Resultado de ruta

Campo minimo:

- `items_found`.
- `items_missing`.
- `recommended_stores`.
- `route_total`.
- `best_single_chain`.
- `best_single_total`.
- `estimated_savings`.
- `assumptions`.

Reglas:

- Hasta tener coordenadas, la ruta es economica, no geografica.
- Cuando se agreguen distancias, mostrar ahorro neto o advertir que no incluye traslado.

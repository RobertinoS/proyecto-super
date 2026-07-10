# Estado del proyecto

Actualizado: 2026-07-10.

## Sprint actual

Sprint 3 - Matching de productos y precio comparable.

Rama:

```text
sprint-3-product-matching
```

Objetivo: agrupar productos equivalentes o similares por nombre, marca, categoria, presentacion y unidad para comparar precios por unidad base.

## Diagnostico ejecutivo

El repo Git dedicado esta en:

```text
C:\Users\Rober\Desktop\Proyecto Super
```

Sprint 1 y Sprint 2 estan preservados. El dashboard local no fue reemplazado: ahora acepta CSV normalizado simple o CSV matcheado. Si detecta columnas de matching, ordena por precio unitario comparable y muestra grupo, confianza y comercio ganador por grupo.

## Flujo actual

```text
data/sample/sepa/sepa_precios_simulado.csv
        -> scripts/03_filtrar_san_juan.py
        -> data/processed/precios_san_juan_sepa.csv
        -> scripts/04_matching_productos.py
        -> data/processed/precios_matcheados.csv
        -> dashboard/index.html
```

## Artefactos Sprint 3

- `scripts/04_matching_productos.py`
- `data/sample/product_dictionary.csv`
- `tests/test_product_matching.py`
- `data/processed/precios_matcheados.csv` generado localmente
- `data/processed/precios_matcheados_reporte.json` generado localmente

## Decision tecnica

- Solucion local, costo 0 y sin credenciales.
- Primero reglas deterministicas y diccionario editable.
- Sin modelos de IA ni APIs externas.
- `grupo_comparacion` sale del diccionario cuando hay match manual.
- Si no hay match manual, se usa fallback heuristico por categoria, marca, producto normalizado, cantidad y unidad.
- `confianza_matching` es alta para diccionario (`0.95`) y menor para heuristica.

## Validaciones Sprint 3

El matching:

- Normaliza mayusculas/minusculas.
- Elimina tildes.
- Limpia espacios y simbolos.
- Interpreta `kg`, `kilo`, `kilos`, `1000 g`.
- Interpreta `g`, `gr`, `gramos`.
- Interpreta `l`, `litro`, `litros`, `1000 ml`.
- Interpreta `ml`, `cc`.
- Interpreta `x`, `por`, `pack`.
- Calcula precio por `kg`, `l` o `un`.
- Evita agrupar variantes parecidas pero no equivalentes, como comun/zero, entera/descremada e integral/largo fino.

## Resultados actuales

Con el sample SEPA:

- Filas matcheadas: 32.
- Grupos comparables: 7.
- Entradas de diccionario: 12.
- Confianza promedio: 0.95.

Grupos detectados:

- `aceite_girasol_cocinero_900ml`
- `arroz_largo_fino_gallo_1kg`
- `azucar_comun_ledesma_1kg`
- `cafe_molido_la_morenita_750g`
- `fideos_spaghetti_matarazzo_500g`
- `leche_entera_la_serenisima_1l`
- `yerba_mate_playadito_1kg`

## Pruebas ejecutadas

```bash
python -m py_compile scripts/04_matching_productos.py
python scripts/03_filtrar_san_juan.py --input data/sample/sepa/sepa_precios_simulado.csv
python scripts/04_matching_productos.py
python -m pytest
```

Resultados:

- Compilacion Python: OK.
- Filtro San Juan: OK, 32 filas San Juan.
- Matching: OK, 32 filas, 7 grupos, confianza promedio 0.95.
- `python -m pytest`: 17 passed.

## Riesgos y pendientes

- El diccionario debe crecer con productos reales y variantes encontradas en scraping.
- Las equivalencias por sabor, variedad o calidad requieren reglas mas finas para evitar falsos positivos.
- Falta distinguir promociones, packs temporales y descuentos de tarjeta en el precio comparable.
- Falta calcular ahorro por lista de compra y ruta optima.

## Proximo sprint recomendado

Sprint 4 - Listas de compra y ahorro.

Objetivo: permitir que el usuario arme o guarde listas, comparar costo total por comercio/ruta y estimar ahorro usando precios unitarios comparables.

import csv
import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "05_calcular_lista_compra.py"

PRICE_COLUMNS = [
    "comercio",
    "sucursal",
    "localidad",
    "producto",
    "marca",
    "categoria",
    "presentacion",
    "precio",
    "fecha_relevamiento",
    "fuente",
    "cantidad_base",
    "unidad_base",
    "precio_unitario_comparable",
    "grupo_comparacion",
    "confianza_matching",
]

LIST_COLUMNS = [
    "item_lista",
    "grupo_comparacion",
    "cantidad",
    "unidad",
    "prioridad",
]

COMPARISON_COLUMNS = [
    "comercio",
    "productos_encontrados",
    "productos_faltantes",
    "cobertura_lista_pct",
    "costo_total_estimado",
    "diferencia_vs_mas_barato",
    "ahorro_vs_mas_caro",
    "ranking_precio",
]

BEST_COLUMNS = [
    "item_lista",
    "grupo_comparacion",
    "comercio_recomendado",
    "producto_encontrado",
    "precio_final",
    "precio_unitario_comparable",
    "ahorro_vs_promedio",
    "confianza_matching",
]


def load_module():
    spec = importlib.util.spec_from_file_location("calcular_lista_compra", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_csv(path, rows, fieldnames):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def price_row(comercio, producto, group, precio, comparable, quantity, unit, confidence="0.95"):
    return {
        "comercio": comercio,
        "sucursal": f"{comercio} Centro",
        "localidad": "Capital",
        "producto": producto,
        "marca": "Marca Test",
        "categoria": "Almacen",
        "presentacion": f"{quantity} {unit}",
        "precio": str(precio),
        "fecha_relevamiento": "2026-07-10",
        "fuente": "test",
        "cantidad_base": str(quantity),
        "unidad_base": unit,
        "precio_unitario_comparable": str(comparable),
        "grupo_comparacion": group,
        "confianza_matching": confidence,
    }


def shopping_row(item, group, quantity, unit, priority="media"):
    return {
        "item_lista": item,
        "grupo_comparacion": group,
        "cantidad": str(quantity),
        "unidad": unit,
        "prioridad": priority,
    }


def sample_prices():
    return [
        price_row("Comercio A", "Yerba Playadito 1kg", "yerba_mate_playadito_1kg", 1000, 1000, 1, "kg"),
        price_row("Comercio A", "Leche entera 1L", "leche_entera_la_serenisima_1l", 1200, 1200, 1, "l"),
        price_row("Comercio A", "Fideos spaghetti 500g", "fideos_spaghetti_matarazzo_500g", 900, 1800, 0.5, "kg"),
        price_row("Comercio B", "Yerba Playadito 1000 g", "yerba_mate_playadito_1kg", 900, 900, 1, "kg"),
        price_row("Comercio B", "Leche entera 1L", "leche_entera_la_serenisima_1l", 1150, 1150, 1, "l"),
        price_row("Comercio C", "Yerba Mate Playadito x 1 kilo", "yerba_mate_playadito_1kg", 1300, 1300, 1, "kg"),
        price_row("Comercio C", "Leche entera 1L", "leche_entera_la_serenisima_1l", 1300, 1300, 1, "l"),
        price_row("Comercio C", "Fideos spaghetti 500g", "fideos_spaghetti_matarazzo_500g", 1000, 2000, 0.5, "kg"),
    ]


def sample_list():
    return [
        shopping_row("Yerba Playadito 1kg", "yerba_mate_playadito_1kg", 1, "kg", "alta"),
        shopping_row("Leche entera 1L", "leche_entera_la_serenisima_1l", 1, "l", "alta"),
        shopping_row("Fideos spaghetti 500g", "fideos_spaghetti_matarazzo_500g", 500, "g", "media"),
    ]


def test_load_shopping_list_converts_units(tmp_path):
    module = load_module()
    list_path = tmp_path / "lista.csv"
    write_csv(
        list_path,
        [
            shopping_row("Fideos 500g", "fideos_spaghetti_matarazzo_500g", 500, "g"),
            shopping_row("Aceite 900ml", "aceite_girasol_cocinero_900ml", 900, "ml"),
        ],
        LIST_COLUMNS,
    )

    items = module.load_shopping_list(list_path)

    assert items[0].cantidad == 0.5
    assert items[0].unidad == "kg"
    assert items[1].cantidad == 0.9
    assert items[1].unidad == "l"


def test_calculate_costs_missing_products_ranking_and_split(tmp_path):
    module = load_module()
    prices_path = tmp_path / "precios_matcheados.csv"
    list_path = tmp_path / "lista.csv"
    comparison_path = tmp_path / "comparacion_lista_compra.csv"
    best_path = tmp_path / "mejor_compra_por_producto.csv"
    write_csv(prices_path, sample_prices(), PRICE_COLUMNS)
    write_csv(list_path, sample_list(), LIST_COLUMNS)

    report = module.calculate_shopping_list(prices_path, list_path, comparison_path, best_path)

    assert report["items"] == 3
    assert report["commerces"] == 3
    assert comparison_path.exists()
    assert best_path.exists()

    comparison = read_csv(comparison_path)
    assert all(column in comparison[0] for column in COMPARISON_COLUMNS)
    assert [row["comercio"] for row in comparison] == ["Comercio A", "Comercio C", "Comercio B"]
    assert comparison[0]["costo_total_estimado"] == "3100.00"
    assert comparison[0]["diferencia_vs_mas_barato"] == "0.00"
    assert comparison[0]["ahorro_vs_mas_caro"] == "500.00"
    assert comparison[1]["costo_total_estimado"] == "3600.00"
    assert comparison[1]["diferencia_vs_mas_barato"] == "500.00"
    assert comparison[2]["cobertura_lista_pct"] == "66.67"
    assert "Fideos spaghetti 500g" in comparison[2]["productos_faltantes"]

    best = {row["item_lista"]: row for row in read_csv(best_path)}
    assert all(column in next(iter(best.values())) for column in BEST_COLUMNS)
    assert best["Yerba Playadito 1kg"]["comercio_recomendado"] == "Comercio B"
    assert best["Leche entera 1L"]["comercio_recomendado"] == "Comercio B"
    assert best["Fideos spaghetti 500g"]["comercio_recomendado"] == "Comercio A"
    assert best["Fideos spaghetti 500g"]["precio_final"] == "900.00"


def test_script_generates_processed_shopping_outputs():
    subprocess.run(
        [
            sys.executable,
            "scripts/03_filtrar_san_juan.py",
            "--input",
            "data/sample/sepa/sepa_precios_simulado.csv",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [sys.executable, "scripts/04_matching_productos.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        [sys.executable, "scripts/05_calcular_lista_compra.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    comparison = ROOT / "data" / "processed" / "comparacion_lista_compra.csv"
    best = ROOT / "data" / "processed" / "mejor_compra_por_producto.csv"
    assert comparison.exists()
    assert best.exists()
    assert all(column in read_csv(comparison)[0] for column in COMPARISON_COLUMNS)
    assert all(column in read_csv(best)[0] for column in BEST_COLUMNS)

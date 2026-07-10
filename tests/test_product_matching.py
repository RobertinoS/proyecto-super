import csv
import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "04_matching_productos.py"
REQUIRED_BASE_COLUMNS = [
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
]
MATCH_COLUMNS = [
    "cantidad_base",
    "unidad_base",
    "precio_unitario_comparable",
    "grupo_comparacion",
    "confianza_matching",
]


def load_module():
    spec = importlib.util.spec_from_file_location("matching_productos", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_rows(path, rows):
    fieldnames = REQUIRED_BASE_COLUMNS
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_rows(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def row(producto, marca, categoria, presentacion, precio):
    return {
        "comercio": "Vea",
        "sucursal": "Capital Centro",
        "localidad": "Capital",
        "producto": producto,
        "marca": marca,
        "categoria": categoria,
        "presentacion": presentacion,
        "precio": precio,
        "fecha_relevamiento": "2026-07-09",
        "fuente": "test",
    }


def test_normalize_text_removes_accents_case_and_symbols():
    matching = load_module()
    assert matching.normalize_text("  Yerba MÁTE   Playadito!!! ") == "yerba mate playadito"


def test_kg_and_1000g_are_equivalent():
    matching = load_module()
    kg = matching.extract_presentation("Yerba Mate Playadito 1 kilo")
    grams = matching.extract_presentation("Yerba Playadito 1000 g")
    assert kg.quantity == grams.quantity == 1
    assert kg.unit == grams.unit == "kg"


def test_liter_and_1000ml_are_equivalent():
    matching = load_module()
    liter = matching.extract_presentation("Aceite Cocinero 1 litro")
    ml = matching.extract_presentation("Aceite Cocinero 1000 ml")
    assert liter.quantity == ml.quantity == 1
    assert liter.unit == ml.unit == "l"


def test_unit_price_calculation_with_dictionary(tmp_path):
    matching = load_module()
    dictionary = matching.load_dictionary(ROOT / "data" / "sample" / "product_dictionary.csv")
    matched = matching.normalize_row(row("Cafe molido clasico", "La Morenita", "Desayuno", "750 g", "6000"), dictionary)
    assert matched["cantidad_base"] == "0.75"
    assert matched["unidad_base"] == "kg"
    assert matched["precio_unitario_comparable"] == "8000.00"
    assert matched["grupo_comparacion"] == "cafe_molido_la_morenita_750g"


def test_matching_preserves_required_columns_and_groups_variants(tmp_path):
    source = tmp_path / "precios.csv"
    output = tmp_path / "precios_matcheados.csv"
    report = tmp_path / "reporte.json"
    write_rows(
        source,
        [
            row("Yerba Mate Playadito 1kg", "Playadito", "Almacen", "", "3490"),
            row("Yerba Playadito 1000 g", "Playadito", "Almacen", "", "3520"),
            row("Playadito yerba mate x 1 kilo", "Playadito", "Almacen", "", "3400"),
        ],
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--input",
            str(source),
            "--dictionary",
            str(ROOT / "data" / "sample" / "product_dictionary.csv"),
            "--output",
            str(output),
            "--report",
            str(report),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    rows = read_rows(output)
    assert len(rows) == 3
    for column in REQUIRED_BASE_COLUMNS + MATCH_COLUMNS:
        assert column in rows[0]
    assert {item["grupo_comparacion"] for item in rows} == {"yerba_mate_playadito_1kg"}
    assert {item["unidad_base"] for item in rows} == {"kg"}
    assert {item["cantidad_base"] for item in rows} == {"1"}


def test_similar_but_different_products_do_not_share_group():
    matching = load_module()
    dictionary = matching.load_dictionary(ROOT / "data" / "sample" / "product_dictionary.csv")
    cases = [
        (
            row("Coca Cola comun 2.25L", "Coca Cola", "Bebidas", "2.25 l", "2500"),
            row("Coca Cola Zero 2.25L", "Coca Cola", "Bebidas", "2.25 l", "2550"),
        ),
        (
            row("Leche entera 1L", "La Serenisima", "Lacteos", "1 l", "1200"),
            row("Leche descremada 1L", "La Serenisima", "Lacteos", "1 l", "1180"),
        ),
        (
            row("Arroz largo fino 1kg", "Gallo", "Almacen", "1 kg", "1500"),
            row("Arroz integral 1kg", "Gallo", "Almacen", "1 kg", "1900"),
        ),
    ]

    for left, right in cases:
        left_matched = matching.normalize_row(left, dictionary)
        right_matched = matching.normalize_row(right, dictionary)
        assert left_matched["grupo_comparacion"] != right_matched["grupo_comparacion"]


def test_script_generates_processed_matched_csv():
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
    result = subprocess.run(
        [sys.executable, "scripts/04_matching_productos.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    output = ROOT / "data" / "processed" / "precios_matcheados.csv"
    assert output.exists()
    rows = read_rows(output)
    assert rows
    assert all(column in rows[0] for column in REQUIRED_BASE_COLUMNS + MATCH_COLUMNS)

import csv
import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "09_validar_precios_reales.py"
MATCHING_SCRIPT_PATH = ROOT / "scripts" / "04_matching_productos.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


validator = load_module(SCRIPT_PATH, "real_price_validator")
matching = load_module(MATCHING_SCRIPT_PATH, "product_matching")


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def valid_row(**overrides):
    row = {
        "comercio": "Vea",
        "sucursal": "Av Libertador",
        "localidad": "Capital",
        "direccion": "Av. Libertador 1250",
        "producto": "Yerba Mate Playadito 1 kg",
        "marca": "Playadito",
        "categoria": "Almacen",
        "presentacion": "1 kg",
        "precio": "3290",
        "fecha_relevamiento": "2026-07-10",
        "fuente": "manual_gondola",
        "observacion": "",
    }
    row.update(overrides)
    return row


def test_template_has_required_columns():
    template = ROOT / "data" / "sample" / "precios_reales_template.csv"
    with template.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        assert reader.fieldnames == validator.REQUIRED_COLUMNS


def test_demo_validation_generates_output_and_report(tmp_path):
    output = tmp_path / "precios_reales_validados.csv"
    report = tmp_path / "reporte_validacion_precios_reales.csv"

    summary = validator.validate_real_prices(
        ROOT / "data" / "sample" / "precios_reales_demo.csv",
        output,
        report,
    )

    assert summary["rows_read"] >= 20
    assert summary["rows_valid"] >= 20
    assert summary["rows_invalid"] >= 3
    assert output.exists()
    assert report.exists()
    assert set(validator.OUTPUT_COLUMNS).issubset(read_rows(output)[0].keys())

    issue_types = {row["tipo_error"] for row in read_rows(report)}
    assert {"precio_invalido", "fecha_invalida", "localidad_fuera_alcance", "duplicado", "precio_sospechoso"}.issubset(issue_types)


def test_invalid_price_and_invalid_date_are_reported(tmp_path):
    source = tmp_path / "input.csv"
    output = tmp_path / "output.csv"
    report = tmp_path / "report.csv"
    rows = [
        valid_row(),
        valid_row(producto="Manteca La Serenisima 200 g", presentacion="200 g", precio="abc"),
        valid_row(producto="Queso cremoso 1 kg", presentacion="1 kg", fecha_relevamiento="31/02/2026"),
    ]
    write_rows(source, validator.REQUIRED_COLUMNS, rows)

    summary = validator.validate_real_prices(source, output, report)
    issue_types = [row["tipo_error"] for row in read_rows(report)]

    assert summary["rows_valid"] == 1
    assert "precio_invalido" in issue_types
    assert "fecha_invalida" in issue_types


def test_missing_columns_fail_with_report(tmp_path):
    source = tmp_path / "missing.csv"
    output = tmp_path / "output.csv"
    report = tmp_path / "report.csv"
    fieldnames = [column for column in validator.REQUIRED_COLUMNS if column != "precio"]
    write_rows(source, fieldnames, [{"comercio": "Vea"}])

    with pytest.raises(ValueError, match="Faltan columnas obligatorias"):
        validator.validate_real_prices(source, output, report)

    assert read_rows(report)[0]["tipo_error"] == "columna_faltante"
    assert read_rows(report)[0]["campo"] == "precio"


def test_duplicates_are_reported_and_excluded(tmp_path):
    source = tmp_path / "duplicates.csv"
    output = tmp_path / "output.csv"
    report = tmp_path / "report.csv"
    write_rows(source, validator.REQUIRED_COLUMNS, [valid_row(), valid_row()])

    summary = validator.validate_real_prices(source, output, report)

    assert summary["rows_valid"] == 1
    assert summary["duplicates"] == 1
    assert read_rows(report)[0]["tipo_error"] == "duplicado"


def test_validated_prices_are_compatible_with_matching(tmp_path):
    source = tmp_path / "input.csv"
    validated = tmp_path / "precios_reales_validados.csv"
    validation_report = tmp_path / "reporte.csv"
    matched = tmp_path / "precios_reales_matcheados.csv"
    matching_report = tmp_path / "matching.json"
    rows = [
        valid_row(producto="Yerba Mate Playadito 1 kg", presentacion="1 kg", precio="3290"),
        valid_row(
            comercio="Carrefour",
            sucursal="Hiper Rawson",
            localidad="Rawson",
            producto="Yerba Playadito 1000 g",
            presentacion="1000 g",
            precio="3375",
        ),
    ]
    write_rows(source, validator.REQUIRED_COLUMNS, rows)

    validator.validate_real_prices(source, validated, validation_report)
    summary = matching.match_products(
        validated,
        ROOT / "data" / "sample" / "product_dictionary.csv",
        matched,
        matching_report,
    )
    matched_rows = read_rows(matched)

    assert summary["rows_written"] == 2
    assert matched_rows[0]["grupo_comparacion"]
    assert matched_rows[0]["precio_unitario_comparable"]

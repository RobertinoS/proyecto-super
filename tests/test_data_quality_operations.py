import csv
import importlib.util
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "10_generar_reporte_calidad_datos.py"
VALIDATOR_PATH = ROOT / "scripts" / "09_validar_precios_reales.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


quality = load_module(SCRIPT_PATH, "data_quality_operations")
validator = load_module(VALIDATOR_PATH, "real_price_validator_for_quality")


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def price_row(comercio, sucursal, localidad, producto, categoria, fecha, fila):
    return {
        "fila_origen": str(fila),
        "comercio": comercio,
        "sucursal": sucursal,
        "localidad": localidad,
        "producto": producto,
        "marca": "Marca",
        "categoria": categoria,
        "presentacion": "1 kg",
        "precio": "1000.00",
        "fecha_relevamiento": fecha,
        "fuente": "manual_gondola",
        "direccion": "Direccion demo",
        "observacion": "",
    }


def issue_row(fila, tipo_error, comercio, sucursal, localidad):
    return {
        "fila": str(fila),
        "campo": "precio",
        "tipo_error": tipo_error,
        "valor_detectado": "demo",
        "sugerencia": "revisar",
        "comercio": comercio,
        "sucursal": sucursal,
        "localidad": localidad,
    }


def build_quality_fixture(tmp_path: Path):
    prices = tmp_path / "precios_reales_validados.csv"
    validation_report = tmp_path / "reporte_validacion_precios_reales.csv"
    quality_output = tmp_path / "reporte_calidad_datos.csv"
    summary_output = tmp_path / "resumen_calidad_fuente.csv"

    price_rows = [
        price_row("Vea", "Centro", "Capital", "Yerba", "Almacen", "2026-07-10", 2),
        price_row("Carrefour", "Rawson", "Rawson", "Aceite", "Almacen", "2026-07-10", 3),
        price_row("Atomo", "Rivadavia", "Rivadavia", "Leche", "Lacteos", "2026-07-10", 4),
        price_row("ChangoMas", "Santa Lucia", "Santa Lucia", "Fideos", "Almacen", "2026-06-20", 5),
    ]
    issue_rows = [
        issue_row(3, "precio_sospechoso", "Carrefour", "Rawson", "Rawson"),
        issue_row(3, "duplicado", "Carrefour", "Rawson", "Rawson"),
        issue_row(4, "precio_invalido", "Atomo", "Rivadavia", "Rivadavia"),
    ]
    write_rows(prices, quality.OUTPUT_COLUMNS if hasattr(quality, "OUTPUT_COLUMNS") else [
        "fila_origen",
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
        "direccion",
        "observacion",
    ], price_rows)
    write_rows(validation_report, validator.REPORT_COLUMNS, issue_rows)
    return prices, validation_report, quality_output, summary_output


def row_by_key(rows, comercio):
    return next(row for row in rows if row["comercio"] == comercio)


def test_generates_quality_outputs_and_states(tmp_path):
    prices, validation_report, quality_output, summary_output = build_quality_fixture(tmp_path)

    report = quality.generate_quality_reports(
        prices,
        validation_report,
        quality_output,
        summary_output,
        date(2026, 7, 12),
    )
    detail_rows = read_rows(quality_output)
    summary_rows = read_rows(summary_output)

    assert report["groups"] == 4
    assert quality_output.exists()
    assert summary_output.exists()
    assert row_by_key(detail_rows, "Vea")["estado_calidad"] == "OK"
    assert row_by_key(detail_rows, "Carrefour")["estado_calidad"] == "REVISAR"
    assert row_by_key(detail_rows, "Atomo")["estado_calidad"] == "INVALIDO"
    assert row_by_key(detail_rows, "ChangoMas")["estado_calidad"] == "DESACTUALIZADO"
    assert row_by_key(summary_rows, "Vea")["estado_operativo"] == "OK"


def test_calculates_age_and_quality_score(tmp_path):
    prices, validation_report, quality_output, summary_output = build_quality_fixture(tmp_path)

    quality.generate_quality_reports(
        prices,
        validation_report,
        quality_output,
        summary_output,
        date(2026, 7, 12),
    )
    summary_rows = read_rows(summary_output)

    assert row_by_key(summary_rows, "Vea")["antiguedad_dias"] == "2"
    assert row_by_key(summary_rows, "ChangoMas")["antiguedad_dias"] == "22"
    assert int(row_by_key(summary_rows, "Vea")["score_calidad"]) == 100
    assert int(row_by_key(summary_rows, "Carrefour")["score_calidad"]) < 100
    assert int(row_by_key(summary_rows, "Atomo")["score_calidad"]) <= 45
    assert int(row_by_key(summary_rows, "ChangoMas")["score_calidad"]) <= 65


def test_is_compatible_with_sprint_10_validation_report(tmp_path):
    validated = tmp_path / "precios_reales_validados.csv"
    validation_report = tmp_path / "reporte_validacion_precios_reales.csv"
    quality_output = tmp_path / "reporte_calidad_datos.csv"
    summary_output = tmp_path / "resumen_calidad_fuente.csv"

    validator.validate_real_prices(
        ROOT / "data" / "sample" / "precios_reales_demo.csv",
        validated,
        validation_report,
    )
    report = quality.generate_quality_reports(
        validated,
        validation_report,
        quality_output,
        summary_output,
        date(2026, 7, 12),
    )
    detail_rows = read_rows(quality_output)
    states = {row["estado_calidad"] for row in detail_rows}

    assert report["groups"] >= 4
    assert {"REVISAR", "INVALIDO"}.issubset(states)
    assert any(row["precios_sospechosos"] == "1" for row in detail_rows)
    assert any(row["duplicados"] == "1" for row in detail_rows)

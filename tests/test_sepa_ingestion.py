import csv
import json
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_COLUMNS = [
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


def run_command(args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=False)


def read_csv(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_sepa_filter_sample_generates_dashboard_contract(tmp_path):
    output = tmp_path / "precios_san_juan_sepa.csv"
    errors = tmp_path / "errores.csv"
    report = tmp_path / "reporte.json"

    result = run_command(
        [
            sys.executable,
            "scripts/03_filtrar_san_juan.py",
            "--input",
            "data/sample/sepa/sepa_precios_simulado.csv",
            "--output",
            str(output),
            "--errors",
            str(errors),
            "--report",
            str(report),
        ]
    )

    assert result.returncode == 0, result.stderr or result.stdout
    rows = read_csv(output)
    assert rows
    assert list(rows[0].keys()) == EXPECTED_COLUMNS
    assert {"Capital", "Rawson", "Santa Lucia", "Rivadavia"}.issubset({row["localidad"] for row in rows})
    assert "Godoy Cruz" not in {row["localidad"] for row in rows}
    assert "Cordoba" not in {row["localidad"] for row in rows}
    assert {"Vea", "Carrefour", "ChangoMas"}.issubset({row["comercio"] for row in rows})
    assert all(float(row["precio"]) > 0 for row in rows)

    summary = json.loads(report.read_text(encoding="utf-8"))
    assert summary["rows_skipped_outside_san_juan"] == 2
    assert summary["errors"] == 0


def test_manual_zip_import_and_filter(tmp_path):
    sample = ROOT / "data/sample/sepa/sepa_precios_simulado.csv"
    zip_path = tmp_path / "sepa_manual.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.write(sample, arcname="sepa_precios_simulado.csv")

    raw_dir = tmp_path / "raw" / "sepa"
    import_result = run_command(
        [
            sys.executable,
            "scripts/01_descargar_o_importar_sepa.py",
            "--mode",
            "manual",
            "--input",
            str(zip_path),
            "--output-dir",
            str(raw_dir),
        ]
    )

    assert import_result.returncode == 0, import_result.stderr or import_result.stdout
    manifest = json.loads((raw_dir / "sepa_import_manifest.json").read_text(encoding="utf-8"))
    assert manifest["mode"] == "manual"
    assert manifest["files"][0]["role_guess"] == "desconocido"
    assert manifest["extracted"][0]["role_guess"] == "precios"

    output = tmp_path / "precios_zip.csv"
    filter_result = run_command(
        [
            sys.executable,
            "scripts/03_filtrar_san_juan.py",
            "--input",
            str(raw_dir / "manual" / zip_path.name),
            "--output",
            str(output),
            "--errors",
            str(tmp_path / "errores_zip.csv"),
            "--report",
            str(tmp_path / "reporte_zip.json"),
        ]
    )

    assert filter_result.returncode == 0, filter_result.stderr or filter_result.stdout
    assert len(read_csv(output)) >= 30


def test_official_like_split_pipe_zip_is_merged(tmp_path):
    source_dir = tmp_path / "split"
    source_dir.mkdir()
    (source_dir / "comercio.csv").write_text(
        "id_comercio|id_bandera|comercio_razon_social|comercio_bandera_nombre\n"
        "1|10|Cencosud S.A.|Vea\n",
        encoding="utf-8",
    )
    (source_dir / "sucursales.csv").write_text(
        "id_comercio|id_bandera|id_sucursal|sucursales_nombre|sucursales_localidad|sucursales_provincia\n"
        "1|10|1001|Capital Centro|Capital|AR-J\n"
        "1|10|1002|Mendoza Centro|Godoy Cruz|AR-M\n",
        encoding="utf-8",
    )
    (source_dir / "productos.csv").write_text(
        "id_comercio|id_bandera|id_sucursal|id_producto|productos_descripcion|productos_cantidad_presentacion|productos_unidad_medida_presentacion|productos_marca|productos_precio_lista\n"
        "1|10|1001|779001|Yerba mate suave|1|kg|Playadito|3490.00\n"
        "1|10|1002|779001|Yerba mate suave|1|kg|Playadito|3550.00\n",
        encoding="utf-8",
    )
    zip_path = tmp_path / "sepa_split.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        for path in source_dir.iterdir():
            archive.write(path, arcname=path.name)

    output = tmp_path / "precios_split.csv"
    result = run_command(
        [
            sys.executable,
            "scripts/03_filtrar_san_juan.py",
            "--input",
            str(zip_path),
            "--output",
            str(output),
            "--errors",
            str(tmp_path / "errores_split.csv"),
            "--report",
            str(tmp_path / "reporte_split.json"),
            "--fallback-date",
            "2026-07-09",
        ]
    )

    assert result.returncode == 0, result.stderr or result.stdout
    rows = read_csv(output)
    assert len(rows) == 1
    assert rows[0]["comercio"] == "Vea"
    assert rows[0]["sucursal"] == "Capital Centro"
    assert rows[0]["localidad"] == "Capital"
    assert rows[0]["presentacion"] == "1 kg"
    assert rows[0]["precio"] == "3490.00"


def test_sepa_filter_fails_with_missing_minimum_columns(tmp_path):
    bad_source = tmp_path / "bad.csv"
    bad_source.write_text("producto,precio\nYerba,3490\n", encoding="utf-8")

    result = run_command(
        [
            sys.executable,
            "scripts/03_filtrar_san_juan.py",
            "--input",
            str(bad_source),
            "--output",
            str(tmp_path / "out.csv"),
            "--errors",
            str(tmp_path / "errors.csv"),
            "--report",
            str(tmp_path / "report.json"),
        ]
    )

    assert result.returncode == 1
    assert "campos minimos" in result.stderr.lower()

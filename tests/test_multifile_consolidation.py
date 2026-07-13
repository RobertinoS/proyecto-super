import csv
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "11_consolidar_relevamientos.py"
MATCHING_PATH = ROOT / "scripts" / "04_matching_productos.py"
QUALITY_PATH = ROOT / "scripts" / "10_generar_reporte_calidad_datos.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


consolidation = load_module(SCRIPT_PATH, "multifile_consolidation")
matching = load_module(MATCHING_PATH, "matching_for_consolidation")
quality = load_module(QUALITY_PATH, "quality_for_consolidation")


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def run_sample(tmp_path: Path):
    output = tmp_path / "precios_reales_consolidados.csv"
    report = tmp_path / "reporte_consolidacion.csv"
    manifest = tmp_path / "manifiesto_consolidacion.csv"
    summary = consolidation.consolidate_relevamientos(
        ROOT / "data" / "sample" / "multifile",
        output,
        report,
        manifest,
        processed_at=datetime(2026, 7, 12, 9, 0, tzinfo=timezone.utc),
        execution_id="test_sprint_12",
    )
    return summary, output, report, manifest


def test_discovers_csv_recursively_in_stable_order():
    base = ROOT / "data" / "sample" / "multifile"
    files = consolidation.discover_csv_files(base)
    origins = [path.relative_to(base).as_posix() for path in files]

    assert len(files) == 5
    assert origins == sorted(origins, key=str.casefold)
    assert any("Santa_Lucia" in origin for origin in origins)


def test_validates_each_file_and_reports_controlled_issues(tmp_path):
    summary, _, report, _ = run_sample(tmp_path)
    rows = read_rows(report)

    assert summary["files_processed"] == 5
    assert sum(int(row["duplicados_internos"]) for row in rows) == 1
    assert sum(int(row["duplicados_entre_archivos"]) for row in rows) == 1
    assert sum(int(row["filas_invalidas"]) for row in rows) == 2
    assert sum(int(row["precios_sospechosos"]) for row in rows) == 1
    assert {row["estado_archivo"] for row in rows} == {"OK", "REVISAR"}


def test_consolidates_and_keeps_last_file_for_cross_file_duplicate(tmp_path):
    summary, output, _, _ = run_sample(tmp_path)
    rows = read_rows(output)
    corrected = next(
        row
        for row in rows
        if row["comercio"] == "Vea"
        and row["sucursal"] == "Centro"
        and row["producto"] == "Yerba Mate Playadito 1 kg"
    )

    assert summary["rows_consolidated"] == 12
    assert corrected["precio"] == "3150.00"
    assert corrected["archivo_origen"].endswith("02_correccion.csv")
    assert corrected["conflicto_detectado"] == "SI"
    assert corrected["estado_registro"] == "CONSOLIDADO_CONFLICTO"
    assert set(consolidation.CONSOLIDATED_COLUMNS).issubset(rows[0])


def test_generates_report_and_manifest(tmp_path):
    summary, output, report, manifest = run_sample(tmp_path)
    manifest_rows = read_rows(manifest)

    assert output.exists()
    assert report.exists()
    assert manifest.exists()
    assert summary["result"] == "COMPLETADO_CON_INCIDENCIAS"
    assert manifest_rows[0]["ejecucion_id"] == "test_sprint_12"
    assert manifest_rows[0]["archivos_procesados"] == "5"
    assert manifest_rows[0]["filas_consolidadas"] == "12"


def test_consolidated_output_is_compatible_with_matching(tmp_path):
    _, output, _, _ = run_sample(tmp_path)
    matched = tmp_path / "precios_reales_consolidados_matcheados.csv"
    matching_report = tmp_path / "matching.json"

    summary = matching.match_products(
        output,
        ROOT / "data" / "sample" / "product_dictionary.csv",
        matched,
        matching_report,
    )
    rows = read_rows(matched)

    assert summary["rows_written"] == 12
    assert all(row["grupo_comparacion"] for row in rows)
    assert all(row["precio_unitario_comparable"] for row in rows)


def test_consolidation_report_is_compatible_with_quality_flow(tmp_path):
    _, output, report, _ = run_sample(tmp_path)
    quality_output = tmp_path / "reporte_calidad_datos.csv"
    summary_output = tmp_path / "resumen_calidad_fuente.csv"

    result = quality.generate_quality_reports(
        output,
        report,
        quality_output,
        summary_output,
        datetime(2026, 7, 12).date(),
    )

    assert result["groups"] >= 4
    assert quality_output.exists()
    assert summary_output.exists()
    assert any(row["estado_calidad"] in {"REVISAR", "INVALIDO"} for row in read_rows(quality_output))

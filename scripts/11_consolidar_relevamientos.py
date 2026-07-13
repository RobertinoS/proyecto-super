from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


TRACE_COLUMNS = [
    "archivo_origen",
    "fecha_procesamiento",
    "estado_registro",
    "conflicto_detectado",
]

REPORT_COLUMNS = [
    "archivo_origen",
    "filas_leidas",
    "filas_validas",
    "filas_invalidas",
    "duplicados_internos",
    "duplicados_entre_archivos",
    "precios_sospechosos",
    "estado_archivo",
    "mensaje",
    "comercio",
    "sucursal",
    "localidad",
]

MANIFEST_COLUMNS = [
    "ejecucion_id",
    "fecha_hora",
    "carpeta_origen",
    "archivos_procesados",
    "filas_totales",
    "filas_consolidadas",
    "incidencias_totales",
    "resultado",
]


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_validator():
    path = Path(__file__).with_name("09_validar_precios_reales.py")
    spec = importlib.util.spec_from_file_location("real_price_validator_for_consolidation", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar el validador: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


validator = load_validator()
CONSOLIDATED_COLUMNS = validator.OUTPUT_COLUMNS + TRACE_COLUMNS


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return [dict(row) for row in csv.DictReader(file)]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def discover_csv_files(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        raise FileNotFoundError(f"No existe la carpeta de entrada: {input_dir}")
    if not input_dir.is_dir():
        raise ValueError(f"La entrada debe ser una carpeta: {input_dir}")
    files = [path for path in input_dir.rglob("*.csv") if path.is_file()]
    return sorted(files, key=lambda path: path.relative_to(input_dir).as_posix().casefold())


def duplicate_key(row: dict[str, str]) -> tuple[str, ...]:
    return (
        validator.normalize_text(row.get("comercio")),
        validator.normalize_text(row.get("sucursal")),
        validator.normalize_text(row.get("producto")),
        validator.normalize_text(row.get("marca")),
        validator.normalize_text(row.get("presentacion")),
        validator.clean_display(row.get("fecha_relevamiento")),
    )


def first_context(raw_rows: list[dict[str, str]], valid_rows: list[dict[str, str]]) -> dict[str, str]:
    source = next((row for row in valid_rows if row), None) or next((row for row in raw_rows if row), {})
    return {
        "comercio": validator.clean_display(source.get("comercio")),
        "sucursal": validator.clean_display(source.get("sucursal")),
        "localidad": validator.clean_display(source.get("localidad")),
    }


def count_invalid_rows(issues: list[dict[str, str]], rows_read: int, rows_valid: int) -> int:
    fatal_rows = {
        row.get("fila", "")
        for row in issues
        if row.get("tipo_error") in validator.FATAL_ERROR_TYPES and row.get("fila")
    }
    if fatal_rows:
        return len(fatal_rows)
    return max(rows_read - rows_valid, 0)


def build_file_message(report: dict[str, Any]) -> str:
    parts = []
    if report["filas_invalidas"]:
        parts.append(f"{report['filas_invalidas']} fila(s) invalida(s)")
    if report["duplicados_internos"]:
        parts.append(f"{report['duplicados_internos']} duplicado(s) interno(s)")
    if report["duplicados_entre_archivos"]:
        parts.append(f"{report['duplicados_entre_archivos']} duplicado(s) entre archivos")
    if report["precios_sospechosos"]:
        parts.append(f"{report['precios_sospechosos']} precio(s) sospechoso(s)")
    if report.get("error_validacion"):
        parts.append(str(report["error_validacion"]))
    return "; ".join(parts) if parts else "Archivo validado sin incidencias."


def finalize_file_report(report: dict[str, Any]) -> dict[str, str]:
    if report["filas_validas"] == 0:
        state = "INVALIDO"
    elif any(
        report[field] > 0
        for field in (
            "filas_invalidas",
            "duplicados_internos",
            "duplicados_entre_archivos",
            "precios_sospechosos",
        )
    ):
        state = "REVISAR"
    else:
        state = "OK"
    report["estado_archivo"] = state
    report["mensaje"] = build_file_message(report)
    return {column: str(report.get(column, "")) for column in REPORT_COLUMNS}


def consolidate_relevamientos(
    input_dir: Path,
    output_path: Path,
    report_path: Path,
    manifest_path: Path,
    processed_at: datetime | None = None,
    execution_id: str | None = None,
    min_suspicious_price: float = 50.0,
    max_suspicious_price: float = 500000.0,
) -> dict[str, Any]:
    input_dir = input_dir.resolve()
    files = discover_csv_files(input_dir)
    if not files:
        raise ValueError(f"No se encontraron archivos CSV en: {input_dir}")

    timestamp = processed_at or datetime.now().astimezone()
    timestamp_text = timestamp.replace(microsecond=0).isoformat()
    run_id = execution_id or f"consolidacion_{timestamp.strftime('%Y%m%d_%H%M%S')}"
    winners: dict[tuple[str, ...], dict[str, str]] = {}
    file_reports: list[dict[str, Any]] = []
    rows_total = 0

    with tempfile.TemporaryDirectory(prefix="proyecto_super_consolidacion_") as temp_dir:
        temp_root = Path(temp_dir)
        for index, source_path in enumerate(files, start=1):
            origin = source_path.relative_to(input_dir).as_posix()
            valid_path = temp_root / f"valid_{index}.csv"
            validation_path = temp_root / f"report_{index}.csv"
            raw_rows, _ = validator.read_csv(source_path)
            rows_total += len(raw_rows)
            validation_error = ""
            try:
                validator.validate_real_prices(
                    source_path,
                    valid_path,
                    validation_path,
                    min_suspicious_price=min_suspicious_price,
                    max_suspicious_price=max_suspicious_price,
                )
            except Exception as exc:
                validation_error = str(exc)

            valid_rows = read_csv(valid_path)
            issues = read_csv(validation_path)
            context = first_context(raw_rows, valid_rows)
            report: dict[str, Any] = {
                "archivo_origen": origin,
                "filas_leidas": len(raw_rows),
                "filas_validas": len(valid_rows),
                "filas_invalidas": count_invalid_rows(issues, len(raw_rows), len(valid_rows)),
                "duplicados_internos": sum(1 for row in issues if row.get("tipo_error") == "duplicado"),
                "duplicados_entre_archivos": 0,
                "precios_sospechosos": sum(1 for row in issues if row.get("tipo_error") == "precio_sospechoso"),
                "estado_archivo": "",
                "mensaje": "",
                "error_validacion": validation_error,
                **context,
            }
            file_reports.append(report)

            for valid_row in valid_rows:
                key = duplicate_key(valid_row)
                previous = winners.get(key)
                conflict = previous is not None
                if conflict:
                    report["duplicados_entre_archivos"] += 1
                enriched = dict(valid_row)
                enriched.update(
                    {
                        "archivo_origen": origin,
                        "fecha_procesamiento": timestamp_text,
                        "estado_registro": "CONSOLIDADO_CONFLICTO" if conflict else "VALIDO",
                        "conflicto_detectado": "SI" if conflict else "NO",
                    }
                )
                winners[key] = enriched

    consolidated_rows = sorted(
        winners.values(),
        key=lambda row: (
            validator.normalize_text(row.get("comercio")),
            validator.normalize_text(row.get("sucursal")),
            row.get("fecha_relevamiento", ""),
            validator.normalize_text(row.get("producto")),
        ),
    )
    finalized_reports = [finalize_file_report(report) for report in file_reports]
    incidences = sum(
        int(report[field])
        for report in file_reports
        for field in (
            "filas_invalidas",
            "duplicados_internos",
            "duplicados_entre_archivos",
            "precios_sospechosos",
        )
    )
    result = "COMPLETADO_CON_INCIDENCIAS" if incidences else "OK"
    manifest_rows = [
        {
            "ejecucion_id": run_id,
            "fecha_hora": timestamp_text,
            "carpeta_origen": str(input_dir),
            "archivos_procesados": str(len(files)),
            "filas_totales": str(rows_total),
            "filas_consolidadas": str(len(consolidated_rows)),
            "incidencias_totales": str(incidences),
            "resultado": result,
        }
    ]

    write_csv(output_path, consolidated_rows, CONSOLIDATED_COLUMNS)
    write_csv(report_path, finalized_reports, REPORT_COLUMNS)
    write_csv(manifest_path, manifest_rows, MANIFEST_COLUMNS)

    return {
        "input": str(input_dir),
        "output": str(output_path),
        "report": str(report_path),
        "manifest": str(manifest_path),
        "files_processed": len(files),
        "rows_read": rows_total,
        "rows_consolidated": len(consolidated_rows),
        "cross_file_duplicates": sum(report["duplicados_entre_archivos"] for report in file_reports),
        "incidents": incidences,
        "result": result,
    }


def main() -> int:
    root = project_root()
    parser = argparse.ArgumentParser(description="Valida y consolida relevamientos reales diarios desde multiples CSV.")
    parser.add_argument("--input", required=True, help="Carpeta con CSV; el descubrimiento es recursivo.")
    parser.add_argument("--output", default=str(root / "data" / "processed" / "precios_reales_consolidados.csv"))
    parser.add_argument("--report", default=str(root / "data" / "processed" / "reporte_consolidacion.csv"))
    parser.add_argument("--manifest", default=str(root / "data" / "processed" / "manifiesto_consolidacion.csv"))
    parser.add_argument("--min-suspicious-price", type=float, default=50.0)
    parser.add_argument("--max-suspicious-price", type=float, default=500000.0)
    args = parser.parse_args()

    try:
        report = consolidate_relevamientos(
            Path(args.input),
            Path(args.output),
            Path(args.report),
            Path(args.manifest),
            min_suspicious_price=args.min_suspicious_price,
            max_suspicious_price=args.max_suspicious_price,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"ok": True, **report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

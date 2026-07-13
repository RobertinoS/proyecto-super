from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any


QUALITY_COLUMNS = [
    "archivo_origen",
    "comercio",
    "sucursal",
    "localidad",
    "total_filas",
    "filas_validas",
    "filas_invalidas",
    "incidencias",
    "duplicados",
    "precios_sospechosos",
    "fecha_min",
    "fecha_max",
    "antiguedad_dias",
    "estado_calidad",
]

SUMMARY_COLUMNS = [
    "comercio",
    "sucursal",
    "localidad",
    "productos_validos",
    "categorias_cubiertas",
    "ultima_fecha_relevamiento",
    "antiguedad_dias",
    "score_calidad",
    "estado_operativo",
]

PRICE_REQUIRED_COLUMNS = [
    "comercio",
    "sucursal",
    "localidad",
    "producto",
    "categoria",
    "fecha_relevamiento",
]

VALIDATION_REPORT_COLUMNS = [
    "fila",
    "campo",
    "tipo_error",
    "valor_detectado",
    "sugerencia",
]

FATAL_ISSUE_TYPES = {
    "columna_faltante",
    "campo_obligatorio",
    "precio_invalido",
    "fecha_invalida",
    "localidad_fuera_alcance",
}

REVIEW_ISSUE_TYPES = {"duplicado", "precio_sospechoso"}


@dataclass
class GroupStats:
    comercio: str
    sucursal: str
    localidad: str
    valid_rows: int = 0
    products: set[str] = field(default_factory=set)
    categories: set[str] = field(default_factory=set)
    dates: list[date] = field(default_factory=list)
    issue_rows: list[dict[str, str]] = field(default_factory=list)


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return [dict(row) for row in csv.DictReader(file)]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def validate_columns(rows: list[dict[str, str]], required: list[str], name: str) -> None:
    if not rows:
        return
    columns = set(rows[0].keys())
    missing = [column for column in required if column not in columns]
    if missing:
        raise ValueError(f"Faltan columnas obligatorias en {name}: {', '.join(missing)}")


def clean(value: Any) -> str:
    return str(value or "").strip()


def parse_int(value: Any) -> int | None:
    text = clean(value)
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def parse_date(value: Any) -> date | None:
    text = clean(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y%m%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def parse_calculation_date(value: str | None) -> date:
    if not value:
        return date.today()
    parsed = parse_date(value)
    if parsed is None:
        raise ValueError("--date debe tener formato YYYY-MM-DD")
    return parsed


def group_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        clean(row.get("comercio")) or "SIN_ASIGNAR",
        clean(row.get("sucursal")) or "SIN_ASIGNAR",
        clean(row.get("localidad")) or "SIN_ASIGNAR",
    )


def row_context_from_issue(issue: dict[str, str], rows_by_line: dict[int, dict[str, str]]) -> tuple[str, str, str]:
    if clean(issue.get("comercio")) or clean(issue.get("sucursal")) or clean(issue.get("localidad")):
        return group_key(issue)
    line = parse_int(issue.get("fila"))
    if line is not None and line in rows_by_line:
        return group_key(rows_by_line[line])
    return ("SIN_ASIGNAR", "SIN_ASIGNAR", "SIN_ASIGNAR")


def issue_count(stats: GroupStats, issue_type: str) -> int:
    return sum(1 for issue in stats.issue_rows if issue.get("tipo_error") == issue_type)


def invalid_row_count(stats: GroupStats) -> int:
    rows = {
        clean(issue.get("fila"))
        for issue in stats.issue_rows
        if issue.get("tipo_error") != "precio_sospechoso" and clean(issue.get("fila"))
    }
    if rows:
        return len(rows)
    return sum(1 for issue in stats.issue_rows if issue.get("tipo_error") != "precio_sospechoso")


def fatal_issue_count(stats: GroupStats) -> int:
    return sum(1 for issue in stats.issue_rows if issue.get("tipo_error") in FATAL_ISSUE_TYPES)


def max_age_days(stats: GroupStats, calculation_date: date) -> int | None:
    if not stats.dates:
        return None
    return max((calculation_date - max(stats.dates)).days, 0)


def min_date(stats: GroupStats) -> str:
    return min(stats.dates).isoformat() if stats.dates else ""


def max_date(stats: GroupStats) -> str:
    return max(stats.dates).isoformat() if stats.dates else ""


def quality_state(stats: GroupStats, calculation_date: date, stale_days: int = 7) -> str:
    age = max_age_days(stats, calculation_date)
    if fatal_issue_count(stats) > 0:
        return "INVALIDO"
    if age is not None and age > stale_days:
        return "DESACTUALIZADO"
    if issue_count(stats, "duplicado") > 0 or issue_count(stats, "precio_sospechoso") > 0:
        return "REVISAR"
    return "OK"


def quality_score(stats: GroupStats, calculation_date: date, stale_days: int = 7) -> int:
    score = 100
    invalid_rows = invalid_row_count(stats)
    duplicates = issue_count(stats, "duplicado")
    suspicious = issue_count(stats, "precio_sospechoso")
    fatals = fatal_issue_count(stats)
    age = max_age_days(stats, calculation_date)

    score -= min(60, fatals * 30)
    score -= min(30, invalid_rows * 10)
    score -= min(25, duplicates * 15)
    score -= min(20, suspicious * 10)
    if age is None:
        score -= 20
    elif age > stale_days:
        score -= min(40, (age - stale_days) * 5)

    state = quality_state(stats, calculation_date, stale_days)
    if state == "INVALIDO":
        score = min(score, 45)
    elif state == "DESACTUALIZADO":
        score = min(score, 65)
    elif state == "REVISAR":
        score = min(score, 85)
    return max(0, min(100, int(round(score))))


def build_group_stats(valid_rows: list[dict[str, str]], validation_rows: list[dict[str, str]]) -> dict[tuple[str, str, str], GroupStats]:
    validate_columns(valid_rows, PRICE_REQUIRED_COLUMNS, "precios validados")
    if validation_rows:
        validate_columns(validation_rows, VALIDATION_REPORT_COLUMNS, "reporte de validacion")

    groups: dict[tuple[str, str, str], GroupStats] = {}
    rows_by_line: dict[int, dict[str, str]] = {}

    for row in valid_rows:
        key = group_key(row)
        stats = groups.setdefault(key, GroupStats(*key))
        stats.valid_rows += 1
        if clean(row.get("producto")):
            stats.products.add(clean(row.get("producto")))
        if clean(row.get("categoria")):
            stats.categories.add(clean(row.get("categoria")))
        parsed_date = parse_date(row.get("fecha_relevamiento"))
        if parsed_date:
            stats.dates.append(parsed_date)
        line = parse_int(row.get("fila_origen"))
        if line is not None:
            rows_by_line[line] = row

    for issue in validation_rows:
        key = row_context_from_issue(issue, rows_by_line)
        stats = groups.setdefault(key, GroupStats(*key))
        stats.issue_rows.append(issue)

    return groups


def build_quality_rows(
    groups: dict[tuple[str, str, str], GroupStats],
    archivo_origen: str,
    calculation_date: date,
    stale_days: int,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    detail_rows: list[dict[str, str]] = []
    summary_rows: list[dict[str, str]] = []

    for key in sorted(groups):
        stats = groups[key]
        invalid_rows = invalid_row_count(stats)
        age = max_age_days(stats, calculation_date)
        state = quality_state(stats, calculation_date, stale_days)
        score = quality_score(stats, calculation_date, stale_days)
        detail_rows.append(
            {
                "archivo_origen": archivo_origen,
                "comercio": stats.comercio,
                "sucursal": stats.sucursal,
                "localidad": stats.localidad,
                "total_filas": str(stats.valid_rows + invalid_rows),
                "filas_validas": str(stats.valid_rows),
                "filas_invalidas": str(invalid_rows),
                "incidencias": str(len(stats.issue_rows)),
                "duplicados": str(issue_count(stats, "duplicado")),
                "precios_sospechosos": str(issue_count(stats, "precio_sospechoso")),
                "fecha_min": min_date(stats),
                "fecha_max": max_date(stats),
                "antiguedad_dias": "" if age is None else str(age),
                "estado_calidad": state,
            }
        )
        summary_rows.append(
            {
                "comercio": stats.comercio,
                "sucursal": stats.sucursal,
                "localidad": stats.localidad,
                "productos_validos": str(len(stats.products)),
                "categorias_cubiertas": str(len(stats.categories)),
                "ultima_fecha_relevamiento": max_date(stats),
                "antiguedad_dias": "" if age is None else str(age),
                "score_calidad": str(score),
                "estado_operativo": state,
            }
        )

    order = {"INVALIDO": 0, "REVISAR": 1, "DESACTUALIZADO": 2, "OK": 3}
    detail_rows.sort(key=lambda row: (order.get(row["estado_calidad"], 9), row["comercio"], row["sucursal"]))
    summary_rows.sort(key=lambda row: (order.get(row["estado_operativo"], 9), row["comercio"], row["sucursal"]))
    return detail_rows, summary_rows


def generate_quality_reports(
    prices_path: Path,
    validation_report_path: Path,
    quality_output_path: Path,
    summary_output_path: Path,
    calculation_date: date,
    stale_days: int = 7,
    archivo_origen: str | None = None,
) -> dict[str, Any]:
    valid_rows = read_csv(prices_path)
    validation_rows = read_csv(validation_report_path)
    groups = build_group_stats(valid_rows, validation_rows)
    origin = archivo_origen or prices_path.name
    detail_rows, summary_rows = build_quality_rows(groups, origin, calculation_date, stale_days)
    write_csv(quality_output_path, detail_rows, QUALITY_COLUMNS)
    write_csv(summary_output_path, summary_rows, SUMMARY_COLUMNS)

    states = defaultdict(int)
    for row in detail_rows:
        states[row["estado_calidad"]] += 1

    return {
        "prices": str(prices_path),
        "validation_report": str(validation_report_path),
        "quality_output": str(quality_output_path),
        "summary_output": str(summary_output_path),
        "calculation_date": calculation_date.isoformat(),
        "stale_days": stale_days,
        "groups": len(detail_rows),
        "states": dict(sorted(states.items())),
    }


def main() -> int:
    root = project_root()
    parser = argparse.ArgumentParser(description="Genera reportes operativos de calidad de datos reales.")
    parser.add_argument("--prices", default=str(root / "data" / "processed" / "precios_reales_validados.csv"))
    parser.add_argument("--validation-report", default=str(root / "data" / "processed" / "reporte_validacion_precios_reales.csv"))
    parser.add_argument("--quality-output", default=str(root / "data" / "processed" / "reporte_calidad_datos.csv"))
    parser.add_argument("--summary-output", default=str(root / "data" / "processed" / "resumen_calidad_fuente.csv"))
    parser.add_argument("--date", default="", help="Fecha de calculo YYYY-MM-DD. Si se omite, usa la fecha actual.")
    parser.add_argument("--stale-days", type=int, default=7)
    parser.add_argument("--archivo-origen", default="")
    args = parser.parse_args()

    try:
        report = generate_quality_reports(
            Path(args.prices),
            Path(args.validation_report),
            Path(args.quality_output),
            Path(args.summary_output),
            parse_calculation_date(args.date),
            args.stale_days,
            args.archivo_origen or None,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"ok": True, **report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

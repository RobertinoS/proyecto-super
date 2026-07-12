from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any


REQUIRED_COLUMNS = [
    "comercio",
    "sucursal",
    "localidad",
    "direccion",
    "producto",
    "marca",
    "categoria",
    "presentacion",
    "precio",
    "fecha_relevamiento",
    "fuente",
    "observacion",
]

OUTPUT_COLUMNS = [
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
]

REPORT_COLUMNS = [
    "fila",
    "campo",
    "tipo_error",
    "valor_detectado",
    "sugerencia",
]

FATAL_ERROR_TYPES = {
    "campo_obligatorio",
    "precio_invalido",
    "fecha_invalida",
    "localidad_fuera_alcance",
    "duplicado",
}

DEFAULT_LOCALITIES = {
    "capital": "Capital",
    "san juan": "Capital",
    "rawson": "Rawson",
    "santa lucia": "Santa Lucia",
    "rivadavia": "Rivadavia",
}

REQUIRED_NON_EMPTY_FIELDS = [
    "comercio",
    "sucursal",
    "localidad",
    "producto",
    "categoria",
    "presentacion",
    "precio",
    "fecha_relevamiento",
    "fuente",
]


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = strip_accents(str(value)).lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def clean_display(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def parse_price(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("$", "").replace("ARS", "").replace("ars", "")
    text = text.replace("\u00a0", "").replace(" ", "")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", "")
    try:
        price = float(text)
    except ValueError:
        return None
    if price <= 0:
        return None
    return price


def parse_date(value: Any) -> str | None:
    text = clean_display(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y%m%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def build_allowed_localities(raw_value: str | None = None) -> dict[str, str]:
    if not raw_value:
        return DEFAULT_LOCALITIES.copy()
    allowed: dict[str, str] = {}
    for item in raw_value.split(","):
        display = clean_display(item)
        if display:
            allowed[normalize_text(display)] = strip_accents(display).title()
    return allowed or DEFAULT_LOCALITIES.copy()


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = [dict(row) for row in reader]
        return rows, list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def add_issue(
    issues: list[dict[str, str]],
    row_number: int,
    field: str,
    issue_type: str,
    value: Any,
    suggestion: str,
) -> None:
    issues.append(
        {
            "fila": str(row_number),
            "campo": field,
            "tipo_error": issue_type,
            "valor_detectado": clean_display(value),
            "sugerencia": suggestion,
        }
    )


def validate_columns(fieldnames: list[str], report_path: Path) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
    if not missing:
        return
    issues: list[dict[str, str]] = []
    for column in missing:
        add_issue(
            issues,
            1,
            column,
            "columna_faltante",
            "",
            "Agregar la columna obligatoria respetando el nombre de la plantilla.",
        )
    write_csv(report_path, issues, REPORT_COLUMNS)
    raise ValueError(f"Faltan columnas obligatorias: {', '.join(missing)}")


def duplicate_key(row: dict[str, str], canonical_locality: str, iso_date: str) -> tuple[str, ...]:
    return (
        normalize_text(row.get("comercio")),
        normalize_text(row.get("sucursal")),
        normalize_text(canonical_locality),
        normalize_text(row.get("producto")),
        normalize_text(row.get("marca")),
        normalize_text(row.get("presentacion")),
        iso_date,
    )


def validate_real_prices(
    input_path: Path,
    output_path: Path,
    report_path: Path,
    allowed_localities: dict[str, str] | None = None,
    min_suspicious_price: float = 50.0,
    max_suspicious_price: float = 500000.0,
) -> dict[str, Any]:
    rows, fieldnames = read_csv(input_path)
    validate_columns(fieldnames, report_path)
    localities = allowed_localities or DEFAULT_LOCALITIES.copy()

    valid_rows: list[dict[str, str]] = []
    issues: list[dict[str, str]] = []
    seen_keys: set[tuple[str, ...]] = set()
    fatal_rows = 0
    warning_count = 0
    duplicate_count = 0

    for index, row in enumerate(rows, start=2):
        row_has_fatal_error = False
        for field in REQUIRED_NON_EMPTY_FIELDS:
            if not clean_display(row.get(field)):
                add_issue(
                    issues,
                    index,
                    field,
                    "campo_obligatorio",
                    row.get(field, ""),
                    "Completar el campo antes de validar la carga real.",
                )
                row_has_fatal_error = True

        locality_key = normalize_text(row.get("localidad"))
        canonical_locality = localities.get(locality_key)
        if clean_display(row.get("localidad")) and canonical_locality is None:
            add_issue(
                issues,
                index,
                "localidad",
                "localidad_fuera_alcance",
                row.get("localidad", ""),
                "Usar una localidad de San Juan habilitada: Capital, Rawson, Santa Lucia o Rivadavia.",
            )
            row_has_fatal_error = True

        price = parse_price(row.get("precio"))
        if clean_display(row.get("precio")) and price is None:
            add_issue(
                issues,
                index,
                "precio",
                "precio_invalido",
                row.get("precio", ""),
                "Ingresar un numero mayor a cero. Se aceptan coma o punto decimal.",
            )
            row_has_fatal_error = True

        iso_date = parse_date(row.get("fecha_relevamiento"))
        if clean_display(row.get("fecha_relevamiento")) and iso_date is None:
            add_issue(
                issues,
                index,
                "fecha_relevamiento",
                "fecha_invalida",
                row.get("fecha_relevamiento", ""),
                "Usar formato YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY o YYYYMMDD.",
            )
            row_has_fatal_error = True

        if price is not None and (price < min_suspicious_price or price > max_suspicious_price):
            add_issue(
                issues,
                index,
                "precio",
                "precio_sospechoso",
                row.get("precio", ""),
                f"Revisar contra ticket/gondola. Rango esperado: {min_suspicious_price:g} a {max_suspicious_price:g}.",
            )
            warning_count += 1

        if not row_has_fatal_error and price is not None and iso_date is not None and canonical_locality is not None:
            key = duplicate_key(row, canonical_locality, iso_date)
            if key in seen_keys:
                add_issue(
                    issues,
                    index,
                    "producto",
                    "duplicado",
                    row.get("producto", ""),
                    "Existe otra fila con el mismo comercio, sucursal, localidad, producto, marca, presentacion y fecha.",
                )
                row_has_fatal_error = True
                duplicate_count += 1
            else:
                seen_keys.add(key)

        if row_has_fatal_error:
            fatal_rows += 1
            continue

        if price is None or iso_date is None or canonical_locality is None:
            fatal_rows += 1
            continue

        valid_rows.append(
            {
                "comercio": clean_display(row.get("comercio")),
                "sucursal": clean_display(row.get("sucursal")),
                "localidad": canonical_locality,
                "producto": clean_display(row.get("producto")),
                "marca": clean_display(row.get("marca")),
                "categoria": clean_display(row.get("categoria")),
                "presentacion": clean_display(row.get("presentacion")),
                "precio": f"{price:.2f}",
                "fecha_relevamiento": iso_date,
                "fuente": clean_display(row.get("fuente")),
                "direccion": clean_display(row.get("direccion")),
                "observacion": clean_display(row.get("observacion")),
            }
        )

    write_csv(output_path, valid_rows, OUTPUT_COLUMNS)
    write_csv(report_path, issues, REPORT_COLUMNS)

    if not valid_rows:
        raise ValueError("No se generaron filas validas. Revisar el reporte de validacion.")

    return {
        "input": str(input_path),
        "output": str(output_path),
        "report": str(report_path),
        "rows_read": len(rows),
        "rows_valid": len(valid_rows),
        "rows_invalid": fatal_rows,
        "issues": len(issues),
        "warnings": warning_count,
        "duplicates": duplicate_count,
    }


def main() -> int:
    root = project_root()
    parser = argparse.ArgumentParser(description="Valida cargas manuales de precios reales para Proyecto Super.")
    parser.add_argument("--input", default=str(root / "data" / "sample" / "precios_reales_demo.csv"))
    parser.add_argument("--output", default=str(root / "data" / "processed" / "precios_reales_validados.csv"))
    parser.add_argument("--report", default=str(root / "data" / "processed" / "reporte_validacion_precios_reales.csv"))
    parser.add_argument("--allowed-localities", default="")
    parser.add_argument("--min-suspicious-price", type=float, default=50.0)
    parser.add_argument("--max-suspicious-price", type=float, default=500000.0)
    args = parser.parse_args()

    try:
        report = validate_real_prices(
            Path(args.input),
            Path(args.output),
            Path(args.report),
            build_allowed_localities(args.allowed_localities),
            args.min_suspicious_price,
            args.max_suspicious_price,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"ok": True, **report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

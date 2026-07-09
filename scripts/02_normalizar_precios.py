from __future__ import annotations

import argparse
import csv
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
    "producto",
    "marca",
    "categoria",
    "presentacion",
    "precio",
    "fecha_relevamiento",
    "fuente",
]


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def clean_text(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-z0-9%.,/\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def title_text(value: Any) -> str:
    cleaned = clean_text(value)
    return " ".join(part.capitalize() for part in cleaned.split())


def parse_price(value: Any) -> float | None:
    text = str(value or "").strip().replace("$", "").replace(" ", "")
    if not text:
        return None
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        price = float(text)
    except ValueError:
        return None
    if price <= 0:
        return None
    return round(price, 2)


def parse_date(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def validate_columns(fieldnames: list[str] | None) -> None:
    present = set(fieldnames or [])
    missing = [column for column in REQUIRED_COLUMNS if column not in present]
    if missing:
        raise ValueError(f"Faltan columnas obligatorias: {', '.join(missing)}")


def normalize_row(row: dict[str, str], row_number: int) -> tuple[dict[str, Any] | None, str | None]:
    required_text = ["comercio", "sucursal", "localidad", "producto", "categoria", "presentacion", "fuente"]
    empty = [column for column in required_text if not str(row.get(column, "")).strip()]
    if empty:
        return None, f"Fila {row_number}: campos vacios: {', '.join(empty)}"

    price = parse_price(row.get("precio"))
    if price is None:
        return None, f"Fila {row_number}: precio invalido: {row.get('precio')!r}"

    date = parse_date(row.get("fecha_relevamiento"))
    if date is None:
        return None, f"Fila {row_number}: fecha invalida: {row.get('fecha_relevamiento')!r}"

    product_clean = clean_text(row.get("producto"))
    if len(product_clean) < 3:
        return None, f"Fila {row_number}: producto demasiado corto"

    return (
        {
            "comercio": title_text(row.get("comercio")),
            "comercio_limpio": clean_text(row.get("comercio")),
            "sucursal": title_text(row.get("sucursal")),
            "sucursal_limpia": clean_text(row.get("sucursal")),
            "localidad": title_text(row.get("localidad")),
            "producto": str(row.get("producto", "")).strip(),
            "producto_limpio": product_clean,
            "marca": title_text(row.get("marca")),
            "marca_limpia": clean_text(row.get("marca")),
            "categoria": title_text(row.get("categoria")),
            "categoria_limpia": clean_text(row.get("categoria")),
            "presentacion": str(row.get("presentacion", "")).strip().lower(),
            "precio": f"{price:.2f}",
            "fecha_relevamiento": date,
            "fuente": clean_text(row.get("fuente")),
        },
        None,
    )


def normalize_csv(input_path: Path, output_path: Path, errors_path: Path) -> tuple[int, int]:
    if not input_path.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    errors_path.parent.mkdir(parents=True, exist_ok=True)

    valid_rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        validate_columns(reader.fieldnames)
        for index, row in enumerate(reader, start=2):
            normalized, error = normalize_row(row, index)
            if error:
                errors.append({"fila": str(index), "error": error})
                continue
            assert normalized is not None
            valid_rows.append(normalized)

    if not valid_rows:
        raise ValueError("No se genero ningun registro valido. Revisar errores de entrada.")

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(valid_rows[0].keys()))
        writer.writeheader()
        writer.writerows(valid_rows)

    if errors:
        with errors_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["fila", "error"])
            writer.writeheader()
            writer.writerows(errors)
    elif errors_path.exists():
        errors_path.unlink()

    return len(valid_rows), len(errors)


def main() -> int:
    root = project_root()
    parser = argparse.ArgumentParser(description="Normaliza precios CSV demo para Proyecto Super San Juan.")
    parser.add_argument("--input", default=str(root / "data" / "sample" / "precios_demo.csv"))
    parser.add_argument("--output", default=str(root / "data" / "processed" / "precios_normalizados.csv"))
    parser.add_argument("--errors", default=str(root / "data" / "processed" / "precios_normalizados_errores.csv"))
    args = parser.parse_args()

    try:
        valid_count, error_count = normalize_csv(Path(args.input), Path(args.output), Path(args.errors))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"OK: registros_validos={valid_count} errores={error_count} salida={args.output}")
    if error_count:
        print(f"Advertencia: ver errores en {args.errors}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

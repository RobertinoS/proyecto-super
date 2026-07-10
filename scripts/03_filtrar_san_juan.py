from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
import zipfile
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any


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
]

PRIORITY_LOCALITIES = ["capital", "rawson", "santa lucia", "rivadavia"]
MINIMUM_FIELDS = ["producto", "precio", "comercio", "sucursal", "localidad"]
DISPLAY_OVERRIDES = {
    "vea": "Vea",
    "carrefour": "Carrefour",
    "changomas": "ChangoMas",
    "atomo conviene": "Atomo Conviene",
}

ALIASES = {
    "provincia": ["sucursales_provincia", "provincia", "provincia_nombre", "nombre_provincia", "id_provincia", "provincia_id", "cod_provincia"],
    "localidad": ["sucursales_localidad", "localidad", "ciudad", "municipio", "departamento", "localidad_nombre"],
    "comercio": ["comercio_bandera_nombre", "bandera_descripcion", "comercio", "cadena", "nombre_comercio", "comercio_razon_social", "razon_social", "empresa"],
    "sucursal": ["sucursales_nombre", "sucursal_nombre", "sucursal", "branch_name", "nombre_sucursal", "direccion", "domicilio", "id_sucursal"],
    "producto": ["productos_descripcion", "producto", "producto_nombre", "nombre_producto", "producto_descripcion", "descripcion", "nombre"],
    "marca": ["productos_marca", "marca", "marca_nombre"],
    "categoria": ["categoria", "rubro", "familia", "clase"],
    "presentacion": ["presentacion", "presentacion_producto", "productos_presentacion"],
    "precio": ["productos_precio_lista", "precio", "precio_lista", "precio_venta", "precio_unitario"],
    "fecha_relevamiento": ["fecha_relevamiento", "fecha", "fecha_precio", "fecha_vigencia", "capture_date"],
    "fuente": ["fuente", "source", "origen"],
}


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
    if cleaned in DISPLAY_OVERRIDES:
        return DISPLAY_OVERRIDES[cleaned]
    return " ".join(part.capitalize() for part in cleaned.split())


def canonical_header(value: str) -> str:
    return clean_text(value).replace(" ", "_")


def sniff_delimiter(path: Path) -> str:
    sample = path.read_text(encoding="utf-8-sig", errors="replace")[:4096]
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;|\t").delimiter
    except csv.Error:
        return ","


def read_csv(path: Path) -> list[dict[str, str]]:
    delimiter = sniff_delimiter(path)
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        rows = []
        for row in reader:
            rows.append({canonical_header(k or ""): str(v or "").strip() for k, v in row.items()})
        return rows


def collect_csv_paths(input_path: Path, extract_dir: Path | None = None) -> list[Path]:
    if input_path.is_dir():
        return sorted([path for path in input_path.rglob("*") if path.suffix.lower() in {".csv", ".txt"}])
    if zipfile.is_zipfile(input_path):
        if extract_dir is None:
            raise ValueError("El procesamiento de ZIP requiere un directorio temporal de extraccion.")
        with zipfile.ZipFile(input_path) as archive:
            archive.extractall(extract_dir)
        return sorted([path for path in extract_dir.rglob("*") if path.suffix.lower() in {".csv", ".txt"}])
    return [input_path]


def get_value(row: dict[str, str], field: str) -> str:
    for alias in ALIASES[field]:
        key = canonical_header(alias)
        if row.get(key):
            return row[key]
    return ""


def get_first(row: dict[str, str], aliases: list[str]) -> str:
    for alias in aliases:
        value = row.get(canonical_header(alias), "")
        if value:
            return value
    return ""


def key_tuple(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        row.get("id_comercio", ""),
        row.get("id_bandera", ""),
        row.get("id_sucursal", ""),
    )


def commerce_key(row: dict[str, str]) -> tuple[str, str]:
    return (
        row.get("id_comercio", ""),
        row.get("id_bandera", ""),
    )


def merge_official_like_files(csv_paths: list[Path]) -> list[dict[str, str]]:
    loaded = [(path, read_csv(path)) for path in csv_paths]
    all_rows = [row for _, rows in loaded for row in rows]

    commerce_rows = [
        row for row in all_rows
        if (row.get("id_comercio") or row.get("id_bandera")) and get_value(row, "comercio")
    ]
    store_rows = [
        row for row in all_rows
        if key_tuple(row) != ("", "", "") and (get_value(row, "localidad") or get_value(row, "provincia") or get_value(row, "sucursal"))
    ]
    price_rows = [row for row in all_rows if row.get("id_producto") and get_value(row, "precio")]

    if price_rows:
        commerces = {commerce_key(row): row for row in commerce_rows}
        stores = {key_tuple(row): row for row in store_rows}
        merged = []
        for row in price_rows:
            merged_row = {}
            merged_row.update(commerces.get(commerce_key(row), {}))
            merged_row.update(stores.get(key_tuple(row), {}))
            merged_row.update(row)
            merged.append(merged_row)
        return merged

    return all_rows


def validate_minimum_fields(rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("No se encontraron filas en el archivo fuente.")
    missing = [field for field in MINIMUM_FIELDS if not any(get_value(row, field) for row in rows)]
    if missing:
        raise ValueError(f"No se detectaron campos minimos compatibles: {', '.join(missing)}")


def is_san_juan(row: dict[str, str]) -> bool:
    provincia = clean_text(get_value(row, "provincia"))
    localidad = clean_text(get_value(row, "localidad"))
    return provincia in {"ar-j", "san juan", "j", "70"} or "san juan" in provincia or localidad in PRIORITY_LOCALITIES


def parse_price(value: Any) -> float | None:
    text = str(value or "").replace("$", "").replace(" ", "").strip()
    if not text:
        return None
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        price = float(text)
    except ValueError:
        return None
    return round(price, 2) if price > 0 else None


def parse_date(value: Any, fallback: str) -> str | None:
    text = str(value or "").strip() or fallback
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y%m%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def infer_presentation(product: str) -> str:
    match = re.search(r"(\d+(?:[,.]\d+)?)\s*(kg|g|gr|grs|l|lt|lts|ml|cc|un|unidad|unidades)\b", clean_text(product))
    return match.group(0) if match else ""


def get_presentation(row: dict[str, str], product: str) -> str:
    quantity = get_first(row, ["productos_cantidad_presentacion", "cantidad_presentacion"])
    unit = get_first(row, ["productos_unidad_medida_presentacion", "productos_unidad_medida", "unidad_presentacion"])
    if quantity and unit:
        return f"{quantity} {unit}".strip()
    return get_value(row, "presentacion") or infer_presentation(product)


def normalize_row(row: dict[str, str], row_number: int, fallback_date: str) -> tuple[dict[str, str] | None, str | None]:
    if not is_san_juan(row):
        return None, "fuera_de_san_juan"

    price = parse_price(get_value(row, "precio"))
    if price is None:
        return None, f"Fila {row_number}: precio invalido"

    date = parse_date(get_value(row, "fecha_relevamiento"), fallback_date)
    if date is None:
        return None, f"Fila {row_number}: fecha invalida"

    product = get_value(row, "producto")
    commerce = get_value(row, "comercio")
    locality = get_value(row, "localidad")
    required = {
        "comercio": commerce,
        "sucursal": get_value(row, "sucursal"),
        "localidad": locality,
        "producto": product,
        "categoria": get_value(row, "categoria") or "Sin categoria",
        "presentacion": get_presentation(row, product),
    }
    empty = [name for name, value in required.items() if not str(value).strip()]
    if empty:
        return None, f"Fila {row_number}: campos vacios: {', '.join(empty)}"

    out = {
        "comercio": title_text(required["comercio"]),
        "sucursal": title_text(required["sucursal"]),
        "localidad": title_text(required["localidad"]),
        "producto": str(product).strip(),
        "marca": title_text(get_value(row, "marca")),
        "categoria": title_text(required["categoria"]),
        "presentacion": str(required["presentacion"]).strip().lower(),
        "precio": f"{price:.2f}",
        "fecha_relevamiento": date,
        "fuente": clean_text(get_value(row, "fuente") or "sepa_manual"),
    }
    return out, None


def priority_key(row: dict[str, str]) -> tuple[int, str, float]:
    locality = clean_text(row.get("localidad"))
    priority = PRIORITY_LOCALITIES.index(locality) if locality in PRIORITY_LOCALITIES else 99
    return priority, clean_text(row.get("producto")), float(row.get("precio") or 0)


def filter_san_juan(
    input_path: Path,
    output_path: Path,
    errors_path: Path,
    report_path: Path,
    fallback_date: str,
    only_priority: bool = False,
) -> dict:
    with TemporaryDirectory() as temp_dir:
        csv_paths = collect_csv_paths(input_path, Path(temp_dir))
        rows = merge_official_like_files(csv_paths)
    validate_minimum_fields(rows)

    valid: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    skipped_outside = 0

    for index, row in enumerate(rows, start=2):
        normalized, error = normalize_row(row, index, fallback_date)
        if error == "fuera_de_san_juan":
            skipped_outside += 1
            continue
        if error:
            errors.append({"fila": str(index), "error": error})
            continue
        assert normalized is not None
        if only_priority and clean_text(normalized["localidad"]) not in PRIORITY_LOCALITIES:
            continue
        valid.append(normalized)

    valid.sort(key=priority_key)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    errors_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(valid)

    if errors:
        with errors_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["fila", "error"])
            writer.writeheader()
            writer.writerows(errors)
    elif errors_path.exists():
        errors_path.unlink()

    report = {
        "input": str(input_path),
        "output": str(output_path),
        "csv_files_read": [str(path) for path in csv_paths],
        "rows_read": len(rows),
        "rows_san_juan": len(valid),
        "rows_skipped_outside_san_juan": skipped_outside,
        "errors": len(errors),
        "priority_localities": PRIORITY_LOCALITIES,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    root = project_root()
    parser = argparse.ArgumentParser(description="Filtra archivo tipo SEPA a San Juan y genera CSV compatible con dashboard.")
    parser.add_argument("--input", default=str(root / "data" / "sample" / "sepa" / "sepa_precios_simulado.csv"))
    parser.add_argument("--output", default=str(root / "data" / "processed" / "precios_san_juan_sepa.csv"))
    parser.add_argument("--errors", default=str(root / "data" / "processed" / "precios_san_juan_sepa_errores.csv"))
    parser.add_argument("--report", default=str(root / "data" / "processed" / "precios_san_juan_sepa_reporte.json"))
    parser.add_argument("--fallback-date", default=datetime.now().date().isoformat())
    parser.add_argument("--only-priority", action="store_true")
    args = parser.parse_args()

    try:
        report = filter_san_juan(
            Path(args.input),
            Path(args.output),
            Path(args.errors),
            Path(args.report),
            args.fallback_date,
            args.only_priority,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"ok": True, **report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

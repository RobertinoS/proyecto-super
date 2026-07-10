from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any


BASE_COLUMNS = [
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
    "producto_normalizado",
    "marca_normalizada",
    "categoria_normalizada",
    "presentacion_normalizada",
    "cantidad_base",
    "unidad_base",
    "precio_unitario_comparable",
    "grupo_comparacion",
    "confianza_matching",
]

OUTPUT_COLUMNS = BASE_COLUMNS + MATCH_COLUMNS

STOPWORDS = {
    "x",
    "por",
    "pack",
    "paq",
    "unidad",
    "unidades",
    "un",
    "kg",
    "kilo",
    "kilos",
    "kilogramo",
    "kilogramos",
    "g",
    "gr",
    "grs",
    "gramo",
    "gramos",
    "l",
    "lt",
    "lts",
    "litro",
    "litros",
    "ml",
    "cc",
}

UNIT_ALIASES = {
    "kg": "kg",
    "kilo": "kg",
    "kilos": "kg",
    "kilogramo": "kg",
    "kilogramos": "kg",
    "g": "g",
    "gr": "g",
    "grs": "g",
    "gramo": "g",
    "gramos": "g",
    "l": "l",
    "lt": "l",
    "lts": "l",
    "litro": "l",
    "litros": "l",
    "ml": "ml",
    "cc": "ml",
    "un": "un",
    "unidad": "un",
    "unidades": "un",
}


@dataclass(frozen=True)
class Presentation:
    quantity: float
    unit: str
    source: str


@dataclass(frozen=True)
class DictionaryEntry:
    original_norm: str
    product_norm: str
    category_norm: str
    brand_norm: str
    unit: str
    quantity: float
    group: str


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def normalize_text(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.replace("×", " x ")
    text = re.sub(r"[^a-z0-9,./\s-]", " ", text)
    text = re.sub(r"(?<=\d),(?=\d)", ".", text)
    text = re.sub(r"(?<=\d)\s*(kg|kilos?|kilogramos?)\b", " kg", text)
    text = re.sub(r"(?<=\d)\s*(grs?|gramos?)\b", " g", text)
    text = re.sub(r"(?<=\d)\s*(lts?|litros?)\b", " l", text)
    text = re.sub(r"\b(cc)\b", " ml", text)
    text = re.sub(r"\bpor\b", " x ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def slug(value: str) -> str:
    cleaned = normalize_text(value)
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned).strip("_")
    return cleaned or "sin_grupo"


def dictionary_group(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-z0-9_-]+", "_", text).strip("_")
    return text or "sin_grupo"


def parse_number(value: Any) -> float | None:
    text = str(value or "").strip().replace("$", "").replace(" ", "")
    if not text:
        return None
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        number = float(text)
    except ValueError:
        return None
    return number if number > 0 else None


def parse_quantity(value: str) -> float:
    return float(value.replace(",", "."))


def to_base_unit(quantity: float, unit_alias: str) -> tuple[float, str] | None:
    unit = UNIT_ALIASES.get(unit_alias, unit_alias)
    if unit == "kg":
        return quantity, "kg"
    if unit == "g":
        return quantity / 1000, "kg"
    if unit == "l":
        return quantity, "l"
    if unit == "ml":
        return quantity / 1000, "l"
    if unit == "un":
        return quantity, "un"
    return None


def extract_presentation(product: str, presentation: str = "") -> Presentation | None:
    candidates = [presentation, product, f"{product} {presentation}"]
    unit_pattern = r"(kg|kilo|kilos|kilogramo|kilogramos|g|gr|grs|gramo|gramos|l|lt|lts|litro|litros|ml|cc|un|unidad|unidades)"
    for source in candidates:
        text = normalize_text(source)
        match = re.search(rf"\b(\d+(?:[.,]\d+)?)\s*{unit_pattern}\b", text)
        if match:
            converted = to_base_unit(parse_quantity(match.group(1)), match.group(2))
            if converted:
                quantity, unit = converted
                return Presentation(round(quantity, 6), unit, "texto")

        pack_match = re.search(r"\b(?:pack\s*)?x\s*(\d+(?:[.,]\d+)?)\b", text)
        if pack_match:
            return Presentation(parse_quantity(pack_match.group(1)), "un", "pack")

    return None


def remove_quantity_terms(value: str) -> str:
    text = normalize_text(value)
    text = re.sub(r"\b\d+(?:[.,]\d+)?\s*(kg|kilo|kilos|kilogramo|kilogramos|g|gr|grs|gramo|gramos|l|lt|lts|litro|litros|ml|cc|un|unidad|unidades)\b", " ", text)
    text = re.sub(r"\b(?:pack\s*)?x\s*\d+(?:[.,]\d+)?\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_product_name(product: str, brand: str = "") -> str:
    text = remove_quantity_terms(product)
    brand_tokens = set(normalize_text(brand).split())
    tokens = []
    for token in text.split():
        if token in brand_tokens or token in STOPWORDS or token.replace(".", "").isdigit():
            continue
        tokens.append(token)
    normalized = " ".join(tokens)
    normalized = re.sub(r"\byerba\b(?! mate)", "yerba mate", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized or normalize_text(product)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [{key: str(value or "").strip() for key, value in row.items()} for row in reader]


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def validate_columns(rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("El archivo de precios esta vacio.")
    columns = set(rows[0].keys())
    missing = [column for column in BASE_COLUMNS if column not in columns]
    if missing:
        raise ValueError(f"Faltan columnas obligatorias: {', '.join(missing)}")


def load_dictionary(path: Path) -> list[DictionaryEntry]:
    if not path.exists():
        return []
    entries = []
    for row in read_csv(path):
        quantity = parse_number(row.get("cantidad_base"))
        if quantity is None:
            continue
        entries.append(
            DictionaryEntry(
                original_norm=normalize_text(row.get("producto_original")),
                product_norm=normalize_text(row.get("producto_normalizado")),
                category_norm=normalize_text(row.get("categoria_normalizada")),
                brand_norm=normalize_text(row.get("marca_normalizada")),
                unit=normalize_text(row.get("unidad_base")),
                quantity=quantity,
                group=dictionary_group(row.get("grupo_comparacion")),
            )
        )
    return entries


def match_dictionary(product_norm: str, brand_norm: str, category_norm: str, entries: list[DictionaryEntry]) -> DictionaryEntry | None:
    for entry in entries:
        brand_ok = not entry.brand_norm or not brand_norm or entry.brand_norm == brand_norm
        category_ok = not entry.category_norm or not category_norm or entry.category_norm == category_norm
        if brand_ok and category_ok and (entry.original_norm == product_norm or entry.original_norm in product_norm or product_norm in entry.original_norm):
            return entry
    return None


def build_group(product_norm: str, brand_norm: str, category_norm: str, presentation: Presentation | None) -> str:
    unit = presentation.unit if presentation else "sin_unidad"
    quantity = format_quantity(presentation.quantity) if presentation else "sin_cantidad"
    return slug(f"{category_norm}_{brand_norm}_{product_norm}_{quantity}_{unit}")


def format_quantity(value: float | None) -> str:
    if value is None:
        return ""
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return text or "0"


def normalize_row(row: dict[str, str], dictionary: list[DictionaryEntry]) -> dict[str, str]:
    price = parse_number(row.get("precio"))
    if price is None:
        raise ValueError(f"Precio invalido para producto {row.get('producto', '')!r}")

    product_norm = normalize_product_name(row.get("producto", ""), row.get("marca", ""))
    brand_norm = normalize_text(row.get("marca"))
    category_norm = normalize_text(row.get("categoria"))
    presentation = extract_presentation(row.get("producto", ""), row.get("presentacion", ""))
    dictionary_entry = match_dictionary(product_norm, brand_norm, category_norm, dictionary)

    confidence = 0.55
    source_product = product_norm
    source_brand = brand_norm
    source_category = category_norm
    group = build_group(product_norm, brand_norm, category_norm, presentation)

    if dictionary_entry:
        source_product = dictionary_entry.product_norm
        source_brand = dictionary_entry.brand_norm or brand_norm
        source_category = dictionary_entry.category_norm or category_norm
        presentation = Presentation(dictionary_entry.quantity, dictionary_entry.unit, "diccionario")
        group = dictionary_entry.group
        confidence = 0.95
    elif presentation and brand_norm:
        confidence = 0.78
    elif presentation:
        confidence = 0.68

    quantity_base = presentation.quantity if presentation else None
    unit_base = presentation.unit if presentation else ""
    unit_price = price / quantity_base if quantity_base and quantity_base > 0 else price

    out = dict(row)
    out.update(
        {
            "producto_normalizado": source_product,
            "marca_normalizada": source_brand,
            "categoria_normalizada": source_category,
            "presentacion_normalizada": f"{format_quantity(quantity_base)} {unit_base}".strip(),
            "cantidad_base": format_quantity(quantity_base),
            "unidad_base": unit_base,
            "precio_unitario_comparable": f"{unit_price:.2f}",
            "grupo_comparacion": group,
            "confianza_matching": f"{confidence:.2f}",
        }
    )
    return out


def match_products(input_path: Path, dictionary_path: Path, output_path: Path, report_path: Path | None = None) -> dict[str, Any]:
    rows = read_csv(input_path)
    validate_columns(rows)
    dictionary = load_dictionary(dictionary_path)
    matched = [normalize_row(row, dictionary) for row in rows]
    matched.sort(key=lambda row: (row["grupo_comparacion"], parse_number(row["precio_unitario_comparable"]) or 0, row["comercio"]))
    write_csv(output_path, matched, OUTPUT_COLUMNS)

    groups = {row["grupo_comparacion"] for row in matched}
    report = {
        "input": str(input_path),
        "dictionary": str(dictionary_path),
        "output": str(output_path),
        "rows_read": len(rows),
        "rows_written": len(matched),
        "groups": len(groups),
        "dictionary_entries": len(dictionary),
        "average_confidence": round(sum(float(row["confianza_matching"]) for row in matched) / len(matched), 4) if matched else 0,
    }
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    root = project_root()
    parser = argparse.ArgumentParser(description="Genera matching de productos y precio unitario comparable.")
    parser.add_argument("--input", default=str(root / "data" / "processed" / "precios_san_juan_sepa.csv"))
    parser.add_argument("--dictionary", default=str(root / "data" / "sample" / "product_dictionary.csv"))
    parser.add_argument("--output", default=str(root / "data" / "processed" / "precios_matcheados.csv"))
    parser.add_argument("--report", default=str(root / "data" / "processed" / "precios_matcheados_reporte.json"))
    args = parser.parse_args()

    try:
        report = match_products(Path(args.input), Path(args.dictionary), Path(args.output), Path(args.report))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"ok": True, **report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

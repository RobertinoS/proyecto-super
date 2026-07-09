from __future__ import annotations

import math
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Any

try:
    from unidecode import unidecode
except Exception:  # pragma: no cover - fallback for fresh environments
    def unidecode(value: str) -> str:
        return "".join(
            char
            for char in unicodedata.normalize("NFKD", value)
            if not unicodedata.combining(char)
        )


PRICE_RE = re.compile(r"[-+]?\$?\s*([0-9]{1,3}(?:[.\s][0-9]{3})*|[0-9]+)(?:,([0-9]{1,2}))?")
PRESENTATION_RE = re.compile(
    r"(?P<qty>\d+(?:[.,]\d+)?)\s*(?P<unit>kg|kgs|kilo|kilos|g|gr|grs|gramos|l|lt|lts|litro|litros|ml|cc|un|uni|unidad|unidades)\b",
    re.IGNORECASE,
)
PACK_RE = re.compile(r"\bx\s*(?P<qty>\d{1,3})\b", re.IGNORECASE)


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value):
            return None
        return value
    if isinstance(value, int):
        return float(value)
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "no disponible", "precio no disponible"}:
        return None
    parsed = parse_argentine_price(text)
    return parsed


def parse_argentine_price(value: Any) -> float | None:
    """Parse values like "$ 1.234,50", "1234.5" or "4.899" into float."""
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("\xa0", " ").replace("$", "").strip()
    match = PRICE_RE.search(text)
    if not match:
        cleaned = re.sub(r"[^0-9,.-]", "", text)
    else:
        cleaned = match.group(0).replace("$", "").strip()
    if not cleaned:
        return None
    cleaned = cleaned.replace(" ", "")
    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    else:
        parts = cleaned.split(".")
        if len(parts) > 1 and len(parts[-1]) == 3:
            cleaned = "".join(parts)
    try:
        return float(Decimal(cleaned))
    except (InvalidOperation, ValueError):
        return None


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = unidecode(str(value).lower())
    text = re.sub(r"[^a-z0-9%.,/\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_unit(unit: str | None) -> str | None:
    if not unit:
        return None
    unit_clean = clean_text(unit)
    if unit_clean in {"kg", "kgs", "kilo", "kilos"}:
        return "kg"
    if unit_clean in {"g", "gr", "grs", "gramos"}:
        return "g"
    if unit_clean in {"l", "lt", "lts", "litro", "litros"}:
        return "l"
    if unit_clean in {"ml", "cc"}:
        return "ml"
    if unit_clean in {"un", "uni", "unidad", "unidades"}:
        return "un"
    return unit_clean or None


def detect_presentation(name: Any) -> dict[str, Any]:
    text = clean_text(name)
    match = None
    for match in PRESENTATION_RE.finditer(text):
        pass
    pack_match = PACK_RE.search(text)
    if not match:
        if pack_match:
            qty = float(pack_match.group("qty"))
            return {
                "presentation_qty": qty,
                "presentation_unit": "un",
                "normalized_qty": qty,
                "normalized_unit": "un",
            }
        return {
            "presentation_qty": None,
            "presentation_unit": None,
            "normalized_qty": None,
            "normalized_unit": None,
        }
    qty = float(match.group("qty").replace(",", "."))
    unit = normalize_unit(match.group("unit"))
    normalized_qty = qty
    normalized_unit = unit
    if unit == "g":
        normalized_qty = qty / 1000
        normalized_unit = "kg"
    elif unit == "ml":
        normalized_qty = qty / 1000
        normalized_unit = "l"
    return {
        "presentation_qty": qty,
        "presentation_unit": unit,
        "normalized_qty": normalized_qty,
        "normalized_unit": normalized_unit,
    }


def calculate_reference_price(price: Any, name: Any = None, qty: Any = None, unit: str | None = None) -> tuple[float | None, str | None]:
    price_float = to_float(price)
    if price_float is None or price_float <= 0:
        return None, None
    if qty is None or unit is None:
        detected = detect_presentation(name)
        qty = detected["normalized_qty"]
        unit = detected["normalized_unit"]
    try:
        qty_float = float(qty) if qty is not None else None
    except (TypeError, ValueError):
        qty_float = None
    if not qty_float or qty_float <= 0 or not unit:
        return None, None
    if unit in {"kg", "l", "un"}:
        return round(price_float / qty_float, 2), unit
    return None, None


def infer_brand(product_name: Any, explicit_brand: Any = None) -> str | None:
    explicit = clean_text(explicit_brand).upper()
    if explicit and explicit not in {"NO DISPONIBLE", "NAN", "SIN MARCA"}:
        return explicit
    raw = str(product_name or "").strip()
    first_words = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+", raw)
    if not first_words:
        return None
    if first_words[0].isupper() and len(first_words[0]) > 2:
        return unidecode(first_words[0]).upper()
    return None


def product_search_key(name: Any, brand: Any = None) -> str:
    parts = [clean_text(brand), clean_text(name)]
    return " ".join(part for part in parts if part)


def normalize_price_record(record: dict[str, Any]) -> dict[str, Any]:
    product_name = record.get("product_name_raw") or record.get("Producto") or record.get("producto") or record.get("name")
    brand = infer_brand(product_name, record.get("brand") or record.get("Marca") or record.get("marca"))
    price_list = to_float(record.get("price_list") or record.get("Precio") or record.get("precio"))
    price_promo_1 = to_float(record.get("price_promo_1") or record.get("precio_promo_1"))
    price_promo_2 = to_float(record.get("price_promo_2") or record.get("precio_promo_2"))
    best_general = price_list
    if price_promo_1 is not None and (best_general is None or price_promo_1 < best_general):
        best_general = price_promo_1
    best_conditional = price_promo_2
    presentation = detect_presentation(product_name)
    reference_price, reference_unit = calculate_reference_price(
        best_general,
        product_name,
        presentation["normalized_qty"],
        presentation["normalized_unit"],
    )
    clean_name = clean_text(product_name)
    output = {
        **record,
        "product_name_raw": str(product_name or "").strip(),
        "product_name_clean": clean_name,
        "brand": brand,
        "price_list": price_list,
        "price_promo_1": price_promo_1,
        "price_promo_2": price_promo_2,
        "best_general_price": best_general,
        "best_conditional_price": best_conditional,
        "reference_price": reference_price,
        "reference_unit": reference_unit,
        "presentation_qty": presentation["presentation_qty"],
        "presentation_unit": presentation["presentation_unit"],
        "normalized_unit": presentation["normalized_unit"],
        "search_key": product_search_key(clean_name, brand),
    }
    return output

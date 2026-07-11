from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PRICE_REQUIRED_COLUMNS = [
    "comercio",
    "producto",
    "precio",
    "grupo_comparacion",
    "precio_unitario_comparable",
    "cantidad_base",
    "unidad_base",
    "confianza_matching",
]

LIST_REQUIRED_COLUMNS = [
    "item_lista",
    "grupo_comparacion",
    "cantidad",
    "unidad",
    "prioridad",
]

COMPARISON_COLUMNS = [
    "comercio",
    "productos_encontrados",
    "productos_faltantes",
    "cobertura_lista_pct",
    "costo_total_estimado",
    "diferencia_vs_mas_barato",
    "ahorro_vs_mas_caro",
    "ranking_precio",
]

BEST_COLUMNS = [
    "item_lista",
    "grupo_comparacion",
    "comercio_recomendado",
    "producto_encontrado",
    "precio_final",
    "precio_unitario_comparable",
    "ahorro_vs_promedio",
    "confianza_matching",
]

UNIT_ALIASES = {
    "kg": "kg",
    "kilo": "kg",
    "kilos": "kg",
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
class ShoppingItem:
    item_lista: str
    grupo_comparacion: str
    cantidad: float
    unidad: str
    prioridad: str


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


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
    return number if number >= 0 else None


def format_money(value: float | None) -> str:
    return "" if value is None else f"{value:.2f}"


def format_pct(value: float) -> str:
    return f"{value:.2f}"


def normalize_unit(unit: Any) -> str:
    return UNIT_ALIASES.get(str(unit or "").strip().lower(), str(unit or "").strip().lower())


def to_base_quantity(quantity: float, unit: str) -> tuple[float, str] | None:
    normalized = normalize_unit(unit)
    if normalized == "kg":
        return quantity, "kg"
    if normalized == "g":
        return quantity / 1000, "kg"
    if normalized == "l":
        return quantity, "l"
    if normalized == "ml":
        return quantity / 1000, "l"
    if normalized == "un":
        return quantity, "un"
    return None


def validate_columns(rows: list[dict[str, str]], required: list[str], name: str) -> None:
    if not rows:
        raise ValueError(f"El archivo {name} esta vacio.")
    columns = set(rows[0].keys())
    missing = [column for column in required if column not in columns]
    if missing:
        raise ValueError(f"Faltan columnas en {name}: {', '.join(missing)}")


def load_shopping_list(path: Path) -> list[ShoppingItem]:
    rows = read_csv(path)
    validate_columns(rows, LIST_REQUIRED_COLUMNS, "lista")
    items: list[ShoppingItem] = []
    for index, row in enumerate(rows, start=2):
        quantity = parse_number(row.get("cantidad"))
        converted = to_base_quantity(quantity or 0, row.get("unidad", ""))
        if quantity is None or quantity <= 0 or converted is None:
            raise ValueError(f"Fila {index}: cantidad o unidad invalida en lista.")
        base_quantity, base_unit = converted
        group = row.get("grupo_comparacion", "").strip()
        if not group:
            raise ValueError(f"Fila {index}: grupo_comparacion vacio.")
        items.append(
            ShoppingItem(
                item_lista=row.get("item_lista", "").strip() or group,
                grupo_comparacion=group,
                cantidad=base_quantity,
                unidad=base_unit,
                prioridad=row.get("prioridad", "").strip(),
            )
        )
    return items


def load_prices(path: Path) -> list[dict[str, str]]:
    rows = read_csv(path)
    validate_columns(rows, PRICE_REQUIRED_COLUMNS, "precios")
    return rows


def row_base_price(row: dict[str, str]) -> float | None:
    effective = parse_number(row.get("precio_efectivo"))
    if effective is not None:
        return effective
    return parse_number(row.get("precio"))


def row_comparable_price(row: dict[str, str]) -> float | None:
    effective = parse_number(row.get("precio_unitario_efectivo"))
    if effective is not None:
        return effective
    return parse_number(row.get("precio_unitario_comparable"))


def price_mode(rows: list[dict[str, str]]) -> str:
    return "precio_efectivo" if any(row.get("precio_efectivo") for row in rows) else "precio_gondola"


def row_cost_for_item(row: dict[str, str], item: ShoppingItem) -> float | None:
    price = row_base_price(row)
    comparable = row_comparable_price(row)
    row_unit = normalize_unit(row.get("unidad_base"))
    if item.unidad == "un" and price is not None:
        return price * item.cantidad
    if comparable is not None and row_unit == item.unidad:
        return comparable * item.cantidad
    return None


def best_offer_for_item(rows: list[dict[str, str]], item: ShoppingItem, commerce: str | None = None) -> dict[str, Any] | None:
    candidates = []
    for row in rows:
        if row.get("grupo_comparacion") != item.grupo_comparacion:
            continue
        if commerce is not None and row.get("comercio") != commerce:
            continue
        cost = row_cost_for_item(row, item)
        if cost is None:
            continue
        candidates.append((cost, row))
    if not candidates:
        return None
    cost, row = min(candidates, key=lambda pair: (pair[0], pair[1].get("comercio", ""), pair[1].get("sucursal", "")))
    return {"cost": cost, "row": row}


def build_comparison(prices: list[dict[str, str]], items: list[ShoppingItem]) -> list[dict[str, str]]:
    commerces = sorted({row.get("comercio", "") for row in prices if row.get("comercio")})
    raw_rows: list[dict[str, Any]] = []
    total_items = len(items)

    for commerce in commerces:
        found = 0
        missing_items = []
        total_cost = 0.0
        for item in items:
            offer = best_offer_for_item(prices, item, commerce)
            if offer is None:
                missing_items.append(item.item_lista)
                continue
            found += 1
            total_cost += offer["cost"]
        coverage = found / total_items * 100 if total_items else 0
        raw_rows.append(
            {
                "comercio": commerce,
                "productos_encontrados": found,
                "productos_faltantes": len(missing_items),
                "faltantes_detalle": "; ".join(missing_items),
                "cobertura_lista_pct": coverage,
                "costo_total_estimado": total_cost,
            }
        )

    if not raw_rows:
        return []

    max_found = max(row["productos_encontrados"] for row in raw_rows)
    comparable = [row for row in raw_rows if row["productos_encontrados"] == max_found]
    cheapest = min(row["costo_total_estimado"] for row in comparable) if comparable else 0
    most_expensive = max(row["costo_total_estimado"] for row in comparable) if comparable else 0
    raw_rows.sort(key=lambda row: (-row["productos_encontrados"], row["costo_total_estimado"], row["comercio"]))

    out = []
    for rank, row in enumerate(raw_rows, start=1):
        same_coverage = row["productos_encontrados"] == max_found
        out.append(
            {
                "comercio": row["comercio"],
                "productos_encontrados": str(row["productos_encontrados"]),
                "productos_faltantes": row["faltantes_detalle"] if row["faltantes_detalle"] else "0",
                "cobertura_lista_pct": format_pct(row["cobertura_lista_pct"]),
                "costo_total_estimado": format_money(row["costo_total_estimado"]),
                "diferencia_vs_mas_barato": format_money(row["costo_total_estimado"] - cheapest) if same_coverage else "",
                "ahorro_vs_mas_caro": format_money(most_expensive - row["costo_total_estimado"]) if same_coverage else "",
                "ranking_precio": str(rank),
            }
        )
    return out


def build_best_split(prices: list[dict[str, str]], items: list[ShoppingItem]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in items:
        offers = []
        for row in prices:
            if row.get("grupo_comparacion") != item.grupo_comparacion:
                continue
            cost = row_cost_for_item(row, item)
            if cost is None:
                continue
            offers.append((cost, row))
        if not offers:
            rows.append(
                {
                    "item_lista": item.item_lista,
                    "grupo_comparacion": item.grupo_comparacion,
                    "comercio_recomendado": "",
                    "producto_encontrado": "",
                    "precio_final": "",
                    "precio_unitario_comparable": "",
                    "ahorro_vs_promedio": "",
                    "confianza_matching": "",
                }
            )
            continue
        average = sum(cost for cost, _ in offers) / len(offers)
        best_cost, best_row = min(offers, key=lambda pair: (pair[0], pair[1].get("comercio", ""), pair[1].get("sucursal", "")))
        rows.append(
            {
                "item_lista": item.item_lista,
                "grupo_comparacion": item.grupo_comparacion,
                "comercio_recomendado": best_row.get("comercio", ""),
                "producto_encontrado": best_row.get("producto", ""),
                "precio_final": format_money(best_cost),
                "precio_unitario_comparable": format_money(row_comparable_price(best_row)),
                "ahorro_vs_promedio": format_money(average - best_cost),
                "confianza_matching": best_row.get("confianza_matching", ""),
            }
        )
    rows.sort(key=lambda row: (row["grupo_comparacion"], row["item_lista"]))
    return rows


def calculate_shopping_list(
    prices_path: Path,
    shopping_list_path: Path,
    comparison_output: Path,
    best_output: Path,
    report_path: Path | None = None,
) -> dict[str, Any]:
    prices = load_prices(prices_path)
    items = load_shopping_list(shopping_list_path)
    comparison = build_comparison(prices, items)
    best_split = build_best_split(prices, items)
    write_csv(comparison_output, comparison, COMPARISON_COLUMNS)
    write_csv(best_output, best_split, BEST_COLUMNS)

    full_coverage = [row for row in comparison if row["productos_faltantes"] == "0"]
    cheapest = full_coverage[0] if full_coverage else (comparison[0] if comparison else None)
    report = {
        "prices": str(prices_path),
        "shopping_list": str(shopping_list_path),
        "comparison_output": str(comparison_output),
        "best_output": str(best_output),
        "items": len(items),
        "commerces": len(comparison),
        "price_mode": price_mode(prices),
        "best_commerce": cheapest["comercio"] if cheapest else "",
        "best_cost": cheapest["costo_total_estimado"] if cheapest else "",
        "split_items": len(best_split),
    }
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    root = project_root()
    parser = argparse.ArgumentParser(description="Calcula ranking de comercios y mejor compra por producto para una lista.")
    parser.add_argument("--prices", default=str(root / "data" / "processed" / "precios_matcheados.csv"))
    parser.add_argument("--list", default=str(root / "data" / "sample" / "lista_compra_demo.csv"))
    parser.add_argument("--comparison-output", default=str(root / "data" / "processed" / "comparacion_lista_compra.csv"))
    parser.add_argument("--best-output", default=str(root / "data" / "processed" / "mejor_compra_por_producto.csv"))
    parser.add_argument("--report", default=str(root / "data" / "processed" / "lista_compra_reporte.json"))
    args = parser.parse_args()

    try:
        report = calculate_shopping_list(
            Path(args.prices),
            Path(args.list),
            Path(args.comparison_output),
            Path(args.best_output),
            Path(args.report),
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"ok": True, **report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

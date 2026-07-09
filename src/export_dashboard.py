from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
import csv
import re


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def rows(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":"), default=str), encoding="utf-8")


CHAIN_BY_SOURCE = {
    "vea": "Vea",
    "carrefour": "Carrefour",
    "masonline": "ChangoMas",
    "atomo": "Atomo Conviene",
    "maxiconsumo": "Maxiconsumo",
    "laanonima": "La Anonima",
    "cabral": "Cabral Mayorista",
    "la_cumbre": "La Cumbre Sanjuanina",
    "yaguar": "Yaguar",
    "makro": "Makro",
    "cafe_america": "Cafe America",
    "la_nobleza": "La Nobleza",
    "la_estrella": "La Estrella",
    "basualdo": "Basualdo",
}


def plain(value: Any) -> str:
    text = str(value or "").lower()
    replacements = str.maketrans("áéíóúüñ", "aeiouun")
    return text.translate(replacements)


def canonical_chain(row: dict[str, Any]) -> str:
    return CHAIN_BY_SOURCE.get(str(row.get("source_id") or ""), str(row.get("chain") or "Sin cadena").strip())


def canonical_category(value: Any) -> str:
    text = plain(value)
    if "catalog" in text or "folleto" in text:
        return "Catalogo oficial"
    if "bebida" in text:
        return "Bebidas"
    if "limpieza" in text:
        return "Limpieza"
    if "lact" in text or "fiambre" in text or "fresco" in text:
        return "Lacteos y frescos"
    if "carne" in text or "pescado" in text or "congel" in text:
        return "Carnes y congelados"
    if "almacen" in text:
        return "Almacen"
    if "home san juan" in text or "oferta" in text:
        return "Ofertas mayoristas"
    return str(value or "Sin categoria").strip() or "Sin categoria"


def enrich_price_rows(price_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for row in price_rows:
        item = dict(row)
        item["chain"] = canonical_chain(item)
        item["category"] = canonical_category(item.get("category"))
        enriched.append(item)
    return enriched


def to_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def infer_offer_type(text: str) -> str:
    normalized = text.lower()
    if re.search(r"\b(visa|master|amex|american|tarjeta|banco|cuota|naranja|cabal|modo|mercado pago)\b", normalized):
        return "tarjeta"
    if re.search(r"\b(2x1|3x2|4x3|segunda|2do|lleva|llevando|combo|bulto)\b", normalized):
        return "volumen"
    if re.search(r"\b(catalogo|folleto|oferta imperdible)\b", normalized):
        return "catalogo"
    return "precio"


def discount_from_row(row: dict[str, Any]) -> tuple[float | None, float | None]:
    list_price = to_float(row.get("price_list"))
    best_price = to_float(row.get("best_general_price"))
    if not list_price or not best_price or list_price <= best_price:
        return None, None
    amount = round(list_price - best_price, 2)
    pct = round((amount / list_price) * 100, 2)
    return amount, pct


def build_promotions(price_rows: list[dict[str, Any]], catalog_links: list[dict[str, Any]], limit: int = 600) -> list[dict[str, Any]]:
    promotions: list[dict[str, Any]] = []
    for row in price_rows:
        promo_texts = [row.get("promo_1_text"), row.get("promo_2_text")]
        promo_text = " | ".join(str(text).strip() for text in promo_texts if text)
        discount_amount, discount_pct = discount_from_row(row)
        conditional_price = to_float(row.get("best_conditional_price"))
        has_signal = promo_text or discount_amount or conditional_price
        if not has_signal:
            continue
        offer_type = infer_offer_type(promo_text)
        promotions.append(
            {
                "source_id": row.get("source_id"),
                "chain": row.get("chain"),
                "branch_name": row.get("branch_name"),
                "city": row.get("city"),
                "category": row.get("category") or "Sin categoria",
                "product_name": row.get("product_name_raw"),
                "brand": row.get("brand"),
                "price_list": row.get("price_list"),
                "best_price": row.get("best_general_price"),
                "conditional_price": row.get("best_conditional_price"),
                "discount_amount": discount_amount,
                "discount_pct": discount_pct,
                "promo_text": promo_text or "Precio detectado por debajo del precio lista",
                "offer_type": offer_type,
                "url": row.get("url"),
                "confidence_score": row.get("confidence_score"),
                "capture_date": row.get("capture_date"),
            }
        )
    for item in catalog_links:
        text = " ".join(str(item.get(key) or "") for key in ["title", "chain", "source_id", "url"])
        promotions.append(
            {
                "source_id": item.get("source_id"),
                "chain": CHAIN_BY_SOURCE.get(str(item.get("source_id") or ""), item.get("chain") or item.get("source_id")),
                "branch_name": None,
                "city": "San Juan",
                "category": "Catalogo oficial",
                "product_name": item.get("title") or "Catalogo oficial",
                "brand": None,
                "price_list": None,
                "best_price": None,
                "conditional_price": None,
                "discount_amount": None,
                "discount_pct": None,
                "promo_text": "Catalogo, folleto u oferta oficial para revisar vigencia y condiciones",
                "offer_type": infer_offer_type(text),
                "url": item.get("url"),
                "confidence_score": None,
                "capture_date": None,
            }
        )
    promotions.sort(
        key=lambda row: (
            row.get("discount_pct") is None,
            -(row.get("discount_pct") or 0),
            str(row.get("chain") or ""),
        )
    )
    return promotions[:limit]


def build_payment_options(promotions: list[dict[str, Any]], sources: list[dict[str, Any]], limit: int = 250) -> list[dict[str, Any]]:
    options = []
    seen = set()
    for item in promotions:
        text = str(item.get("promo_text") or "")
        if infer_offer_type(text) != "tarjeta":
            continue
        key = (item.get("chain"), text, item.get("url"))
        if key in seen:
            continue
        seen.add(key)
        options.append(
            {
                "chain": item.get("chain"),
                "source_id": item.get("source_id"),
                "title": text,
                "category": item.get("category"),
                "product_name": item.get("product_name"),
                "discount_pct": item.get("discount_pct"),
                "conditional_price": item.get("conditional_price"),
                "url": item.get("url"),
                "confidence_score": item.get("confidence_score"),
                "capture_date": item.get("capture_date"),
            }
        )
    for source in sources:
        if not source.get("has_promotions"):
            continue
        url = source.get("offers_url") or source.get("base_url")
        key = (source.get("name"), "Pagina oficial de promociones", url)
        if key in seen:
            continue
        seen.add(key)
        options.append(
            {
                "chain": source.get("name"),
                "source_id": source.get("source_id"),
                "title": "Pagina oficial de promociones y medios de pago",
                "category": "Promociones oficiales",
                "product_name": None,
                "discount_pct": None,
                "conditional_price": None,
                "url": url,
                "confidence_score": source.get("confidence_score"),
                "capture_date": None,
            }
        )
    return options[:limit]


def export_dashboard(
    db_path: str | Path = "database/precios_san_juan.sqlite",
    export_dir: str | Path = "data/export",
    max_prices: int = 5000,
) -> dict[str, int]:
    conn = connect(db_path)
    out = Path(export_dir)
    prices = rows(
        conn,
        """
        SELECT capture_date, source_id, chain, branch_name, city, product_name_raw,
               product_name_clean, brand, category, price_list, price_promo_1,
               promo_1_text, price_promo_2, promo_2_text, best_general_price,
               best_conditional_price, reference_price, reference_unit, url,
               confidence_score
        FROM prices
        WHERE best_general_price IS NOT NULL
          AND source_id <> 'historical_csv'
        ORDER BY capture_date DESC, confidence_score DESC, best_general_price ASC
        LIMIT ?
        """,
        (max_prices,),
    )
    prices = enrich_price_rows(prices)
    products = rows(
        conn,
        """
        SELECT product_id, name_raw, name_clean, brand, category, presentation_qty,
               presentation_unit, normalized_unit, source_id, search_key
        FROM products
        ORDER BY name_clean
        LIMIT 10000
        """,
    )
    stores = rows(conn, "SELECT * FROM stores ORDER BY chain, city, branch_name")
    sources = rows(conn, "SELECT * FROM sources ORDER BY priority, name")
    audit = {
        "prices_count": conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0],
        "products_count": conn.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        "stores_count": conn.execute("SELECT COUNT(*) FROM stores").fetchone()[0],
        "sources_count": conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0],
        "latest_capture_date": conn.execute("SELECT MAX(capture_date) FROM prices").fetchone()[0],
        "runs": rows(conn, "SELECT * FROM scrape_runs ORDER BY started_at DESC LIMIT 20"),
    }
    catalog_links = read_catalog_links(Path(db_path).resolve().parents[1] if Path(db_path).is_absolute() else Path("."))
    conn.close()
    promotions = build_promotions(prices, catalog_links)
    payment_options = build_payment_options(promotions, sources)
    write_json(out / "precios_actuales.json", prices)
    write_json(out / "productos.json", products)
    write_json(out / "sucursales.json", stores)
    write_json(out / "fuentes.json", sources)
    write_json(out / "auditoria.json", audit)
    write_json(out / "catalogos_oficiales.json", catalog_links)
    write_json(out / "promociones.json", promotions)
    write_json(out / "tarjetas.json", payment_options)
    return {
        "precios_actuales": len(prices),
        "productos": len(products),
        "sucursales": len(stores),
        "fuentes": len(sources),
        "catalogos_oficiales": len(catalog_links),
        "promociones": len(promotions),
        "tarjetas": len(payment_options),
    }


def read_catalog_links(project_root: Path) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    processed = project_root / "data" / "processed"
    if not processed.exists():
        return rows_out
    for path in processed.glob("*/*catalog_links.csv"):
        try:
            with path.open("r", encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    row["artifact_path"] = str(path.relative_to(project_root))
                    rows_out.append(row)
        except Exception:
            continue
    seen = set()
    unique = []
    for row in rows_out:
        key = row.get("url")
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


if __name__ == "__main__":
    result = export_dashboard()
    print(result)

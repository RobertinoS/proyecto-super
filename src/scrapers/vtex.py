from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urlencode

from normalize import normalize_price_record
from scrapers.base import BaseScraper, load_source_config


def nested_value(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return None


def teaser_name(teaser: dict[str, Any]) -> str | None:
    value = nested_value(teaser, "Name", "name", "<Name>k__BackingField")
    return str(value).strip() if value else None


def teaser_percent(teaser: dict[str, Any]) -> float | None:
    effects = nested_value(teaser, "Effects", "effects", "<Effects>k__BackingField") or {}
    params = nested_value(effects, "Parameters", "parameters", "<Parameters>k__BackingField") or []
    for param in params:
        name = str(nested_value(param, "Name", "name", "<Name>k__BackingField") or "").lower()
        value = nested_value(param, "Value", "value", "<Value>k__BackingField")
        if "percentualdiscount" not in name:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    return None


def extract_teaser_promotions(offer: dict[str, Any]) -> list[dict[str, Any]]:
    promotions = []
    for teaser in offer.get("Teasers") or []:
        name = teaser_name(teaser)
        if not name:
            continue
        percent = teaser_percent(teaser)
        text = f"{name} {percent:.0f}% off" if percent else name
        promotions.append({"text": text, "percent": percent})
    return promotions


def best_installment_text(offer: dict[str, Any], price: float | None) -> str | None:
    if not price:
        return None
    candidates = []
    for item in offer.get("Installments") or []:
        try:
            installments = int(item.get("NumberOfInstallments") or 0)
            total = float(item.get("TotalValuePlusInterestRate") or 0)
        except (TypeError, ValueError):
            continue
        if installments <= 1 or not total:
            continue
        interest = item.get("InterestRate")
        no_interest = interest in (None, 0, 0.0) or float(interest or 0) == 0
        if no_interest and total <= price * 1.01:
            candidates.append((installments, str(item.get("PaymentSystemName") or "tarjeta").strip()))
    if not candidates:
        return None
    installments, card = sorted(candidates, key=lambda item: item[0], reverse=True)[0]
    return f"Hasta {installments} cuotas sin interes con {card}"


def offer_from_product(product: dict[str, Any]) -> dict[str, Any]:
    items = product.get("items") or []
    item = items[0] if items else {}
    sellers = item.get("sellers") or []
    seller = sellers[0] if sellers else {}
    offer = seller.get("commertialOffer") or {}
    promotions = extract_teaser_promotions(offer)
    price = offer.get("Price")
    card_promo_price = None
    if promotions and price:
        percents = [promo["percent"] for promo in promotions if promo.get("percent")]
        if percents:
            card_promo_price = round(float(price) * (1 - max(percents) / 100), 2)
    return {
        "sku": item.get("itemId") or product.get("productId"),
        "ean": item.get("ean"),
        "price": price,
        "list_price": offer.get("ListPrice"),
        "available": offer.get("AvailableQuantity"),
        "image": ((item.get("images") or [{}])[0] or {}).get("imageUrl"),
        "teaser_text": " | ".join(promo["text"] for promo in promotions[:3]) or None,
        "card_promo_price": card_promo_price,
        "installment_text": best_installment_text(offer, price),
    }


class VtexScraper(BaseScraper):
    def product_search(self, path: str | None = None, fq: str | None = None, page_size: int = 50, max_pages: int = 4) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for page in range(max_pages):
            start = page * page_size
            end = start + page_size - 1
            params = {"_from": start, "_to": end}
            if fq:
                params["fq"] = fq
                endpoint = f"{self.config.base_url.rstrip('/')}/api/catalog_system/pub/products/search?{urlencode(params)}"
            else:
                endpoint = f"{self.config.base_url.rstrip('/')}/api/catalog_system/pub/products/search/{path or ''}?{urlencode(params)}"
            response = self.fetch(endpoint)
            self.save_raw(f"vtex_{path or fq or 'search'}_{page}.json", response.text)
            try:
                products = response.json()
            except Exception:
                products = []
            if not products:
                break
            for product in products:
                offer = offer_from_product(product)
                if offer["price"] is None:
                    continue
                list_price = offer["list_price"] or offer["price"]
                if list_price and offer["price"] and list_price > offer["price"] * 5:
                    list_price = offer["price"]
                promo_price = offer["price"] if offer["price"] and list_price and offer["price"] < list_price else None
                price_promo_2 = offer["card_promo_price"]
                promo_1_text = "Precio online menor al precio lista" if promo_price else offer["teaser_text"]
                promo_2_text = offer["teaser_text"] if promo_price and offer["teaser_text"] else offer["installment_text"]
                category_tree = product.get("categories") or []
                category = category_tree[-1].strip("/") if category_tree else (path or fq or "")
                records.append(
                    normalize_price_record(
                        {
                            "capture_date": datetime.now().date().isoformat(),
                            "source_id": self.config.source_id,
                            "chain": self.config.name,
                            "branch_name": "Online",
                            "province": "San Juan",
                            "city": "San Juan",
                            "product_name_raw": product.get("productName"),
                            "brand": product.get("brand"),
                            "category": category,
                            "price_list": list_price,
                            "price_promo_1": promo_price,
                            "promo_1_text": promo_1_text,
                            "price_promo_2": price_promo_2,
                            "promo_2_text": promo_2_text,
                            "url": product.get("link"),
                            "confidence_score": self.config.confidence_score,
                            "source_product_id": product.get("productId"),
                            "ean": offer["ean"],
                        }
                    )
                )
        return dedupe(records)


def dedupe(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    unique = []
    for row in records:
        key = (row.get("source_id"), row.get("source_product_id"), row.get("product_name_clean"), row.get("best_general_price"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def run_vtex_paths(source_id: str, paths: list[str], page_size: int = 50, max_pages: int = 4) -> list[dict[str, Any]]:
    scraper = VtexScraper(load_source_config(source_id))
    records: list[dict[str, Any]] = []
    for path in paths:
        records.extend(scraper.product_search(path=path, page_size=page_size, max_pages=max_pages))
    scraper.save_processed(records, [{"source_id": source_id, "records_found": len(records), "method": "vtex_api"}])
    return dedupe(records)


def run_vtex_clusters(source_id: str, clusters: dict[str, str], page_size: int = 50, max_pages: int = 4) -> list[dict[str, Any]]:
    scraper = VtexScraper(load_source_config(source_id))
    records: list[dict[str, Any]] = []
    for category, cluster_id in clusters.items():
        rows = scraper.product_search(fq=f"productClusterIds:{cluster_id}", page_size=page_size, max_pages=max_pages)
        for row in rows:
            row["category"] = category
        records.extend(rows)
    scraper.save_processed(records, [{"source_id": source_id, "records_found": len(records), "method": "vtex_cluster_api"}])
    return dedupe(records)

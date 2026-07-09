from __future__ import annotations

import re
from datetime import datetime

from normalize import normalize_price_record, parse_argentine_price
from scrapers.base import BaseScraper, load_source_config


MAXICONSUMO_PAGES = {
    "Home San Juan": "https://www.maxiconsumo.com/sucursal_san_juan",
    "Ofertas San Juan": "https://www.maxiconsumo.com/sucursal_san_juan/ofertas",
}


class MaxiconsumoScraper(BaseScraper):
    def parse_page(self, category: str, url: str) -> list[dict]:
        from bs4 import BeautifulSoup

        response = self.fetch(url)
        self.save_raw(f"maxiconsumo_{category}.html", response.text)
        soup = BeautifulSoup(response.text, "lxml")
        records = []
        cards = soup.select("li.product-item, .product-item-info")
        for card in cards:
            title = card.select_one(".product-item-link, .product-item-name")
            price_nodes = card.select(".price")
            if not title or not price_nodes:
                continue
            prices = [parse_argentine_price(node.get_text(" ", strip=True)) for node in price_nodes]
            prices = [price for price in prices if price is not None and price >= 50]
            if not prices:
                continue
            text = card.get_text(" ", strip=True)
            sku_match = re.search(r"SKU\s+([0-9A-Za-z_-]+)", text)
            link = title.get("href") if title.name == "a" else None
            records.append(
                normalize_price_record(
                    {
                        "capture_date": datetime.now().date().isoformat(),
                        "source_id": self.config.source_id,
                        "chain": self.config.name,
                        "branch_name": "San Juan / Pocitos",
                        "province": "San Juan",
                        "department": "Pocito",
                        "city": "Pocito",
                        "product_name_raw": title.get_text(" ", strip=True),
                        "brand": None,
                        "category": category,
                        "price_list": prices[0],
                        "price_promo_1": min(prices) if min(prices) < prices[0] else None,
                        "promo_1_text": "Precio unitario por bulto cerrado" if len(prices) > 1 and min(prices) < prices[0] else None,
                        "url": link or url,
                        "confidence_score": self.config.confidence_score,
                        "source_product_id": sku_match.group(1) if sku_match else None,
                    }
                )
            )
        return dedupe(records)


def dedupe(records: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for row in records:
        key = (row.get("source_product_id"), row.get("product_name_clean"), row.get("best_general_price"))
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def run_maxiconsumo() -> list[dict]:
    scraper = MaxiconsumoScraper(load_source_config("maxiconsumo"))
    records = []
    for category, url in MAXICONSUMO_PAGES.items():
        records.extend(scraper.parse_page(category, url))
    scraper.save_processed(records, [{"source_id": "maxiconsumo", "records_found": len(records), "method": "magento_html"}])
    return dedupe(records)

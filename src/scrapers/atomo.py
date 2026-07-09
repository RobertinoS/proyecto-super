from __future__ import annotations

from datetime import datetime

from normalize import normalize_price_record, parse_argentine_price
from scrapers.base import BaseScraper, load_source_config


ATOMO_CATEGORIES = {
    "Almacen": "https://atomoconviene.com/atomo-ecommerce/3-almacen",
    "Bebidas": "https://atomoconviene.com/atomo-ecommerce/81-bebidas",
    "Carnes y congelados": "https://atomoconviene.com/atomo-ecommerce/300-carnes-y-congelados",
    "Lacteos y fiambres": "https://atomoconviene.com/atomo-ecommerce/226-lacteos-fiambres",
    "Limpieza": "https://atomoconviene.com/atomo-ecommerce/85-limpieza",
}


class AtomoScraper(BaseScraper):
    def parse_category(self, category: str, url: str, max_pages: int = 4) -> list[dict]:
        from bs4 import BeautifulSoup

        records = []
        seen_pages = set()
        for page in range(1, max_pages + 1):
            page_url = f"{url}?page={page}"
            response = self.fetch(page_url)
            self.save_raw(f"atomo_{category}_{page}.html", response.text)
            soup = BeautifulSoup(response.text, "lxml")
            cards = soup.select(".card-body")
            signature = tuple(card.get_text(" ", strip=True)[:80] for card in cards[:5])
            if not cards or signature in seen_pages:
                break
            seen_pages.add(signature)
            for card in cards:
                title = card.select_one(".product-title")
                price = card.select_one(".price")
                image = card.select_one("img")
                link = card.select_one("a[href]")
                if not title or not price:
                    continue
                value = parse_argentine_price(price.get_text(" ", strip=True))
                if value is None or value < 50:
                    continue
                records.append(
                    normalize_price_record(
                        {
                            "capture_date": datetime.now().date().isoformat(),
                            "source_id": self.config.source_id,
                            "chain": self.config.name,
                            "branch_name": "Online",
                            "province": "San Juan",
                            "city": "San Juan",
                            "product_name_raw": title.get_text(" ", strip=True),
                            "brand": None,
                            "category": category,
                            "price_list": value,
                            "url": link.get("href") if link else page_url,
                            "confidence_score": self.config.confidence_score,
                            "source_product_id": None,
                            "image_url": image.get("src") if image else None,
                        }
                    )
                )
        return dedupe(records)


def dedupe(records: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for row in records:
        key = (row.get("product_name_clean"), row.get("price_list"), row.get("category"))
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def run_atomo(max_pages: int = 4) -> list[dict]:
    scraper = AtomoScraper(load_source_config("atomo"))
    records = []
    for category, url in ATOMO_CATEGORIES.items():
        records.extend(scraper.parse_category(category, url, max_pages=max_pages))
    scraper.save_processed(records, [{"source_id": "atomo", "records_found": len(records), "method": "html_card_body"}])
    return dedupe(records)

from __future__ import annotations

import csv
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

from normalize import normalize_price_record, parse_argentine_price

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None


DEFAULT_UA = "Mozilla/5.0 ComparadorPreciosSanJuan/1.0"
STRICT_PRICE_RE = re.compile(r"\$\s*([0-9]{1,3}(?:[.\s][0-9]{3})*(?:,[0-9]{1,2})?|[0-9]+(?:,[0-9]{1,2})?)")


@dataclass
class ScraperConfig:
    source_id: str
    name: str
    base_url: str
    offers_url: str | None
    confidence_score: int
    requires_js: bool
    requires_location: bool


def load_source_config(source_id: str, config_path: str | Path = "config/fuentes.yml") -> ScraperConfig:
    if yaml is None:
        raise RuntimeError("PyYAML no esta instalado. Ejecuta pip install -r requirements.txt")
    data = yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}
    for source in data.get("sources", []):
        if source.get("source_id") == source_id:
            return ScraperConfig(
                source_id=source_id,
                name=source.get("name", source_id),
                base_url=source.get("base_url"),
                offers_url=source.get("offers_url"),
                confidence_score=int(source.get("confidence_score") or 70),
                requires_js=bool(source.get("requires_js")),
                requires_location=bool(source.get("requires_location")),
            )
    raise KeyError(f"No existe source_id={source_id} en {config_path}")


def parse_visible_price(text: str) -> float | None:
    match = STRICT_PRICE_RE.search(text.replace("\xa0", " "))
    if not match:
        return None
    price = parse_argentine_price(match.group(1))
    if price is None or price < 50:
        return None
    return price


class BaseScraper:
    def __init__(
        self,
        config: ScraperConfig,
        timeout: int = 30,
        user_agent: str = DEFAULT_UA,
        rate_limit_seconds: float = 1.5,
        project_root: str | Path = ".",
    ) -> None:
        self.config = config
        self.timeout = timeout
        self.rate_limit_seconds = rate_limit_seconds
        self.project_root = Path(project_root)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.raw_dir = self.project_root / "data" / "raw" / config.source_id
        self.processed_dir = self.project_root / "data" / "processed" / config.source_id
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def fetch(self, url: str) -> requests.Response:
        last_exc: Exception | None = None
        for attempt in range(1, 4):
            try:
                response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
                response.raise_for_status()
                time.sleep(self.rate_limit_seconds)
                return response
            except Exception as exc:
                last_exc = exc
                time.sleep(self.rate_limit_seconds * attempt)
        assert last_exc is not None
        raise last_exc

    def save_raw(self, name: str, text: str) -> Path:
        safe_name = re.sub(r"[^a-zA-Z0-9_.-]+", "_", name)[:120]
        path = self.raw_dir / safe_name
        path.write_text(text, encoding="utf-8", errors="ignore")
        return path

    def save_processed(self, records: list[dict[str, Any]], diagnostics: list[dict[str, Any]]) -> dict[str, Any]:
        today = datetime.now().strftime("%Y%m%d")
        records_path = self.processed_dir / f"{self.config.source_id}_{today}.csv"
        diagnostics_path = self.processed_dir / f"{self.config.source_id}_diagnostics_{today}.csv"
        if records:
            pd.DataFrame(records).to_csv(records_path, index=False, encoding="utf-8")
        else:
            records_path.write_text("", encoding="utf-8")
        if diagnostics:
            with diagnostics_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(diagnostics[0].keys()))
                writer.writeheader()
                writer.writerows(diagnostics)
        return {"records_path": str(records_path), "diagnostics_path": str(diagnostics_path), "records": len(records)}

    def parse_jsonld_products(self, html: str, url: str, chain: str, category: str | None = None) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        records = []
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                data = json.loads(script.get_text(strip=True))
            except Exception:
                continue
            items = data if isinstance(data, list) else [data]
            for item in items:
                records.extend(self._jsonld_item_to_records(item, url, chain, category))
        return records

    def _jsonld_item_to_records(self, item: Any, url: str, chain: str, category: str | None) -> list[dict[str, Any]]:
        records = []
        if not isinstance(item, dict):
            return records
        graph = item.get("@graph")
        if isinstance(graph, list):
            for child in graph:
                records.extend(self._jsonld_item_to_records(child, url, chain, category))
        item_type = item.get("@type")
        if isinstance(item_type, list):
            is_product = "Product" in item_type
        else:
            is_product = item_type == "Product"
        if is_product:
            offers = item.get("offers") or {}
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            price = offers.get("price") if isinstance(offers, dict) else None
            record = normalize_price_record(
                {
                    "capture_date": datetime.now().date().isoformat(),
                    "source_id": self.config.source_id,
                    "chain": chain,
                    "branch_name": None,
                    "province": "San Juan",
                    "city": "San Juan",
                    "product_name_raw": item.get("name"),
                    "brand": item.get("brand", {}).get("name") if isinstance(item.get("brand"), dict) else item.get("brand"),
                    "category": category,
                    "price_list": price,
                    "url": item.get("url") or url,
                    "confidence_score": self.config.confidence_score,
                    "source_product_id": item.get("sku") or item.get("productID"),
                }
            )
            if record.get("product_name_raw") and record.get("price_list") is not None:
                records.append(record)
        return records

    def parse_visible_products(self, html: str, url: str, chain: str, category: str | None = None) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        records = []
        for card in soup.select("[class*='product'], [class*='Product'], article"):
            text = card.get_text(" ", strip=True)
            price = parse_visible_price(text)
            if price is None:
                continue
            title_node = card.select_one("[class*='productBrand'], [class*='name'], h2, h3, a")
            title = title_node.get_text(" ", strip=True) if title_node else text[:120]
            if len(title) < 3:
                continue
            records.append(
                normalize_price_record(
                    {
                        "capture_date": datetime.now().date().isoformat(),
                        "source_id": self.config.source_id,
                        "chain": chain,
                        "branch_name": None,
                        "province": "San Juan",
                        "city": "San Juan",
                        "product_name_raw": title,
                        "category": category,
                        "price_list": price,
                        "url": url,
                        "confidence_score": max(50, self.config.confidence_score - 10),
                    }
                )
            )
        seen = set()
        unique = []
        for record in records:
            key = (record["product_name_clean"], record["price_list"])
            if key not in seen:
                unique.append(record)
                seen.add(key)
        return unique

    def inspect_page(self, url: str, category: str | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        response = self.fetch(url)
        self.save_raw(f"{category or 'page'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html", response.text)
        records = self.parse_jsonld_products(response.text, response.url, self.config.name, category)
        if not records:
            records = self.parse_visible_products(response.text, response.url, self.config.name, category)
        soup = BeautifulSoup(response.text, "lxml")
        text = soup.get_text(" ", strip=True).lower()
        diagnostics = {
            "checked_at": datetime.now().isoformat(timespec="seconds"),
            "source_id": self.config.source_id,
            "url": url,
            "status_code": response.status_code,
            "final_url": response.url,
            "bytes": len(response.content),
            "title": soup.title.get_text(" ", strip=True) if soup.title else "",
            "records_found": len(records),
            "has_price_text": "$" in text or "precio" in text,
            "has_offer_text": "oferta" in text or "promo" in text,
            "requires_js_config": self.config.requires_js,
            "requires_location_config": self.config.requires_location,
            "note": "" if records else "No se detectaron productos con precio parseable en HTML estatico.",
        }
        return records, diagnostics


def run_static_probe(source_id: str, paths: list[str] | None = None) -> list[dict[str, Any]]:
    config = load_source_config(source_id)
    scraper = BaseScraper(config)
    targets = []
    for path in paths or [""]:
        url = path if path.startswith("http") else urljoin(config.base_url, path)
        targets.append((url, path.strip("/") or "home"))
    records: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for url, category in targets:
        try:
            page_records, page_diag = scraper.inspect_page(url, category=category)
            records.extend(page_records)
            diagnostics.append(page_diag)
        except Exception as exc:
            diagnostics.append(
                {
                    "checked_at": datetime.now().isoformat(timespec="seconds"),
                    "source_id": source_id,
                    "url": url,
                    "status_code": "",
                    "final_url": "",
                    "bytes": 0,
                    "title": "",
                    "records_found": 0,
                    "has_price_text": False,
                    "has_offer_text": False,
                    "requires_js_config": config.requires_js,
                    "requires_location_config": config.requires_location,
                    "note": f"{type(exc).__name__}: {exc}",
                }
            )
    scraper.save_processed(records, diagnostics)
    return records

from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from ..config import Settings
from .base import BaseSource


LOGGER = logging.getLogger("proyecto_super.sources.vea")
CATALOG_URL = "https://www.vea.com.ar/api/catalog_system/pub/products/search/almacen"
SOURCE_HOME = "https://www.vea.com.ar/"


class VeaSource(BaseSource):
    source_name = "vea"
    source_version = "1.0.0"

    def __init__(self, settings: Settings, session: requests.Session | None = None) -> None:
        self.settings = settings
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "ProyectoSuperSanJuan/1.0 (+responsible-public-price-audit)",
                "Accept": "application/json",
            }
        )

    @property
    def fixture_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "vea_catalog_page.json"

    def health_check(self) -> dict[str, Any]:
        if self.settings.source_mode == "fixture":
            return {"status": "available", "mode": "fixture", "fixture": self.fixture_path.exists()}
        try:
            response = self.session.get(SOURCE_HOME, timeout=self.settings.request_timeout_seconds)
            return {"status": "available" if response.ok else "degraded", "mode": "live", "http_status": response.status_code}
        except requests.RequestException as exc:
            return {"status": "unavailable", "mode": "live", "error": type(exc).__name__}

    def fetch_page(self, page: int, page_size: int) -> Any:
        if self.settings.source_mode == "fixture":
            if page > 0:
                return []
            return json.loads(self.fixture_path.read_text(encoding="utf-8"))
        start = page * page_size
        params = {"_from": start, "_to": start + page_size - 1}
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                response = self.session.get(CATALOG_URL, params=params, timeout=self.settings.request_timeout_seconds)
                response.raise_for_status()
                payload = response.json()
                if not self.validate_response(payload):
                    raise ValueError("La fuente no devolvio una lista JSON valida")
                if self.settings.request_delay_seconds:
                    time.sleep(self.settings.request_delay_seconds)
                return payload
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                LOGGER.warning("vea_fetch_retry attempt=%s error=%s", attempt, type(exc).__name__)
                if attempt < 3:
                    time.sleep(min(self.settings.request_delay_seconds * attempt, 10))
        assert last_error is not None
        raise last_error

    def fetch_catalog(self, max_products: int, max_pages: int) -> tuple[list[dict[str, Any]], list[str]]:
        limit = min(max_products, self.settings.max_products_per_run)
        pages = min(max_pages, self.settings.max_pages_per_run)
        page_size = min(50, limit)
        observations: list[dict[str, Any]] = []
        incidents: list[str] = []
        for page in range(pages):
            payload = self.fetch_page(page, page_size)
            if not payload:
                if page == 0:
                    incidents.append("respuesta_vacia")
                break
            for product in payload:
                row = self.normalize_product(product)
                if row:
                    observations.append(row)
                else:
                    incidents.append(f"producto_invalido_pagina_{page + 1}")
                if len(observations) >= limit:
                    break
            if len(observations) >= limit:
                break
        return observations, incidents

    def normalize_product(self, product: dict[str, Any]) -> dict[str, Any] | None:
        items = product.get("items") or []
        item = items[0] if items else {}
        sellers = item.get("sellers") or []
        seller = sellers[0] if sellers else {}
        offer = seller.get("commertialOffer") or {}
        try:
            price = float(offer.get("Price"))
        except (TypeError, ValueError):
            return None
        name = str(product.get("productName") or "").strip()
        if not name or price <= 0:
            return None
        try:
            list_price = float(offer.get("ListPrice"))
        except (TypeError, ValueError):
            list_price = price
        regular = list_price if price <= list_price <= price * 5 else price
        promo = price if price < regular else None
        categories = [str(value).strip("/") for value in product.get("categories") or [] if str(value).strip("/")]
        teasers = offer.get("Teasers") or []
        promo_text = " | ".join(str(t.get("name") or t.get("<Name>k__BackingField") or "").strip() for t in teasers)
        observed_at = datetime.now(timezone.utc).isoformat()
        raw_key = {
            "source": self.source_name,
            "sku": item.get("itemId") or product.get("productId"),
            "price": price,
            "observed_at": observed_at,
        }
        raw_hash = hashlib.sha256(json.dumps(raw_key, sort_keys=True).encode("utf-8")).hexdigest()
        return {
            "comercio": "Vea",
            "sucursal": "Online nacional",
            "localidad": "San Juan",
            "canal_precio": "ONLINE",
            "producto": name,
            "marca": str(product.get("brand") or "Sin marca").strip(),
            "categoria": categories[-1] if categories else "Sin categoria",
            "presentacion": _presentation_from_name(name),
            "sku": str(item.get("itemId") or product.get("productId") or ""),
            "ean": str(item.get("ean") or ""),
            "precio_regular": round(regular, 2),
            "precio_promocional": round(promo, 2) if promo is not None else None,
            "precio_efectivo": round(price, 2),
            "condicion_promocion": promo_text or None,
            "medio_pago": None,
            "stock_publicado": offer.get("AvailableQuantity"),
            "fecha_hora_extraccion": observed_at,
            "url_origen": product.get("link") or SOURCE_HOME,
            "archivo_origen": "vea_vtex_public_catalog",
            "extractor_version": self.source_version,
            "raw_hash": raw_hash,
        }

    def build_snapshot(self, products: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "source": self.source_name,
            "source_version": self.source_version,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "channel": "ONLINE",
            "products": products,
        }

    def validate_response(self, payload: Any) -> bool:
        return isinstance(payload, list) and all(isinstance(item, dict) for item in payload)


def _presentation_from_name(name: str) -> str:
    import re

    match = re.search(r"\b(\d+(?:[.,]\d+)?)\s*(kg|g|gr|ml|cc|l|lt|un|unidad(?:es)?)\b", name, re.IGNORECASE)
    return f"{match.group(1)} {match.group(2)}" if match else "1 un"

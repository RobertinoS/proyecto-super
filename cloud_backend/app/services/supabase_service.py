from __future__ import annotations

import json
from typing import Any

import requests

from ..config import Settings


class SupabaseService:
    def __init__(self, settings: Settings, session: requests.Session | None = None) -> None:
        self.settings = settings
        self.session = session or requests.Session()

    @property
    def configured(self) -> bool:
        return self.settings.supabase_configured

    def _headers(self, content_type: str = "application/json") -> dict[str, str]:
        key = self.settings.supabase_service_role_key
        return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": content_type, "Prefer": "return=minimal"}

    def save_scrape_run(self, record: dict[str, Any]) -> None:
        if not self.configured:
            return
        allowed = {
            "id", "execution_id", "source", "started_at", "finished_at", "status", "trigger_type",
            "products_read", "products_valid", "products_invalid", "incidents", "extractor_version", "error_summary",
        }
        payload = {key: value for key, value in record.items() if key in allowed}
        response = self.session.post(
            f"{self.settings.supabase_url}/rest/v1/scrape_runs?on_conflict=execution_id",
            headers={**self._headers(), "Prefer": "resolution=merge-duplicates,return=minimal"},
            json=payload,
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()

    def save_observations(self, run_id: str, rows: list[dict[str, Any]]) -> None:
        if not self.configured or not rows:
            return
        columns = {
            "comercio", "sucursal", "localidad", "canal_precio", "producto", "marca", "categoria", "presentacion",
            "sku", "ean", "precio_regular", "precio_promocional", "precio_efectivo", "condicion_promocion", "medio_pago",
            "stock_publicado", "url_origen", "raw_hash",
        }
        payload = [
            {
                **{key: value for key, value in row.items() if key in columns},
                "run_id": run_id,
                "observed_at": row.get("fecha_hora_extraccion"),
                "quality_status": "PENDING",
            }
            for row in rows
        ]
        response = self.session.post(
            f"{self.settings.supabase_url}/rest/v1/price_observations",
            headers=self._headers(),
            json=payload,
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()

    def upload_json(self, bucket: str, path: str, payload: Any) -> None:
        if not self.configured:
            return
        response = self.session.post(
            f"{self.settings.supabase_url}/storage/v1/object/{bucket}/{path}",
            headers={**self._headers("application/json"), "x-upsert": "false"},
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()

    def upload_bytes(self, bucket: str, path: str, content: bytes, content_type: str) -> None:
        if not self.configured:
            return
        response = self.session.post(
            f"{self.settings.supabase_url}/storage/v1/object/{bucket}/{path}",
            headers={**self._headers(content_type), "x-upsert": "false"},
            data=content,
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()

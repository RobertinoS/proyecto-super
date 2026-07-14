from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

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
            "trigger_context", "app_env", "products_read", "products_valid", "products_invalid", "incidents",
            "extractor_version", "error_summary", "updated_at",
        }
        payload = {key: value for key, value in record.items() if key in allowed}
        response = self.session.post(
            f"{self.settings.supabase_url}/rest/v1/scrape_runs?on_conflict=execution_id",
            headers={**self._headers(), "Prefer": "resolution=merge-duplicates,return=minimal"},
            json=payload,
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()

    def find_scrape_run(self, execution_id: str) -> dict[str, Any] | None:
        if not self.configured:
            return None
        encoded = quote(execution_id, safe="")
        response = self.session.get(
            f"{self.settings.supabase_url}/rest/v1/scrape_runs?execution_id=eq.{encoded}&select=*&limit=1",
            headers=self._headers(),
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        rows = response.json()
        return rows[0] if rows else None

    def find_scrape_run_by_id(self, run_id: str) -> dict[str, Any] | None:
        if not self.configured:
            return None
        response = self.session.get(
            f"{self.settings.supabase_url}/rest/v1/scrape_runs?id=eq.{quote(run_id, safe='')}&select=*&limit=1",
            headers=self._headers(),
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        rows = response.json()
        return rows[0] if rows else None

    def get_observations(self, run_id: str) -> list[dict[str, Any]]:
        if not self.configured:
            return []
        response = self.session.get(
            f"{self.settings.supabase_url}/rest/v1/price_observations?run_id=eq.{quote(run_id, safe='')}&select=*",
            headers=self._headers(),
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        observations = response.json()
        for row in observations:
            row["fecha_hora_extraccion"] = row.get("observed_at")
        return observations

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
            f"{self.settings.supabase_url}/rest/v1/price_observations?on_conflict=run_id,raw_hash",
            headers={**self._headers(), "Prefer": "resolution=ignore-duplicates,return=minimal"},
            json=payload,
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()

    def mark_observations_quality(self, run_id: str, quality_status: str) -> None:
        if not self.configured:
            return
        response = self.session.patch(
            f"{self.settings.supabase_url}/rest/v1/price_observations?run_id=eq.{quote(run_id, safe='')}",
            headers=self._headers(),
            json={"quality_status": quality_status},
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()

    def save_execution_event(
        self,
        execution_id: str,
        run_id: str | None,
        event_type: str,
        status: str,
        message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not self.configured:
            return
        response = self.session.post(
            f"{self.settings.supabase_url}/rest/v1/execution_events?on_conflict=execution_id,event_type,status",
            headers={**self._headers(), "Prefer": "resolution=ignore-duplicates,return=minimal"},
            json={
                "execution_id": execution_id,
                "run_id": run_id,
                "event_type": event_type,
                "status": status,
                "message": message,
                "metadata": metadata or {},
            },
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()

    def update_source_health(
        self,
        source: str,
        success: bool,
        extractor_version: str,
        error: str | None = None,
    ) -> None:
        if not self.configured:
            return
        payload: dict[str, Any] = {
            "source": source,
            "extractor_version": extractor_version,
            "last_result": "SUCCESS" if success else "FAILURE",
            "last_error": error,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if success:
            payload.update({"last_success_at": payload["updated_at"], "consecutive_failures": 0})
        else:
            payload.update({"last_failure_at": payload["updated_at"], "consecutive_failures": 1})
        response = self.session.post(
            f"{self.settings.supabase_url}/rest/v1/source_health?on_conflict=source",
            headers={**self._headers(), "Prefer": "resolution=merge-duplicates,return=minimal"},
            json=payload,
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()

    def save_publication_run(self, record: dict[str, Any]) -> None:
        if not self.configured:
            return
        allowed = {
            "scrape_run_id", "status", "approved_by", "approved_at", "published_at",
            "dataset_path", "rows_published", "notes",
        }
        payload = {key: value for key, value in record.items() if key in allowed}
        response = self.session.post(
            f"{self.settings.supabase_url}/rest/v1/publication_runs?on_conflict=scrape_run_id,status",
            headers={**self._headers(), "Prefer": "resolution=merge-duplicates,return=minimal"},
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
        if getattr(response, "status_code", None) != 409:
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
        if getattr(response, "status_code", None) != 409:
            response.raise_for_status()

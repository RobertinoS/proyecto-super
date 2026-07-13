from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from ..models import RunSummary, ScrapeJobRequest
from ..sources.base import BaseSource
from .supabase_service import SupabaseService


class RunService:
    def __init__(self, sources: dict[str, BaseSource], supabase: SupabaseService) -> None:
        self.sources = sources
        self.supabase = supabase
        self._runs: dict[str, dict[str, Any]] = {}
        self._execution_index: dict[str, str] = {}
        self._lock = threading.Lock()

    def execute(self, request: ScrapeJobRequest) -> RunSummary:
        if request.source not in self.sources:
            raise KeyError(f"Fuente no disponible: {request.source}")
        execution_id = request.execution_id or f"{request.trigger_type}-{uuid.uuid4()}"
        with self._lock:
            existing_id = self._execution_index.get(execution_id)
            if existing_id:
                summary = self._runs[existing_id]["summary"].model_copy()
                summary.duplicate_execution = True
                return summary
            run_id = str(uuid.uuid4())
            summary = RunSummary(
                run_id=run_id,
                execution_id=execution_id,
                source=request.source,
                status="RUNNING",
                started_at=datetime.now(timezone.utc),
            )
            self._runs[run_id] = {"summary": summary, "observations": [], "processed": [], "quality": None}
            self._execution_index[execution_id] = run_id
        try:
            if not request.dry_run and not self.supabase.configured:
                raise RuntimeError("Supabase no esta configurado; use dry_run o configure persistencia")
            observations, incidents = self.sources[request.source].fetch_catalog(request.max_products, request.max_pages)
            summary.products_read = len(observations)
            summary.products_valid = len(observations)
            summary.products_invalid = len(incidents)
            summary.incidents = len(incidents)
            summary.status = "SCRAPED" if observations else "EMPTY"
            summary.finished_at = datetime.now(timezone.utc)
            self._runs[run_id]["observations"] = observations
            self._runs[run_id]["incidents"] = incidents
            if not request.dry_run:
                source = self.sources[request.source]
                run_payload = {
                    **summary.model_dump(mode="json"),
                    "id": run_id,
                    "trigger_type": request.trigger_type,
                    "extractor_version": source.source_version,
                }
                self.supabase.save_scrape_run(run_payload)
                self.supabase.save_observations(run_id, observations)
                timestamp = summary.started_at.strftime("%Y%m%dT%H%M%SZ")
                date_path = summary.started_at.strftime("%Y/%m/%d")
                self.supabase.upload_json(
                    self.supabase.settings.raw_bucket,
                    f"{request.source}/{date_path}/{run_id}/{timestamp}.json",
                    source.build_snapshot(observations),
                )
        except Exception as exc:
            summary.status = "FAILED"
            summary.error_summary = f"{type(exc).__name__}: {exc}"
            summary.finished_at = datetime.now(timezone.utc)
            if not request.dry_run and self.supabase.configured:
                try:
                    self.supabase.save_scrape_run(
                        {
                            **summary.model_dump(mode="json"),
                            "id": run_id,
                            "trigger_type": request.trigger_type,
                            "extractor_version": self.sources[request.source].source_version,
                        }
                    )
                except Exception:
                    pass
        if summary.finished_at is None:
            summary.finished_at = datetime.now(timezone.utc)
        return summary

    def get(self, run_id: str) -> dict[str, Any] | None:
        return self._runs.get(run_id)

    def last_for_source(self, source: str) -> RunSummary | None:
        candidates = [row["summary"] for row in self._runs.values() if row["summary"].source == source]
        return max(candidates, key=lambda item: item.started_at) if candidates else None

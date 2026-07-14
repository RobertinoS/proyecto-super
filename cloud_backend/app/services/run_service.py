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

        existing = self._find_existing_execution(execution_id)
        if existing:
            existing.duplicate_execution = True
            return existing

        # A deterministic UUID keeps retries on different Render instances on the
        # same database identity. Supabase still enforces execution_id uniqueness.
        run_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"proyecto-super:{execution_id}"))
        with self._lock:
            existing_id = self._execution_index.get(execution_id)
            if existing_id:
                summary = self._runs[existing_id]["summary"].model_copy()
                summary.duplicate_execution = True
                return summary
            summary = RunSummary(
                run_id=run_id,
                execution_id=execution_id,
                source=request.source,
                status="RUNNING",
                started_at=datetime.now(timezone.utc),
            )
            self._runs[run_id] = {"summary": summary, "observations": [], "processed": [], "quality": None}
            self._execution_index[execution_id] = run_id

        source = self.sources[request.source]
        persist = self.supabase.configured
        db_trigger_type = "manual" if request.trigger_type == "manual_staging" else request.trigger_type
        self._runs[run_id]["run_meta"] = {
            "trigger_type": db_trigger_type,
            "trigger_context": request.trigger_type,
            "extractor_version": source.source_version,
        }
        try:
            if self.supabase.settings.app_env == "staging" and not persist:
                raise RuntimeError("Supabase staging no esta configurado; la ejecucion durable queda bloqueada")
            if not request.dry_run and not persist:
                raise RuntimeError("Supabase no esta configurado; use dry_run o configure persistencia")

            if persist:
                self.supabase.save_scrape_run(
                    self._run_payload(summary, db_trigger_type, request.trigger_type, source.source_version)
                )
                self.supabase.save_execution_event(
                    execution_id,
                    run_id,
                    "SCRAPE_STARTED",
                    "RUNNING",
                    metadata={"source": request.source, "dry_run": request.dry_run},
                )

            observations, incidents = source.fetch_catalog(request.max_products, request.max_pages)
            summary.products_read = len(observations)
            summary.products_valid = len(observations)
            summary.products_invalid = len(incidents)
            summary.incidents = len(incidents)
            summary.status = "SCRAPED" if observations else "EMPTY"
            summary.finished_at = datetime.now(timezone.utc)
            self._runs[run_id]["observations"] = observations
            self._runs[run_id]["incidents"] = incidents

            if persist:
                self.supabase.save_scrape_run(
                    self._run_payload(summary, db_trigger_type, request.trigger_type, source.source_version)
                )
                self.supabase.save_observations(run_id, observations)
                timestamp = summary.started_at.strftime("%Y%m%dT%H%M%SZ")
                date_path = summary.started_at.strftime("%Y/%m/%d")
                self.supabase.upload_json(
                    self.supabase.settings.raw_bucket,
                    f"{request.source}/{date_path}/{run_id}/{timestamp}.json",
                    source.build_snapshot(observations),
                )
                self.supabase.update_source_health(request.source, bool(observations), source.source_version)
                self.supabase.save_execution_event(
                    execution_id,
                    run_id,
                    "SCRAPE_COMPLETED",
                    summary.status,
                    metadata={"products": len(observations), "incidents": len(incidents)},
                )
        except Exception as exc:
            summary.status = "FAILED"
            summary.error_summary = f"{type(exc).__name__}: {exc}"
            summary.finished_at = datetime.now(timezone.utc)
            if persist:
                try:
                    self.supabase.save_scrape_run(
                        self._run_payload(summary, db_trigger_type, request.trigger_type, source.source_version)
                    )
                    self.supabase.update_source_health(request.source, False, source.source_version, summary.error_summary)
                    self.supabase.save_execution_event(
                        execution_id,
                        run_id,
                        "SCRAPE_FAILED",
                        "FAILED",
                        message=summary.error_summary,
                    )
                except Exception:
                    pass
        if summary.finished_at is None:
            summary.finished_at = datetime.now(timezone.utc)
        return summary

    def get(self, run_id: str) -> dict[str, Any] | None:
        local = self._runs.get(run_id)
        if local:
            return local
        if not self.supabase.configured:
            return None
        remote = self.supabase.find_scrape_run_by_id(run_id)
        return self._hydrate_remote(remote) if remote else None

    def last_for_source(self, source: str) -> RunSummary | None:
        candidates = [row["summary"] for row in self._runs.values() if row["summary"].source == source]
        return max(candidates, key=lambda item: item.started_at) if candidates else None

    def persist_summary(self, run_id: str) -> None:
        record = self.get(run_id)
        if not record or not self.supabase.configured:
            return
        meta = record.get("run_meta") or {}
        source = record["summary"].source
        self.supabase.save_scrape_run(
            self._run_payload(
                record["summary"],
                meta.get("trigger_type", "manual"),
                meta.get("trigger_context", "manual"),
                meta.get("extractor_version", self.sources[source].source_version),
            )
        )

    def _find_existing_execution(self, execution_id: str) -> RunSummary | None:
        with self._lock:
            existing_id = self._execution_index.get(execution_id)
            if existing_id:
                return self._runs[existing_id]["summary"].model_copy()
        if not self.supabase.configured:
            return None
        remote = self.supabase.find_scrape_run(execution_id)
        if not remote:
            return None
        record = self._hydrate_remote(remote)
        return record["summary"].model_copy()

    def _hydrate_remote(self, remote: dict[str, Any]) -> dict[str, Any]:
        payload = {**remote, "run_id": remote.get("run_id") or remote.get("id")}
        summary = RunSummary.model_validate(payload)
        observations = self.supabase.get_observations(summary.run_id)
        record = {
            "summary": summary,
            "observations": observations,
            "processed": [],
            "quality": None,
            "incidents": [],
            "run_meta": {
                "trigger_type": remote.get("trigger_type", "manual"),
                "trigger_context": remote.get("trigger_context", remote.get("trigger_type", "manual")),
                "extractor_version": remote.get("extractor_version", "unknown"),
            },
        }
        with self._lock:
            self._runs[summary.run_id] = record
            self._execution_index[summary.execution_id] = summary.run_id
        return record

    def _run_payload(
        self,
        summary: RunSummary,
        trigger_type: str,
        trigger_context: str,
        extractor_version: str,
    ) -> dict[str, Any]:
        return {
            **summary.model_dump(mode="json"),
            "id": summary.run_id,
            "trigger_type": trigger_type,
            "trigger_context": trigger_context,
            "app_env": self.supabase.settings.app_env,
            "extractor_version": extractor_version,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

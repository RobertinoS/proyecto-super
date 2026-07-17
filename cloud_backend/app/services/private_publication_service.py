from __future__ import annotations

import csv
import hashlib
import io
import json
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from ..config import Settings
from .review_service import ReviewError, ReviewService
from .run_service import RunService
from .supabase_service import SupabaseService


class PrivatePublicationError(RuntimeError):
    pass


class PrivatePublicationService:
    """Creates approved CSV datasets only behind the separate private gate."""

    def __init__(self, settings: Settings, runs: RunService, reviews: ReviewService, supabase: SupabaseService) -> None:
        self.settings = settings
        self.runs = runs
        self.reviews = reviews
        self.supabase = supabase
        self._datasets: dict[str, dict[str, Any]] = {}
        self._by_run: dict[str, str] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _csv_bytes(rows: list[dict[str, Any]]) -> bytes:
        fieldnames = list(rows[0]) if rows else []
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        return buffer.getvalue().encode("utf-8")

    def _rows_for_run(self, run_id: str) -> list[dict[str, Any]]:
        record = self.runs.get(run_id)
        if not record:
            raise KeyError(run_id)
        rows = record.get("processed") or []
        if not rows:
            rows = [
                {**row, "precio": row.get("precio_efectivo"), "quality_status": row.get("quality_status", "OK")}
                for row in record.get("observations", [])
                if row.get("quality_status", "OK") != "INVALIDO"
            ]
        if not rows:
            raise PrivatePublicationError("No hay filas aprobables para generar el dataset privado")
        return rows

    def publish(self, run_id: str, actor: str, dry_run: bool = True) -> dict[str, Any]:
        record = self.runs.get(run_id)
        if not record:
            raise KeyError(run_id)
        approval = self.reviews.approval_status(run_id)
        if not approval or approval.get("status") != "APPROVED":
            raise PrivatePublicationError("La publicacion privada requiere un dataset aprobado")
        rows = self._rows_for_run(run_id)
        csv_content = self._csv_bytes(rows)
        checksum = hashlib.sha256(csv_content).hexdigest()
        date_path = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        dataset_path = f"published/{date_path}/{run_id}/precios_aprobados.csv"
        manifest_path = f"published/{date_path}/{run_id}/manifiesto.json"
        dataset_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"proyecto-super:{approval['id']}:{checksum}"))
        manifest = {
            "dataset_id": dataset_id,
            "run_id": run_id,
            "approval_id": approval["id"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "rows": len(rows),
            "checksum_sha256": checksum,
            "approved_by": approval.get("approved_by") or actor,
            "extractor_version": (record.get("run_meta") or {}).get("extractor_version", "unknown"),
            "quality_score": approval.get("quality_score"),
            "bucket": self.settings.published_bucket,
            "visibility": "private",
        }
        actual_publication = self.settings.enable_private_publication and not dry_run
        status = "PRIVATE_PUBLISHED" if actual_publication else "PRIVATE_DRY_RUN"
        dataset = {
            "id": dataset_id,
            "run_id": run_id,
            "approval_id": approval["id"],
            "status": status,
            "dataset_path": dataset_path,
            "manifest_path": manifest_path,
            "rows": len(rows),
            "checksum_sha256": checksum,
            "created_at": manifest["created_at"],
            "approved_by": manifest["approved_by"],
            "quality_score": manifest["quality_score"],
            "private": True,
            "dry_run": not actual_publication,
        }
        with self._lock:
            existing_id = self._by_run.get(run_id)
            if existing_id and self._datasets[existing_id]["checksum_sha256"] == checksum:
                return dict(self._datasets[existing_id])
            self._datasets[dataset_id] = dataset
            self._by_run[run_id] = dataset_id
        if actual_publication:
            if not self.supabase.configured:
                raise PrivatePublicationError("Supabase no esta configurado para publicar en el bucket privado")
            self.supabase.upload_bytes(self.settings.published_bucket, dataset_path, csv_content, "text/csv")
            self.supabase.upload_json(self.settings.published_bucket, manifest_path, manifest)
        self.supabase.save_private_dataset(
            {
                "id": dataset_id,
                "scrape_run_id": run_id,
                "approval_id": approval["id"],
                "status": status,
                "dataset_path": dataset_path,
                "manifest_path": manifest_path,
                "row_count": len(rows),
                "checksum_sha256": checksum,
                "approved_by": manifest["approved_by"],
                "quality_score": manifest["quality_score"],
                "created_at": manifest["created_at"],
            }
        )
        self.supabase.save_publication_run(
            {
                "scrape_run_id": run_id,
                "status": "PUBLISHED" if actual_publication else "DRY_RUN",
                "approved_by": manifest["approved_by"],
                "approved_at": approval.get("approved_at"),
                "published_at": manifest["created_at"] if actual_publication else None,
                "dataset_path": dataset_path,
                "rows_published": len(rows),
                "notes": "Private publication only; no public URL is created.",
            }
        )
        self.supabase.save_execution_event(
            record["summary"].execution_id,
            run_id,
            "PRIVATE_PUBLICATION",
            status,
            metadata={"rows": len(rows), "checksum_sha256": checksum, "enabled": self.settings.enable_private_publication},
        )
        return dict(dataset)

    def latest(self) -> dict[str, Any] | None:
        with self._lock:
            datasets = list(self._datasets.values())
        approved = [item for item in datasets if item["status"] == "PRIVATE_PUBLISHED"]
        candidates = approved or datasets
        if candidates:
            return dict(max(candidates, key=lambda item: item["created_at"]))
        return self.supabase.get_latest_private_dataset() if self.supabase.configured else None

    def get(self, dataset_id: str) -> dict[str, Any] | None:
        with self._lock:
            dataset = self._datasets.get(dataset_id)
            if dataset:
                return dict(dataset)
        return self.supabase.get_private_dataset(dataset_id) if self.supabase.configured else None

    def download_url(self, dataset_id: str) -> dict[str, Any]:
        dataset = self.get(dataset_id)
        if not dataset:
            raise KeyError(dataset_id)
        if dataset["status"] != "PRIVATE_PUBLISHED" or not self.settings.enable_private_publication:
            raise PrivatePublicationError("El dataset privado no esta disponible para descarga")
        url = self.supabase.create_signed_download_url(self.settings.published_bucket, dataset["dataset_path"])
        if not url:
            raise PrivatePublicationError("No se pudo generar una URL firmada para el dataset privado")
        return {"dataset_id": dataset_id, "download_url": url, "expires_in_seconds": 300}

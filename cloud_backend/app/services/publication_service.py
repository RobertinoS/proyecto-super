from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from ..config import Settings
from ..models import PublishResponse
from .run_service import RunService
from .supabase_service import SupabaseService


class PublicationError(RuntimeError):
    pass


class PublicationService:
    def __init__(self, settings: Settings, runs: RunService, supabase: SupabaseService) -> None:
        self.settings = settings
        self.runs = runs
        self.supabase = supabase

    def publish(self, run_id: str, approved: bool, approved_by: str | None, dry_run: bool) -> PublishResponse:
        record = self.runs.get(run_id)
        if not record:
            raise KeyError(run_id)
        if not approved or not approved_by:
            self.supabase.save_execution_event(
                record["summary"].execution_id,
                run_id,
                "PUBLICATION_BLOCKED",
                "REJECTED",
                message="approval_required",
            )
            raise PublicationError("La publicacion requiere aprobacion explicita e identidad del aprobador")
        if not record.get("quality") or record["quality"]["status"] != "READY_FOR_APPROVAL":
            raise PublicationError("El dataset no supero el control de calidad")
        rows = record.get("processed") or []
        if not rows:
            raise PublicationError("No hay filas procesadas para publicar")
        date_path = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        dataset_path = f"published/{date_path}/{run_id}/precios_publicados.csv"
        if dry_run or not self.settings.enable_publication:
            self.supabase.save_publication_run(
                {
                    "scrape_run_id": run_id,
                    "status": "DRY_RUN",
                    "approved_by": approved_by,
                    "approved_at": datetime.now(timezone.utc).isoformat(),
                    "dataset_path": dataset_path,
                    "rows_published": len(rows),
                    "notes": "Publication disabled by dry_run or ENABLE_PUBLICATION=false",
                }
            )
            self.supabase.save_execution_event(
                record["summary"].execution_id,
                run_id,
                "PUBLICATION_BLOCKED",
                "DRY_RUN",
                metadata={"rows": len(rows), "enable_publication": self.settings.enable_publication},
            )
            return PublishResponse(run_id=run_id, status="DRY_RUN", dataset_path=dataset_path, rows_published=len(rows), dry_run=True)
        if not self.supabase.configured:
            raise PublicationError("Supabase no esta configurado")
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        self.supabase.upload_bytes(self.settings.published_bucket, dataset_path, buffer.getvalue().encode("utf-8"), "text/csv")
        record["summary"].status = "PUBLISHED"
        self.runs.persist_summary(run_id)
        self.supabase.save_publication_run(
            {
                "scrape_run_id": run_id,
                "status": "PUBLISHED",
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "published_at": datetime.now(timezone.utc).isoformat(),
                "dataset_path": dataset_path,
                "rows_published": len(rows),
            }
        )
        return PublishResponse(run_id=run_id, status="PUBLISHED", dataset_path=dataset_path, rows_published=len(rows), dry_run=False)

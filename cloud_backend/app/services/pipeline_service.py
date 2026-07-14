from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Any

from ..models import ProcessResponse
from .run_service import RunService


class PipelineService:
    def __init__(self, runs: RunService) -> None:
        self.runs = runs

    def process(self, run_id: str, max_invalid_pct: float, dry_run: bool = True) -> ProcessResponse:
        record = self.runs.get(run_id)
        if not record:
            raise KeyError(run_id)
        if record.get("quality") and record["quality"].get("response"):
            return ProcessResponse.model_validate(record["quality"]["response"])
        rows = record["observations"]
        processed: list[dict[str, Any]] = []
        incidents: list[str] = list(record.get("incidents") or [])
        seen_hashes: set[str] = set()
        for row in rows:
            price = row.get("precio_efectivo") or row.get("precio_regular")
            raw_hash = str(row.get("raw_hash") or "")
            if not row.get("producto") or not isinstance(price, (int, float)) or price <= 0:
                incidents.append("observacion_invalida")
                continue
            if not raw_hash or raw_hash in seen_hashes:
                incidents.append("raw_hash_duplicado_o_ausente")
                continue
            seen_hashes.add(raw_hash)
            processed.append(
                {
                    **row,
                    "precio": price,
                    "fecha_relevamiento": str(row.get("fecha_hora_extraccion", ""))[:10],
                    "fuente": f"oficial:{record['summary'].source}",
                    "quality_status": "OK",
                }
            )
        invalid = max(0, len(rows) - len(processed)) + len(record.get("incidents") or [])
        denominator = max(1, len(rows) + len(record.get("incidents") or []))
        invalid_pct = invalid * 100 / denominator
        score = round(max(0.0, 100.0 - invalid_pct), 2)
        status = "READY_FOR_APPROVAL" if processed and invalid_pct <= max_invalid_pct else "QUALITY_REJECTED"
        record["processed"] = processed
        record["summary"].status = status
        response = ProcessResponse(
            run_id=run_id,
            status=status,
            rows_processed=len(processed),
            rows_invalid=invalid,
            quality_score=score,
            incidents=incidents,
        )
        record["quality"] = {
            "status": status,
            "score": score,
            "invalid": invalid,
            "incidents": incidents,
            "response": response.model_dump(mode="json"),
        }
        if not dry_run and not self.runs.supabase.configured:
            raise RuntimeError("Supabase no esta configurado para persistir el dataset procesado")
        if self.runs.supabase.configured:
            self.runs.persist_summary(run_id)
            self.runs.supabase.mark_observations_quality(run_id, "OK" if status == "READY_FOR_APPROVAL" else "INVALIDO")
            self.runs.supabase.save_execution_event(
                record["summary"].execution_id,
                run_id,
                "PIPELINE_PROCESSED",
                status,
                metadata={"rows_processed": len(processed), "rows_invalid": invalid, "quality_score": score},
            )
            if processed:
                buffer = io.StringIO()
                writer = csv.DictWriter(buffer, fieldnames=list(processed[0]))
                writer.writeheader()
                writer.writerows(processed)
                date_path = record["summary"].started_at.astimezone(timezone.utc).strftime("%Y/%m/%d")
                path = f"processed/{date_path}/{run_id}/precios_procesados.csv"
                self.runs.supabase.upload_bytes(
                    self.runs.supabase.settings.processed_bucket,
                    path,
                    buffer.getvalue().encode("utf-8"),
                    "text/csv",
                )
        return response

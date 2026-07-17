from __future__ import annotations

import hashlib
import json
import threading
import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from .run_service import RunService
from .supabase_service import SupabaseService


ACTIVE_REVIEW_STATUSES = {"PENDING", "IN_REVIEW"}
CRITICAL_SEVERITY = "CRITICAL"
REVIEW_ACTIONS = {
    "approve": ("APPROVED", "APPROVE"),
    "reject": ("REJECTED", "REJECT"),
    "correct": ("CORRECTED", "CORRECT"),
    "dismiss": ("DISMISSED", "DISMISS"),
}


class ReviewError(RuntimeError):
    pass


class ReviewService:
    """Human-review workflow with an in-memory safe fallback for local tests.

    The fallback deliberately never persists outside the process. In staging the
    same records are written through SupabaseService using the service role.
    """

    def __init__(self, runs: RunService, supabase: SupabaseService) -> None:
        self.runs = runs
        self.supabase = supabase
        self._reviews: dict[str, dict[str, Any]] = {}
        self._decisions_by_key: dict[str, dict[str, Any]] = {}
        self._approvals: dict[str, dict[str, Any]] = {}
        self._alerts: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _key(prefix: str, payload: dict[str, Any]) -> str:
        compact = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
        return f"{prefix}-{hashlib.sha256(compact.encode('utf-8')).hexdigest()[:32]}"

    @staticmethod
    def _source_for(record: dict[str, Any]) -> str:
        return str(record["summary"].source)

    @staticmethod
    def _as_datetime(value: Any) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc)
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            return None

    def _review_payload(self, review: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in review.items() if key != "source"}

    def create_review(
        self,
        run_id: str,
        review_type: str,
        severity: str,
        reason: str,
        detected_value: dict[str, Any] | None = None,
        suggested_action: str | None = None,
        observation_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        record = self.runs.get(run_id)
        if not record:
            raise KeyError(run_id)
        identity = {
            "run_id": run_id,
            "review_type": review_type,
            "reason": reason,
            "observation_id": observation_id,
        }
        key = idempotency_key or self._key("review", identity)
        with self._lock:
            for review in self._reviews.values():
                if review["idempotency_key"] == key:
                    return dict(review)
            review_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"proyecto-super:{key}"))
            now = self._now()
            review = {
                "id": review_id,
                "scrape_run_id": run_id,
                "observation_id": observation_id,
                "source": self._source_for(record),
                "review_type": review_type,
                "severity": severity,
                "status": "PENDING",
                "reason": reason,
                "detected_value": detected_value or {},
                "suggested_action": suggested_action,
                "assigned_to": None,
                "reviewed_by": None,
                "reviewed_at": None,
                "decision": None,
                "decision_notes": {},
                "idempotency_key": key,
                "created_at": now,
                "updated_at": now,
            }
            self._reviews[review_id] = review
        self.supabase.save_review(self._review_payload(review))
        return dict(review)

    def ensure_quality_reviews(self, run_id: str) -> list[dict[str, Any]]:
        record = self.runs.get(run_id)
        if not record:
            raise KeyError(run_id)
        quality = record.get("quality") or {}
        incidents = list(quality.get("incidents") or record.get("incidents") or [])
        generated: list[dict[str, Any]] = []
        if record["summary"].status == "FAILED":
            generated.append(
                self.create_review(
                    run_id,
                    "SOURCE_FAILURE",
                    "CRITICAL",
                    "source_execution_failed",
                    {"error": record["summary"].error_summary or "unknown"},
                    "Corregir la fuente antes de solicitar aprobacion.",
                )
            )
        for incident in sorted(set(str(item) for item in incidents)):
            if "duplic" in incident:
                review_type, severity = "DUPLICATE", "HIGH"
            elif "invalida" in incident or "missing" in incident:
                review_type, severity = "MISSING_FIELD", "HIGH"
            elif "sospech" in incident or "outlier" in incident:
                review_type, severity = "PRICE_SUSPICIOUS", "HIGH"
            else:
                review_type, severity = "QUALITY_WARNING", "MEDIUM"
            generated.append(
                self.create_review(
                    run_id,
                    review_type,
                    severity,
                    incident,
                    {"quality_status": quality.get("status"), "quality_score": quality.get("score")},
                    "Revisar la incidencia antes de aprobar el dataset.",
                )
            )
        if quality.get("status") == "QUALITY_REJECTED":
            generated.append(
                self.create_review(
                    run_id,
                    "QUALITY_WARNING",
                    "CRITICAL",
                    "quality_threshold_not_met",
                    {"quality_score": quality.get("score"), "incidents": incidents},
                    "Corregir la calidad y reprocesar antes de publicar.",
                )
            )
            self.create_alert(
                source=self._source_for(record),
                run_id=run_id,
                alert_type="QUALITY_REJECTED",
                severity="CRITICAL",
                message="El procesamiento no alcanzo el umbral de calidad.",
            )
        return generated

    def list_reviews(
        self,
        status: str | None = None,
        severity: str | None = None,
        source: str | None = None,
        run_id: str | None = None,
        review_type: str | None = None,
    ) -> list[dict[str, Any]]:
        filters = {
            key: value
            for key, value in {
                "status": status,
                "severity": severity,
                "source": source,
                "scrape_run_id": run_id,
                "review_type": review_type,
            }.items()
            if value
        }
        if self.supabase.configured:
            rows = self.supabase.list_reviews(filters)
            if rows:
                return rows
        with self._lock:
            rows = list(self._reviews.values())
        for key, value in filters.items():
            rows = [row for row in rows if str(row.get(key, "")) == value]
        return sorted((dict(row) for row in rows), key=lambda row: (row["created_at"], row["id"]), reverse=True)

    def get_review(self, review_id: str) -> dict[str, Any] | None:
        if self.supabase.configured:
            remote = self.supabase.get_review(review_id)
            if remote:
                return remote
        with self._lock:
            review = self._reviews.get(review_id)
            return dict(review) if review else None

    def decide_review(
        self,
        review_id: str,
        action: str,
        actor: str,
        notes: str | None = None,
        corrected_value: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if action not in REVIEW_ACTIONS:
            raise ReviewError("Accion de revision no soportada")
        if action == "correct" and not corrected_value:
            raise ReviewError("La correccion requiere un valor corregido")
        review = self.get_review(review_id)
        if not review:
            raise KeyError(review_id)
        target_status, audit_action = REVIEW_ACTIONS[action]
        key = idempotency_key or self._key(
            "review-decision",
            {"review_id": review_id, "action": audit_action, "actor": actor, "corrected_value": corrected_value},
        )
        with self._lock:
            existing = self._decisions_by_key.get(key)
            if existing:
                return self.get_review(review_id) or review
            if review["status"] == target_status:
                return review
            previous_value = dict(review.get("detected_value") or {})
            now = self._now()
            review.update(
                {
                    "status": target_status,
                    "reviewed_by": actor,
                    "reviewed_at": now,
                    "decision": audit_action,
                    "decision_notes": {
                        "notes": notes or "",
                        "previous_value": previous_value,
                        "corrected_value": corrected_value or {},
                    },
                    "updated_at": now,
                }
            )
            decision = {
                "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"proyecto-super:{key}")),
                "review_id": review_id,
                "action": audit_action,
                "actor": actor,
                "notes": notes,
                "previous_value": previous_value,
                "corrected_value": corrected_value,
                "idempotency_key": key,
                "created_at": now,
            }
            self._decisions_by_key[key] = decision
            self._reviews[review_id] = review
        self.supabase.update_review(review_id, self._review_payload(review))
        self.supabase.save_review_decision(decision)
        record = self.runs.get(review["scrape_run_id"])
        if record:
            self.supabase.save_execution_event(
                record["summary"].execution_id,
                review["scrape_run_id"],
                "REVIEW_DECISION",
                target_status,
                metadata={"review_id": review_id, "action": audit_action, "actor": actor},
            )
        return dict(review)

    def request_approval(self, run_id: str, actor: str, idempotency_key: str | None = None) -> dict[str, Any]:
        record = self.runs.get(run_id)
        if not record:
            raise KeyError(run_id)
        self.ensure_quality_reviews(run_id)
        reviews = self.list_reviews(run_id=run_id)
        counters = Counter(row["status"] for row in reviews)
        pending = sum(counters[state] for state in ACTIVE_REVIEW_STATUSES)
        critical_pending = any(row["severity"] == CRITICAL_SEVERITY and row["status"] in ACTIVE_REVIEW_STATUSES for row in reviews)
        quality = record.get("quality") or {}
        ready = quality.get("status") == "READY_FOR_APPROVAL" and not critical_pending and pending == 0
        desired_status = "READY_FOR_APPROVAL" if ready else "PENDING_REVIEW"
        key = idempotency_key or self._key("dataset-approval", {"run_id": run_id})
        with self._lock:
            approval = self._approvals.get(run_id)
            if approval and approval["status"] in {"APPROVED", "REJECTED"}:
                return dict(approval)
            now = self._now()
            approval = approval or {
                "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"proyecto-super:{key}")),
                "scrape_run_id": run_id,
                "requested_at": now,
                "requested_by": actor,
                "created_at": now,
                "idempotency_key": key,
            }
            approval.update(
                {
                    "status": desired_status,
                    "quality_score": quality.get("score", 0.0),
                    "pending_items": pending,
                    "approved_items": counters["APPROVED"] + counters["CORRECTED"] + counters["DISMISSED"],
                    "rejected_items": counters["REJECTED"],
                    "updated_at": now,
                }
            )
            self._approvals[run_id] = approval
        self.supabase.save_dataset_approval(approval)
        self.supabase.save_execution_event(
            record["summary"].execution_id,
            run_id,
            "DATASET_APPROVAL_REQUESTED",
            desired_status,
            metadata={"pending_items": pending, "quality_score": quality.get("score", 0.0)},
        )
        return dict(approval)

    def approval_status(self, run_id: str) -> dict[str, Any] | None:
        if self.supabase.configured:
            remote = self.supabase.get_dataset_approval(run_id)
            if remote:
                return remote
        with self._lock:
            approval = self._approvals.get(run_id)
            return dict(approval) if approval else None

    def approve_dataset(self, run_id: str, actor: str, idempotency_key: str | None = None) -> dict[str, Any]:
        approval = self.request_approval(run_id, actor, idempotency_key)
        if approval["status"] == "APPROVED":
            return approval
        if approval["status"] != "READY_FOR_APPROVAL":
            raise ReviewError("No se puede aprobar: existen incidencias pendientes o criticas")
        now = self._now()
        approval.update({"status": "APPROVED", "approved_by": actor, "approved_at": now, "updated_at": now})
        with self._lock:
            self._approvals[run_id] = approval
        self.supabase.save_dataset_approval(approval)
        record = self.runs.get(run_id)
        if record:
            self.supabase.save_execution_event(record["summary"].execution_id, run_id, "DATASET_APPROVED", "APPROVED", metadata={"actor": actor})
        return dict(approval)

    def reject_dataset(self, run_id: str, actor: str, reason: str, idempotency_key: str | None = None) -> dict[str, Any]:
        if not reason or not reason.strip():
            raise ReviewError("El rechazo del dataset requiere un motivo")
        approval = self.request_approval(run_id, actor, idempotency_key)
        if approval["status"] == "REJECTED":
            return approval
        now = self._now()
        approval.update(
            {
                "status": "REJECTED",
                "rejected_by": actor,
                "rejected_at": now,
                "rejection_reason": reason.strip(),
                "updated_at": now,
            }
        )
        with self._lock:
            self._approvals[run_id] = approval
        self.supabase.save_dataset_approval(approval)
        record = self.runs.get(run_id)
        if record:
            self.supabase.save_execution_event(record["summary"].execution_id, run_id, "DATASET_REJECTED", "REJECTED", message=reason.strip())
        return dict(approval)

    def create_alert(
        self,
        source: str | None,
        run_id: str | None,
        alert_type: str,
        severity: str,
        message: str,
        metadata: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        key = idempotency_key or self._key("alert", {"source": source, "run_id": run_id, "type": alert_type, "message": message})
        with self._lock:
            for alert in self._alerts.values():
                if alert["idempotency_key"] == key:
                    return dict(alert)
            alert = {
                "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"proyecto-super:{key}")),
                "source": source,
                "run_id": run_id,
                "alert_type": alert_type,
                "severity": severity,
                "status": "OPEN",
                "message": message,
                "metadata": metadata or {},
                "acknowledged_by": None,
                "acknowledged_at": None,
                "idempotency_key": key,
                "created_at": self._now(),
            }
            self._alerts[alert["id"]] = alert
        self.supabase.save_operational_alert(alert)
        return dict(alert)

    def list_alerts(self) -> list[dict[str, Any]]:
        if self.supabase.configured:
            rows = self.supabase.list_operational_alerts()
            if rows:
                return rows
        with self._lock:
            return sorted((dict(row) for row in self._alerts.values()), key=lambda row: row["created_at"], reverse=True)

    def acknowledge_alert(self, alert_id: str, actor: str) -> dict[str, Any]:
        with self._lock:
            alert = self._alerts.get(alert_id)
            if not alert:
                raise KeyError(alert_id)
            if alert["status"] == "ACKNOWLEDGED":
                return dict(alert)
            alert.update({"status": "ACKNOWLEDGED", "acknowledged_by": actor, "acknowledged_at": self._now()})
        self.supabase.update_operational_alert(alert_id, alert)
        return dict(alert)

    def operations_summary(self) -> dict[str, Any]:
        with self._lock:
            runs = [dict(row["summary"].model_dump(mode="json")) for row in self.runs._runs.values()]
        if self.supabase.configured:
            remote_runs = self.supabase.list_recent_scrape_runs()
            if remote_runs:
                runs = remote_runs
        reviews = self.list_reviews()
        alerts = self.list_alerts()
        now = datetime.now(timezone.utc)
        recent = [row for row in runs if (started := self._as_datetime(row.get("started_at"))) and (now - started).total_seconds() <= 86400]
        latest = max(runs, key=lambda row: self._as_datetime(row.get("finished_at") or row.get("started_at")) or datetime.min.replace(tzinfo=timezone.utc), default=None)
        approved = [item for item in self._approvals.values() if item.get("status") == "APPROVED"]
        if self.supabase.configured:
            remote_approved = self.supabase.list_dataset_approvals("APPROVED")
            if remote_approved:
                approved = remote_approved
        latest_time = self._as_datetime((latest or {}).get("finished_at") or (latest or {}).get("started_at"))
        return {
            "executions_last_24h": len(recent),
            "successes_last_24h": sum(row["status"] in {"SCRAPED", "READY_FOR_APPROVAL", "PUBLISHED"} for row in recent),
            "failures_last_24h": sum(row["status"] == "FAILED" for row in recent),
            "degraded_sources": len([alert for alert in alerts if alert["status"] == "OPEN" and alert["severity"] in {"HIGH", "CRITICAL"}]),
            "pending_reviews": sum(row["status"] in ACTIVE_REVIEW_STATUSES for row in reviews),
            "approved_datasets": len(approved),
            "last_update": latest_time.isoformat() if latest_time else None,
            "data_age_seconds": round((now - latest_time).total_seconds(), 3) if latest_time else None,
            "consecutive_failures": 0,
        }

    def operations_sources(self) -> list[dict[str, Any]]:
        sources = {name: {"source": name, "last_success": None, "last_failure": None, "consecutive_failures": 0, "last_products_valid": 0, "last_quality_score": None} for name in self.runs.sources}
        remote_health = self.supabase.list_source_health() if self.supabase.configured else []
        if remote_health:
            for row in remote_health:
                sources[row["source"]] = {
                    "source": row["source"],
                    "last_success": row.get("last_success_at"),
                    "last_failure": row.get("last_failure_at"),
                    "consecutive_failures": int(row.get("consecutive_failures") or 0),
                    "last_products_valid": row.get("last_products_valid", 0),
                    "last_quality_score": row.get("last_quality_score"),
                }
        else:
            with self._lock:
                records = list(self.runs._runs.values())
            for record in records:
                summary = record["summary"]
                item = sources.setdefault(summary.source, {"source": summary.source, "consecutive_failures": 0})
                if summary.status == "FAILED":
                    item["last_failure"] = summary.finished_at.isoformat() if summary.finished_at else None
                    item["consecutive_failures"] = int(item.get("consecutive_failures", 0)) + 1
                else:
                    item["last_success"] = summary.finished_at.isoformat() if summary.finished_at else None
                    item["consecutive_failures"] = 0
                    item["last_products_valid"] = summary.products_valid
                    item["last_quality_score"] = (record.get("quality") or {}).get("score")
        result = []
        now = datetime.now(timezone.utc)
        for item in sources.values():
            failures = int(item.get("consecutive_failures", 0))
            if failures >= 3:
                status = "FAILED"
            elif failures:
                status = "DEGRADED"
            elif (last_success := self._as_datetime(item.get("last_success"))) and (now - last_success).total_seconds() > 86400:
                status = "STALE"
            elif not item.get("last_success"):
                status = "DISABLED"
            else:
                status = "HEALTHY"
            result.append({**item, "operational_status": status})
        return sorted(result, key=lambda item: item["source"])

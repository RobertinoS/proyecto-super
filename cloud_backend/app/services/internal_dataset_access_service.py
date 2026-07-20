from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from ..config import Settings
from .supabase_service import SupabaseService


ELIGIBLE_DATASET_STATUSES = frozenset({"PUBLISHED_PRIVATE", "ACTIVE"})


class InternalDatasetAccessError(RuntimeError):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class AccessGrant:
    dataset_id: str
    request_id: str
    access_url: str
    expires_at: datetime


class InternalDatasetAccessService:
    """Backend-only private dataset access behind the service API key."""

    def __init__(
        self,
        settings: Settings,
        supabase: SupabaseService,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.settings = settings
        self.supabase = supabase
        self.now = now or (lambda: datetime.now(timezone.utc))
        self._grants: dict[tuple[str, str], AccessGrant] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _metadata(dataset: dict[str, Any]) -> dict[str, Any]:
        return {
            "dataset_id": str(dataset["id"]),
            "status": str(dataset["status"]),
            "approval_id": str(dataset["approval_id"]),
            "row_count": int(dataset.get("row_count", dataset.get("rows", 0))),
            "quality_score": dataset.get("quality_score"),
            "created_at": dataset.get("created_at"),
            "checksum_present": bool(dataset.get("checksum_sha256")),
        }

    def _dataset_or_error(self, dataset_id: str) -> dict[str, Any]:
        dataset = self.supabase.get_private_dataset(dataset_id)
        if not dataset:
            raise InternalDatasetAccessError(404, "Dataset privado no encontrado")
        return dataset

    def _assert_eligible(self, dataset: dict[str, Any]) -> None:
        status = str(dataset.get("status", ""))
        if status == "REVOKED":
            raise InternalDatasetAccessError(410, "Dataset privado revocado")
        if status not in ELIGIBLE_DATASET_STATUSES:
            raise InternalDatasetAccessError(409, "Dataset privado no esta aprobado para acceso interno")
        if not dataset.get("checksum_sha256"):
            raise InternalDatasetAccessError(409, "Dataset privado sin checksum verificable")
        approval_id = dataset.get("approval_id")
        approval = self.supabase.get_dataset_approval_by_id(str(approval_id)) if approval_id else None
        if not approval or approval.get("status") != "APPROVED":
            raise InternalDatasetAccessError(409, "Dataset privado sin aprobacion vigente")

    def list_datasets(self) -> list[dict[str, Any]]:
        records = []
        for dataset in self.supabase.list_private_datasets():
            try:
                self._assert_eligible(dataset)
            except InternalDatasetAccessError:
                continue
            records.append(self._metadata(dataset))
        return records

    def current_dataset(self) -> dict[str, Any]:
        candidates = self.list_datasets()
        active = [item for item in candidates if item["status"] == "ACTIVE"]
        selected = active or [item for item in candidates if item["status"] == "PUBLISHED_PRIVATE"]
        if not selected:
            raise InternalDatasetAccessError(404, "No hay dataset privado activo")
        return sorted(selected, key=lambda item: str(item.get("created_at") or ""), reverse=True)[0]

    def get_dataset(self, dataset_id: str) -> dict[str, Any]:
        dataset = self._dataset_or_error(dataset_id)
        self._assert_eligible(dataset)
        return self._metadata(dataset)

    def _audit(
        self,
        dataset_id: str,
        request_id: str,
        action: str,
        result: str,
        expires_at: datetime | None = None,
        denial_reason: str | None = None,
    ) -> dict[str, Any]:
        return self.supabase.save_dataset_access_log(
            {
                "dataset_id": dataset_id,
                "user_id": None,
                "actor_type": "service",
                "action": action,
                "result": result,
                "request_id": request_id,
                "role_snapshot": [],
                "expires_at": expires_at.isoformat() if expires_at else None,
                "denial_reason": denial_reason,
            }
        )

    def access_dataset(self, dataset_id: str, request_id: str) -> dict[str, Any]:
        dataset = self._dataset_or_error(dataset_id)
        self._assert_eligible(dataset)

        existing = self.supabase.find_dataset_access_log_by_actor("service", request_id)
        if existing:
            with self._lock:
                cached = self._grants.get((dataset_id, request_id))
            if cached and cached.expires_at > self.now():
                return {
                    "dataset_id": cached.dataset_id,
                    "request_id": cached.request_id,
                    "access_url": cached.access_url,
                    "expires_at": cached.expires_at,
                    "expires_in_seconds": 300,
                    "duplicate_request": True,
                }
            raise InternalDatasetAccessError(409, "Solicitud de acceso ya procesada; use un request_id nuevo")

        if not self.settings.enable_internal_dataset_access:
            self._audit(dataset_id, request_id, "ACCESS_DENIED", "DENIED", denial_reason="INTERNAL_ACCESS_DISABLED")
            raise InternalDatasetAccessError(409, "Acceso interno temporal deshabilitado")

        try:
            if not self.supabase.is_bucket_private(self.settings.published_bucket):
                self._audit(dataset_id, request_id, "ACCESS_DENIED", "DENIED", denial_reason="BUCKET_NOT_PRIVATE")
                raise InternalDatasetAccessError(409, "El bucket del dataset no es privado")
            path = str(dataset.get("dataset_path") or "")
            if not path or not self.supabase.storage_object_exists(self.settings.published_bucket, path):
                self._audit(dataset_id, request_id, "ACCESS_DENIED", "DENIED", denial_reason="STORAGE_OBJECT_UNAVAILABLE")
                raise InternalDatasetAccessError(503, "Storage privado no disponible")
            url = self.supabase.create_signed_download_url(self.settings.published_bucket, path, expires_in=300)
        except InternalDatasetAccessError:
            raise
        except Exception as exc:
            raise InternalDatasetAccessError(503, "Storage privado no disponible") from exc
        if not url:
            self._audit(dataset_id, request_id, "ACCESS_DENIED", "DENIED", denial_reason="SIGNED_URL_UNAVAILABLE")
            raise InternalDatasetAccessError(503, "Storage privado no disponible")

        expires_at = self.now() + timedelta(seconds=300)
        self._audit(dataset_id, request_id, "URL_ISSUED", "ALLOWED", expires_at=expires_at)
        grant = AccessGrant(dataset_id, request_id, url, expires_at)
        with self._lock:
            self._grants[(dataset_id, request_id)] = grant
        return {
            "dataset_id": dataset_id,
            "request_id": request_id,
            "access_url": url,
            "expires_at": expires_at,
            "expires_in_seconds": 300,
            "duplicate_request": False,
        }

    def audit_for_dataset(self, dataset_id: str) -> list[dict[str, Any]]:
        self._dataset_or_error(dataset_id)
        rows = self.supabase.list_dataset_access_logs(dataset_id)
        return [
            {
                key: row.get(key)
                for key in (
                    "id", "dataset_id", "actor_type", "action", "result", "request_id",
                    "expires_at", "denial_reason", "created_at",
                )
            }
            for row in rows
        ]

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi.testclient import TestClient

from cloud_backend.app.config import Settings
from cloud_backend.app.main import create_app
from cloud_backend.app.services.internal_dataset_access_service import InternalDatasetAccessService


API_KEY = "internal-service-test-key"
NOW = datetime(2026, 7, 19, 12, 0, tzinfo=timezone.utc)


class FakePrivateDatasetStore:
    def __init__(self, datasets: list[dict[str, Any]] | None = None, bucket_private: bool = True, object_exists: bool = True) -> None:
        self.datasets = {row["id"]: dict(row) for row in (datasets or [active_dataset()])}
        self.approvals = {row["approval_id"]: {"id": row["approval_id"], "status": "APPROVED"} for row in self.datasets.values()}
        self.bucket_private = bucket_private
        self.object_exists = object_exists
        self.logs: list[dict[str, Any]] = []
        self.signed_url_calls: list[tuple[str, str, int]] = []

    def get_private_dataset(self, dataset_id: str) -> dict[str, Any] | None:
        row = self.datasets.get(dataset_id)
        return dict(row) if row else None

    def list_private_datasets(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.datasets.values()]

    def get_dataset_approval_by_id(self, approval_id: str) -> dict[str, Any] | None:
        row = self.approvals.get(approval_id)
        return dict(row) if row else None

    def find_dataset_access_log_by_actor(self, actor_type: str, request_id: str) -> dict[str, Any] | None:
        for row in self.logs:
            if row.get("actor_type") == actor_type and row.get("request_id") == request_id:
                return dict(row)
        return None

    def save_dataset_access_log(self, record: dict[str, Any]) -> dict[str, Any]:
        existing = self.find_dataset_access_log_by_actor(str(record.get("actor_type")), str(record["request_id"]))
        if existing:
            return existing
        saved = {"id": f"audit-{len(self.logs) + 1}", **record, "created_at": NOW.isoformat()}
        self.logs.append(saved)
        return dict(saved)

    def list_dataset_access_logs(self, dataset_id: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self.logs if row.get("dataset_id") == dataset_id]

    def is_bucket_private(self, bucket: str) -> bool:
        assert bucket == "published-price-datasets"
        return self.bucket_private

    def storage_object_exists(self, bucket: str, path: str) -> bool:
        assert bucket == "published-price-datasets"
        assert path == "published/2026/07/19/run-active/precios_aprobados.csv"
        return self.object_exists

    def create_signed_download_url(self, bucket: str, path: str, expires_in: int = 300) -> str:
        self.signed_url_calls.append((bucket, path, expires_in))
        return "https://storage.example.test/sign/temporary-access-token"


def active_dataset(status: str = "ACTIVE") -> dict[str, Any]:
    return {
        "id": "dataset-active",
        "scrape_run_id": "run-active",
        "approval_id": "approval-active",
        "status": status,
        "dataset_path": "published/2026/07/19/run-active/precios_aprobados.csv",
        "manifest_path": "published/2026/07/19/run-active/manifiesto.json",
        "row_count": 3,
        "checksum_sha256": "a" * 64,
        "quality_score": 100.0,
        "created_at": NOW.isoformat(),
    }


def build_client(
    *,
    enabled: bool = False,
    datasets: list[dict[str, Any]] | None = None,
    bucket_private: bool = True,
    object_exists: bool = True,
) -> tuple[TestClient, FakePrivateDatasetStore]:
    settings = Settings(
        scraper_api_key=API_KEY,
        source_mode="fixture",
        enable_internal_dataset_access=enabled,
    )
    app = create_app(settings)
    store = FakePrivateDatasetStore(datasets, bucket_private=bucket_private, object_exists=object_exists)
    app.state.internal_dataset_access_service = InternalDatasetAccessService(settings, store, now=lambda: NOW)
    return TestClient(app), store


def service_headers() -> dict[str, str]:
    return {"X-API-Key": API_KEY}


def test_internal_dataset_access_flag_defaults_to_false():
    assert Settings().enable_internal_dataset_access is False


def test_internal_endpoints_require_service_api_key():
    client, _ = build_client()
    assert client.get("/internal/private-datasets").status_code == 401
    assert client.get("/internal/private-datasets", headers={"X-API-Key": "wrong"}).status_code == 403


def test_list_current_and_metadata_return_only_eligible_approved_datasets():
    revoked = active_dataset("REVOKED")
    revoked["id"] = "dataset-revoked"
    pending = active_dataset("PUBLISHED_PRIVATE")
    pending["id"] = "dataset-pending"
    pending["approval_id"] = "approval-pending"
    client, store = build_client(datasets=[active_dataset(), revoked, pending])
    store.approvals["approval-pending"]["status"] = "PENDING_REVIEW"

    listed = client.get("/internal/private-datasets", headers=service_headers())
    current = client.get("/internal/private-datasets/current", headers=service_headers())
    metadata = client.get("/internal/private-datasets/dataset-active", headers=service_headers())

    assert listed.status_code == 200
    assert [row["dataset_id"] for row in listed.json()] == ["dataset-active"]
    assert current.status_code == 200 and current.json()["dataset_id"] == "dataset-active"
    assert metadata.status_code == 200
    assert "dataset_path" not in metadata.json()
    assert metadata.json()["checksum_present"] is True


def test_not_found_unapproved_and_revoked_datasets_are_blocked():
    revoked = active_dataset("REVOKED")
    revoked["id"] = "dataset-revoked"
    unapproved = active_dataset("PUBLISHED_PRIVATE")
    unapproved["id"] = "dataset-unapproved"
    unapproved["approval_id"] = "approval-unapproved"
    client, store = build_client(datasets=[revoked, unapproved])
    store.approvals["approval-unapproved"]["status"] = "PENDING_REVIEW"

    assert client.get("/internal/private-datasets/missing", headers=service_headers()).status_code == 404
    assert client.get("/internal/private-datasets/dataset-revoked", headers=service_headers()).status_code == 410
    assert client.get("/internal/private-datasets/dataset-unapproved", headers=service_headers()).status_code == 409


def test_published_private_is_eligible_but_missing_checksum_is_not():
    published = active_dataset("PUBLISHED_PRIVATE")
    published["id"] = "dataset-published"
    published["approval_id"] = "approval-published"
    no_checksum = active_dataset()
    no_checksum["id"] = "dataset-no-checksum"
    no_checksum["approval_id"] = "approval-no-checksum"
    no_checksum["checksum_sha256"] = ""
    client, _ = build_client(datasets=[published, no_checksum])

    assert client.get("/internal/private-datasets/dataset-published", headers=service_headers()).status_code == 200
    assert client.get("/internal/private-datasets/dataset-no-checksum", headers=service_headers()).status_code == 409


def test_feature_flag_defaults_to_false_and_audits_controlled_denial():
    client, store = build_client(enabled=False)
    response = client.post(
        "/internal/private-datasets/dataset-active/access",
        headers=service_headers(),
        json={"request_id": "internal-access-001"},
    )
    assert response.status_code == 409
    assert store.logs[0]["actor_type"] == "service"
    assert store.logs[0]["action"] == "ACCESS_DENIED"
    assert store.logs[0]["denial_reason"] == "INTERNAL_ACCESS_DISABLED"


def test_temporary_url_is_capped_to_five_minutes_and_request_is_idempotent():
    client, store = build_client(enabled=True)
    payload = {"request_id": "internal-access-002"}
    first = client.post("/internal/private-datasets/dataset-active/access", headers=service_headers(), json=payload)
    second = client.post("/internal/private-datasets/dataset-active/access", headers=service_headers(), json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["expires_in_seconds"] == 300
    assert first.json()["access_url"] == second.json()["access_url"]
    assert second.json()["duplicate_request"] is True
    assert store.signed_url_calls == [("published-price-datasets", "published/2026/07/19/run-active/precios_aprobados.csv", 300)]
    assert len(store.logs) == 1
    assert store.logs[0]["action"] == "URL_ISSUED"
    assert "temporary-access-token" not in str(store.logs[0])


def test_private_bucket_and_storage_are_required_before_url_issuance():
    non_private_client, non_private_store = build_client(enabled=True, bucket_private=False)
    non_private = non_private_client.post(
        "/internal/private-datasets/dataset-active/access",
        headers=service_headers(),
        json={"request_id": "internal-access-003"},
    )
    unavailable_client, unavailable_store = build_client(enabled=True, object_exists=False)
    unavailable = unavailable_client.post(
        "/internal/private-datasets/dataset-active/access",
        headers=service_headers(),
        json={"request_id": "internal-access-004"},
    )

    assert non_private.status_code == 409
    assert unavailable.status_code == 503
    assert non_private_store.signed_url_calls == []
    assert unavailable_store.signed_url_calls == []


def test_access_audit_is_sanitized_and_remains_available_for_governance():
    client, _ = build_client(enabled=True)
    client.post(
        "/internal/private-datasets/dataset-active/access",
        headers=service_headers(),
        json={"request_id": "internal-access-005"},
    )
    response = client.get("/internal/private-datasets/dataset-active/audit", headers=service_headers())
    assert response.status_code == 200
    entry = response.json()[0]
    assert entry["actor_type"] == "service"
    assert "access_url" not in entry
    assert "dataset_path" not in entry


def test_jwt_and_machine_endpoints_remain_separate_from_internal_pilot():
    client, _ = build_client()
    assert client.get("/auth/me").status_code == 401
    assert client.post("/jobs/scrape", json={"source": "vea"}, headers=service_headers()).status_code == 200
    assert client.get("/internal/private-datasets", headers={"Authorization": "Bearer ignored"}).status_code == 401


def test_internal_access_responses_and_openapi_do_not_expose_service_key():
    client, _ = build_client()
    response = client.get("/internal/private-datasets", headers=service_headers())
    schema = client.get("/openapi.json").json()
    assert API_KEY not in response.text
    assert API_KEY not in str(schema)
    assert "/internal/private-datasets/{dataset_id}/access" in schema["paths"]

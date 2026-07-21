from __future__ import annotations

import csv
import io
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from cloud_backend.app.config import Settings
from cloud_backend.app.main import create_app
from cloud_backend.app.services.internal_dataset_access_service import ELIGIBLE_DATASET_STATUSES
from cloud_backend.tests.test_api import API_KEY, FakeSource, auth, valid_row


class RecordingPrivateStorage:
    configured = True

    def __init__(self) -> None:
        self.uploads: list[tuple[str, str, str]] = []
        self.datasets: list[dict] = []
        self.publications: list[dict] = []
        self.events: list[tuple] = []

    def upload_bytes(self, bucket: str, path: str, content: bytes, content_type: str) -> None:
        self.uploads.append((bucket, path, content_type))

    def upload_json(self, bucket: str, path: str, payload: dict) -> None:
        self.uploads.append((bucket, path, "application/json"))

    def save_private_dataset(self, record: dict) -> None:
        self.datasets.append(dict(record))

    def save_publication_run(self, record: dict) -> None:
        self.publications.append(dict(record))

    def save_execution_event(self, execution_id: str, run_id: str, event_type: str, status: str, metadata: dict | None = None) -> None:
        self.events.append((execution_id, run_id, event_type, status, metadata))


def client_for(source: FakeSource | None = None) -> TestClient:
    return TestClient(create_app(Settings(scraper_api_key=API_KEY, source_mode="fixture"), {"fake": source or FakeSource()}))


def ready_run(client: TestClient) -> str:
    run = client.post("/jobs/scrape", json={"source": "fake", "dry_run": True}, headers=auth()).json()
    processed = client.post("/pipeline/process", json={"run_id": run["run_id"]}, headers=auth())
    assert processed.status_code == 200
    assert processed.json()["status"] == "READY_FOR_APPROVAL"
    return run["run_id"]


def test_review_endpoints_require_api_key():
    assert client_for().get("/reviews").status_code == 401
    assert client_for().get("/operations/summary").status_code == 401


def test_human_approval_is_idempotent_and_private_publication_stays_dry_run():
    client = client_for()
    run_id = ready_run(client)
    requested = client.post(
        f"/runs/{run_id}/request-approval",
        json={"actor": "reviewer-a"},
        headers=auth(),
    )
    assert requested.status_code == 200
    assert requested.json()["status"] == "READY_FOR_APPROVAL"

    first = client.post(f"/runs/{run_id}/approve-dataset", json={"actor": "reviewer-a"}, headers=auth())
    second = client.post(f"/runs/{run_id}/approve-dataset", json={"actor": "reviewer-a"}, headers=auth())
    assert first.status_code == second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["status"] == "APPROVED"

    publication = client.post(
        f"/runs/{run_id}/private-publish",
        json={"actor": "reviewer-a", "dry_run": True},
        headers=auth(),
    )
    assert publication.status_code == 200
    dataset = publication.json()
    assert dataset["status"] == "PRIVATE_DRY_RUN"
    assert dataset["private"] is True
    assert dataset["dry_run"] is True
    assert dataset["dataset_path"].endswith("/precios_aprobados.csv")
    assert len(dataset["checksum_sha256"]) == 64

    assert client.get("/datasets/latest-approved", headers=auth()).status_code == 200
    assert client.get(f"/datasets/{dataset['id']}", headers=auth()).status_code == 200
    assert client.get(f"/datasets/{dataset['id']}/download-url", headers=auth()).status_code == 409


def test_effective_private_publication_emits_status_eligible_for_internal_access():
    client = client_for()
    run_id = ready_run(client)
    assert client.post(f"/runs/{run_id}/request-approval", json={"actor": "reviewer-release"}, headers=auth()).status_code == 200
    assert client.post(f"/runs/{run_id}/approve-dataset", json={"actor": "reviewer-release"}, headers=auth()).status_code == 200

    publication = client.app.state.private_publication_service
    publication.settings = replace(publication.settings, enable_private_publication=True)
    storage = RecordingPrivateStorage()
    publication.supabase = storage

    dataset = publication.publish(run_id, "reviewer-release", dry_run=False)

    assert dataset["status"] == "PUBLISHED_PRIVATE"
    assert dataset["status"] in ELIGIBLE_DATASET_STATUSES
    assert dataset["dry_run"] is False
    assert len(storage.uploads) == 2
    assert storage.datasets[0]["status"] == "PUBLISHED_PRIVATE"


def test_private_publication_csv_keeps_the_dashboard_price_contract():
    client = client_for()
    run_id = ready_run(client)
    rows = client.app.state.run_service.get(run_id)["processed"]
    csv_text = client.app.state.private_publication_service._csv_bytes(rows).decode("utf-8")
    headers = set(csv.DictReader(io.StringIO(csv_text)).fieldnames or [])

    assert {
        "comercio", "sucursal", "localidad", "producto", "marca", "categoria",
        "presentacion", "precio", "fecha_relevamiento", "fuente",
    }.issubset(headers)


def test_critical_pending_reviews_block_dataset_approval_and_corrections_are_traced():
    invalid = valid_row()
    invalid["precio_efectivo"] = -5
    invalid["precio_regular"] = -5
    client = client_for(FakeSource(rows=[invalid]))
    run = client.post("/jobs/scrape", json={"source": "fake"}, headers=auth()).json()
    assert client.post("/pipeline/process", json={"run_id": run["run_id"]}, headers=auth()).json()["status"] == "QUALITY_REJECTED"
    request = client.post(
        f"/runs/{run['run_id']}/request-approval",
        json={"actor": "reviewer-b"},
        headers=auth(),
    )
    assert request.status_code == 200
    assert request.json()["status"] == "PENDING_REVIEW"
    reviews = client.get(f"/reviews?run_id={run['run_id']}", headers=auth()).json()
    assert any(item["severity"] == "CRITICAL" for item in reviews)

    review = reviews[0]
    corrected = client.post(
        f"/reviews/{review['id']}/correct",
        json={"actor": "reviewer-b", "notes": "Valor verificado", "corrected_value": {"precio_efectivo": 2500}},
        headers=auth(),
    )
    assert corrected.status_code == 200
    assert corrected.json()["status"] == "CORRECTED"
    assert corrected.json()["decision_notes"]["corrected_value"]["precio_efectivo"] == 2500
    repeated = client.post(
        f"/reviews/{review['id']}/correct",
        json={"actor": "reviewer-b", "notes": "Valor verificado", "corrected_value": {"precio_efectivo": 2500}},
        headers=auth(),
    )
    assert repeated.status_code == 200
    blocked = client.post(f"/runs/{run['run_id']}/approve-dataset", json={"actor": "reviewer-b"}, headers=auth())
    assert blocked.status_code == 409


def test_reject_requires_reason_and_operations_exposes_safe_health():
    client = client_for()
    run_id = ready_run(client)
    assert client.post(
        f"/runs/{run_id}/reject-dataset", json={"actor": "reviewer-c"}, headers=auth()
    ).status_code == 409
    rejected = client.post(
        f"/runs/{run_id}/reject-dataset", json={"actor": "reviewer-c", "reason": "Fuente pendiente"}, headers=auth()
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "REJECTED"

    summary = client.get("/operations/summary", headers=auth())
    sources = client.get("/operations/sources", headers=auth())
    assert summary.status_code == sources.status_code == 200
    assert "pending_reviews" in summary.json()
    assert sources.json()[0]["operational_status"] == "HEALTHY"


def test_alerts_are_acknowledged_idempotently_without_exposing_metadata_secrets():
    client = client_for()
    first_created = client.post(
        "/operations/alerts",
        json={"source": "fake", "alert_type": "SOURCE_DEGRADED", "severity": "HIGH", "message": "Fixture signal", "idempotency_key": "alert-fixture"},
        headers=auth(),
    )
    second_created = client.post(
        "/operations/alerts",
        json={"source": "fake", "alert_type": "SOURCE_DEGRADED", "severity": "HIGH", "message": "Fixture signal", "idempotency_key": "alert-fixture"},
        headers=auth(),
    )
    assert first_created.status_code == second_created.status_code == 200
    alert = first_created.json()
    assert alert["id"] == second_created.json()["id"]
    listed = client.get("/operations/alerts", headers=auth())
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == alert["id"]
    first = client.post(f"/operations/alerts/{alert['id']}/acknowledge", json={"actor": "operator-a"}, headers=auth())
    second = client.post(f"/operations/alerts/{alert['id']}/acknowledge", json={"actor": "operator-a"}, headers=auth())
    assert first.status_code == second.status_code == 200
    assert second.json()["status"] == "ACKNOWLEDGED"


def test_operations_marks_old_source_as_stale_and_reports_data_age():
    client = client_for()
    run_id = ready_run(client)
    record = client.app.state.run_service.get(run_id)
    record["summary"].finished_at = datetime.now(timezone.utc) - timedelta(days=2)
    summary = client.get("/operations/summary", headers=auth()).json()
    sources = client.get("/operations/sources", headers=auth()).json()
    assert summary["data_age_seconds"] > 86400
    assert sources[0]["operational_status"] == "STALE"

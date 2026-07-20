from __future__ import annotations

from cloud_backend.app.config import Settings
from cloud_backend.app.services.supabase_service import SupabaseService


class Response:
    def __init__(self, payload=None, status_code=201):
        self.payload = [] if payload is None else payload
        self.status_code = status_code

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class Session:
    def __init__(self):
        self.calls = []
        self.response_payload = []

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        return Response(self.response_payload)

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        return Response(self.response_payload)

    def patch(self, url, **kwargs):
        self.calls.append(("PATCH", url, kwargs))
        return Response()


def test_unconfigured_supabase_is_noop():
    session = Session()
    service = SupabaseService(Settings(), session)
    service.save_scrape_run({"id": "x"})
    service.save_observations("x", [{"producto": "demo"}])
    assert session.calls == []


def test_configured_supabase_uses_server_headers_without_logging_secret():
    session = Session()
    settings = Settings(supabase_url="https://project.supabase.co", supabase_service_role_key="test-secret")
    service = SupabaseService(settings, session)
    service.save_scrape_run({"id": "x", "unexpected": "must-not-be-sent"})
    assert len(session.calls) == 1
    method, url, kwargs = session.calls[0]
    assert method == "POST"
    assert "/rest/v1/scrape_runs?on_conflict=execution_id" in url
    assert kwargs["headers"]["Authorization"] == "Bearer test-secret"
    assert "unexpected" not in kwargs["json"]


def test_observations_are_mapped_to_database_contract():
    session = Session()
    settings = Settings(supabase_url="https://project.supabase.co", supabase_service_role_key="test-secret")
    service = SupabaseService(settings, session)
    service.save_observations(
        "run-id",
        [{"producto": "Demo", "precio_efectivo": 10, "fecha_hora_extraccion": "2026-07-13T00:00:00Z", "archivo_origen": "ignored"}],
    )
    method, url, kwargs = session.calls[0]
    assert method == "POST"
    assert "on_conflict=run_id,raw_hash" in url
    assert kwargs["headers"]["Prefer"] == "resolution=ignore-duplicates,return=minimal"
    payload = kwargs["json"][0]
    assert payload["run_id"] == "run-id"
    assert payload["observed_at"] == "2026-07-13T00:00:00Z"
    assert "archivo_origen" not in payload


def test_remote_lookup_does_not_expose_credentials_in_url():
    session = Session()
    settings = Settings(supabase_url="https://project.supabase.co", supabase_service_role_key="test-secret")
    service = SupabaseService(settings, session)
    assert service.find_scrape_run("staging execution") is None
    method, url, kwargs = session.calls[0]
    assert method == "GET"
    assert "staging%20execution" in url
    assert "test-secret" not in url
    assert kwargs["headers"]["Authorization"] == "Bearer test-secret"


def test_events_health_and_publication_use_idempotent_upserts():
    session = Session()
    settings = Settings(supabase_url="https://project.supabase.co", supabase_service_role_key="test-secret")
    service = SupabaseService(settings, session)
    service.save_execution_event("exec", "run", "PIPELINE_PROCESSED", "READY_FOR_APPROVAL")
    service.update_source_health("vea", True, "1.0")
    service.save_publication_run({"scrape_run_id": "run", "status": "DRY_RUN"})
    urls = [call[1] for call in session.calls]
    assert any("on_conflict=execution_id,event_type,status" in url for url in urls)
    assert any("source_health?on_conflict=source" in url for url in urls)
    assert any("publication_runs?on_conflict=scrape_run_id,status" in url for url in urls)


def test_review_approval_alert_and_signed_url_use_server_side_contracts_only():
    session = Session()
    settings = Settings(supabase_url="https://project.supabase.co", supabase_service_role_key="test-secret")
    service = SupabaseService(settings, session)
    service.save_review({"id": "review", "scrape_run_id": "run", "source": "vea", "review_type": "OUTLIER", "severity": "HIGH", "status": "PENDING", "reason": "test", "idempotency_key": "review-key"})
    service.save_dataset_approval({"id": "approval", "scrape_run_id": "run", "status": "PENDING_REVIEW", "idempotency_key": "approval-key"})
    service.save_operational_alert({"id": "alert", "alert_type": "SOURCE_FAILURE", "severity": "HIGH", "status": "OPEN", "message": "test", "idempotency_key": "alert-key"})
    service.save_private_dataset({"id": "dataset", "scrape_run_id": "run", "approval_id": "approval", "status": "PRIVATE_DRY_RUN", "dataset_path": "published/file.csv", "manifest_path": "published/manifest.json", "row_count": 1, "checksum_sha256": "a" * 64, "approved_by": "reviewer"})
    session.response_payload = {"signedURL": "/object/sign/published-price-datasets/file.csv?token=temporary"}
    url = service.create_signed_download_url("published-price-datasets", "published/file.csv", 300)

    urls = [call[1] for call in session.calls]
    assert any("review_queue?on_conflict=idempotency_key" in item for item in urls)
    assert any("dataset_approvals?on_conflict=scrape_run_id" in item for item in urls)
    assert any("operational_alerts?on_conflict=idempotency_key" in item for item in urls)
    assert any("private_datasets?on_conflict=scrape_run_id,checksum_sha256" in item for item in urls)
    assert any("/storage/v1/object/sign/published-price-datasets/published/file.csv" in item for item in urls)
    assert url and url.startswith("https://project.supabase.co/storage/v1/object/sign/")
    assert "test-secret" not in "\n".join(urls)


def test_active_roles_and_access_audit_use_server_side_idempotent_contracts():
    session = Session()
    settings = Settings(supabase_url="https://project.supabase.co", supabase_service_role_key="test-secret")
    service = SupabaseService(settings, session)
    session.response_payload = [{"role": "viewer"}, {"role": "reviewer"}]
    assert service.list_active_user_roles("11111111-1111-4111-8111-111111111111") == ["viewer", "reviewer"]

    session.response_payload = []
    record = service.save_dataset_access_log(
        {
            "id": "audit",
            "user_id": "11111111-1111-4111-8111-111111111111",
            "action": "AUTHENTICATED",
            "result": "ALLOWED",
            "request_id": "request-audit-001",
            "role_snapshot": ["viewer"],
            "unexpected": "ignored",
        }
    )
    urls = [call[1] for call in session.calls]
    assert any("app_user_roles?user_id=eq.11111111-1111-4111-8111-111111111111&active=is.true&select=role" in url for url in urls)
    assert any("dataset_access_logs?on_conflict=user_id,request_id" in url for url in urls)
    post = next(call for call in session.calls if call[0] == "POST")
    assert post[2]["headers"]["Prefer"] == "resolution=ignore-duplicates,return=representation"
    assert "unexpected" not in post[2]["json"]
    assert record["request_id"] == "request-audit-001"

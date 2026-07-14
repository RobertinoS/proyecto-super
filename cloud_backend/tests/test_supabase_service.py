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

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        return Response()

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        return Response([])

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

from __future__ import annotations

from cloud_backend.app.config import Settings
from cloud_backend.app.services.supabase_service import SupabaseService


class Response:
    def raise_for_status(self):
        return None


class Session:
    def __init__(self):
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
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
    url, kwargs = session.calls[0]
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
    payload = session.calls[0][1]["json"][0]
    assert payload["run_id"] == "run-id"
    assert payload["observed_at"] == "2026-07-13T00:00:00Z"
    assert "archivo_origen" not in payload

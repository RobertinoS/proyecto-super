from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from cloud_backend.app.config import Settings
from cloud_backend.app.main import create_app
from cloud_backend.app.sources.base import BaseSource


API_KEY = "test-only-key"


class FakeSource(BaseSource):
    source_name = "fake"
    source_version = "test"

    def __init__(self, rows: list[dict[str, Any]] | None = None, fail: bool = False) -> None:
        self.rows = rows if rows is not None else [valid_row()]
        self.fail = fail

    def health_check(self) -> dict[str, Any]:
        return {"status": "available", "mode": "fixture"}

    def fetch_catalog(self, max_products: int, max_pages: int):
        if self.fail:
            raise TimeoutError("fixture timeout")
        return self.rows[:max_products], []

    def fetch_page(self, page: int, page_size: int):
        return self.rows[:page_size]

    def normalize_product(self, product: dict[str, Any]):
        return product

    def build_snapshot(self, products: list[dict[str, Any]]):
        return {"products": products}

    def validate_response(self, payload: Any) -> bool:
        return isinstance(payload, list)


def valid_row() -> dict[str, Any]:
    return {
        "comercio": "Demo",
        "sucursal": "Online",
        "localidad": "San Juan",
        "canal_precio": "ONLINE",
        "producto": "Yerba Demo 1 Kg",
        "marca": "Demo",
        "categoria": "Almacen",
        "presentacion": "1 Kg",
        "sku": "1",
        "ean": "7790000000001",
        "precio_regular": 3000.0,
        "precio_promocional": None,
        "precio_efectivo": 3000.0,
        "condicion_promocion": None,
        "medio_pago": None,
        "stock_publicado": 10,
        "fecha_hora_extraccion": "2026-07-13T12:00:00+00:00",
        "url_origen": "https://example.invalid/producto",
        "archivo_origen": "fixture",
        "extractor_version": "test",
        "raw_hash": "a" * 64,
    }


def client_for(source: BaseSource | None = None) -> TestClient:
    settings = Settings(scraper_api_key=API_KEY, source_mode="fixture")
    return TestClient(create_app(settings, {"fake": source or FakeSource()}))


def auth() -> dict[str, str]:
    return {"X-API-Key": API_KEY}


def test_health_is_public_and_does_not_expose_secret():
    response = client_for().get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert API_KEY not in response.text


def test_staging_health_is_degraded_without_durable_supabase():
    settings = Settings(app_env="staging", scraper_api_key=API_KEY, source_mode="fixture")
    client = TestClient(create_app(settings, {"fake": FakeSource()}))
    health = client.get("/health").json()
    assert health["status"] == "degraded"
    assert health["staging_ready"] is False
    run = client.post(
        "/jobs/scrape",
        json={"source": "fake", "dry_run": True, "trigger_type": "manual_staging"},
        headers=auth(),
    ).json()
    assert run["status"] == "FAILED"
    assert "Supabase staging no esta configurado" in run["error_summary"]


def test_sources_is_public_and_describes_mode():
    response = client_for().get("/sources")
    assert response.status_code == 200
    assert response.json()[0]["name"] == "fake"
    assert response.json()[0]["mode"] == "fixture"


def test_authentication_missing_and_invalid():
    client = client_for()
    payload = {"source": "fake"}
    assert client.post("/jobs/scrape", json=payload).status_code == 401
    assert client.post("/jobs/scrape", json=payload, headers={"X-API-Key": "wrong"}).status_code == 403


def test_scrape_process_and_get_job():
    client = client_for()
    scrape = client.post("/jobs/scrape", json={"source": "fake", "dry_run": True}, headers=auth())
    assert scrape.status_code == 200
    run = scrape.json()
    assert run["products_valid"] == 1
    status = client.get(f"/jobs/{run['run_id']}", headers=auth())
    assert status.status_code == 200
    process = client.post("/pipeline/process", json={"run_id": run["run_id"]}, headers=auth())
    assert process.status_code == 200
    assert process.json()["status"] == "READY_FOR_APPROVAL"


def test_execution_id_is_idempotent():
    client = client_for()
    payload = {"source": "fake", "execution_id": "same-execution", "dry_run": True}
    first = client.post("/jobs/scrape", json=payload, headers=auth()).json()
    second = client.post("/jobs/scrape", json=payload, headers=auth()).json()
    assert first["run_id"] == second["run_id"]
    assert second["duplicate_execution"] is True


def test_manual_staging_trigger_is_accepted_locally():
    response = client_for().post(
        "/jobs/scrape",
        json={"source": "fake", "execution_id": "manual-stage", "trigger_type": "manual_staging"},
        headers=auth(),
    )
    assert response.status_code == 200
    assert response.json()["execution_id"] == "manual-stage"


def test_empty_and_failed_source_are_controlled():
    empty = client_for(FakeSource(rows=[])).post("/jobs/scrape", json={"source": "fake"}, headers=auth()).json()
    assert empty["status"] == "EMPTY"
    failed = client_for(FakeSource(fail=True)).post("/jobs/scrape", json={"source": "fake"}, headers=auth()).json()
    assert failed["status"] == "FAILED"
    assert "TimeoutError" in failed["error_summary"]


def test_non_dry_run_is_blocked_without_persistent_storage():
    response = client_for().post(
        "/jobs/scrape",
        json={"source": "fake", "dry_run": False},
        headers=auth(),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "FAILED"
    assert "Supabase no esta configurado" in response.json()["error_summary"]


def test_publication_requires_quality_and_explicit_approval():
    client = client_for()
    run = client.post("/jobs/scrape", json={"source": "fake"}, headers=auth()).json()
    rejected = client.post(
        "/pipeline/publish",
        json={"run_id": run["run_id"], "approved": False, "dry_run": True},
        headers=auth(),
    )
    assert rejected.status_code == 409
    client.post("/pipeline/process", json={"run_id": run["run_id"]}, headers=auth())
    accepted = client.post(
        "/pipeline/publish",
        json={"run_id": run["run_id"], "approved": True, "approved_by": "test", "dry_run": True},
        headers=auth(),
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "DRY_RUN"


def test_invalid_observation_blocks_publication():
    invalid = valid_row()
    invalid["precio_efectivo"] = -1
    invalid["precio_regular"] = -1
    client = client_for(FakeSource(rows=[invalid]))
    run = client.post("/jobs/scrape", json={"source": "fake"}, headers=auth()).json()
    process = client.post("/pipeline/process", json={"run_id": run["run_id"]}, headers=auth()).json()
    assert process["status"] == "QUALITY_REJECTED"

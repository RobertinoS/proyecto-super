from __future__ import annotations

from typing import Any

from cloud_backend.app.config import Settings
from cloud_backend.app.models import ScrapeJobRequest
from cloud_backend.app.services.pipeline_service import PipelineService
from cloud_backend.app.services.publication_service import PublicationService
from cloud_backend.app.services.run_service import RunService
from cloud_backend.app.sources.base import BaseSource


def observation() -> dict[str, Any]:
    return {
        "comercio": "Vea",
        "sucursal": "Online nacional",
        "localidad": "San Juan",
        "canal_precio": "ONLINE",
        "producto": "Yerba fixture 1 Kg",
        "marca": "Fixture",
        "categoria": "Almacen",
        "presentacion": "1 Kg",
        "sku": "fixture-1",
        "ean": "7790000000001",
        "precio_regular": 3000.0,
        "precio_promocional": None,
        "precio_efectivo": 3000.0,
        "condicion_promocion": None,
        "medio_pago": None,
        "stock_publicado": 10,
        "fecha_hora_extraccion": "2026-07-13T12:00:00+00:00",
        "url_origen": "https://example.invalid/fixture",
        "raw_hash": "a" * 64,
    }


class CountingSource(BaseSource):
    source_name = "vea"
    source_version = "staging-test"

    def __init__(self):
        self.fetches = 0

    def health_check(self):
        return {"status": "available", "mode": "fixture"}

    def fetch_catalog(self, max_products: int, max_pages: int):
        self.fetches += 1
        return [observation()], []

    def fetch_page(self, page: int, page_size: int):
        return [observation()]

    def normalize_product(self, product):
        return product

    def build_snapshot(self, products):
        return {"products": products}

    def validate_response(self, payload):
        return isinstance(payload, list)


class MemorySupabase:
    def __init__(self):
        self.settings = Settings(
            app_env="staging",
            supabase_url="https://example.supabase.co",
            supabase_service_role_key="test-only",
            source_mode="fixture",
            enable_publication=False,
        )
        self.runs: dict[str, dict[str, Any]] = {}
        self.observations: dict[str, dict[str, dict[str, Any]]] = {}
        self.events: set[tuple[str, str, str]] = set()
        self.uploads: set[tuple[str, str]] = set()
        self.publications: set[tuple[str, str]] = set()

    @property
    def configured(self):
        return True

    def save_scrape_run(self, record):
        self.runs[record["execution_id"]] = dict(record)

    def find_scrape_run(self, execution_id):
        return self.runs.get(execution_id)

    def find_scrape_run_by_id(self, run_id):
        return next((row for row in self.runs.values() if row["id"] == run_id), None)

    def save_observations(self, run_id, rows):
        target = self.observations.setdefault(run_id, {})
        for row in rows:
            target.setdefault(row["raw_hash"], dict(row))

    def get_observations(self, run_id):
        return list(self.observations.get(run_id, {}).values())

    def mark_observations_quality(self, run_id, quality_status):
        for row in self.observations.get(run_id, {}).values():
            row["quality_status"] = quality_status

    def save_execution_event(self, execution_id, run_id, event_type, status, message=None, metadata=None):
        self.events.add((execution_id, event_type, status))

    def update_source_health(self, source, success, extractor_version, error=None):
        return None

    def save_publication_run(self, record):
        self.publications.add((record["scrape_run_id"], record["status"]))

    def upload_json(self, bucket, path, payload):
        self.uploads.add((bucket, path))

    def upload_bytes(self, bucket, path, content, content_type):
        self.uploads.add((bucket, path))


def test_staging_dry_run_is_durable_and_survives_service_restart():
    storage = MemorySupabase()
    source = CountingSource()
    request = ScrapeJobRequest(
        source="vea",
        dry_run=True,
        max_products=3,
        max_pages=1,
        execution_id="same-staging-execution",
        trigger_type="manual_staging",
    )

    first_service = RunService({"vea": source}, storage)
    first = first_service.execute(request)
    assert first.status == "SCRAPED"
    assert source.fetches == 1
    assert len(storage.observations[first.run_id]) == 1
    assert storage.runs[request.execution_id]["trigger_type"] == "manual"
    assert storage.runs[request.execution_id]["trigger_context"] == "manual_staging"

    restarted_service = RunService({"vea": source}, storage)
    duplicate = restarted_service.execute(request)
    assert duplicate.run_id == first.run_id
    assert duplicate.duplicate_execution is True
    assert source.fetches == 1

    pipeline = PipelineService(restarted_service)
    processed_first = pipeline.process(first.run_id, max_invalid_pct=10, dry_run=True)
    processed_second = pipeline.process(first.run_id, max_invalid_pct=10, dry_run=True)
    assert processed_first == processed_second
    assert processed_first.status == "READY_FOR_APPROVAL"
    processed_uploads = [path for bucket, path in storage.uploads if bucket == storage.settings.processed_bucket]
    assert len(processed_uploads) == 1

    publication = PublicationService(storage.settings, restarted_service, storage)
    result = publication.publish(first.run_id, approved=True, approved_by="test", dry_run=True)
    assert result.status == "DRY_RUN"
    assert (first.run_id, "DRY_RUN") in storage.publications


def test_duplicate_observation_hash_is_not_inserted_twice():
    storage = MemorySupabase()
    row = observation()
    storage.save_observations("run", [row, dict(row)])
    assert len(storage.observations["run"]) == 1

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import requests
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cloud_backend.app.config import Settings
from cloud_backend.app.main import create_app


DEFAULT_EXECUTION_ID = "sprint15-fixture-idempotency"


class ApiClient:
    def __init__(self, base_url: str | None, api_key: str) -> None:
        self.base_url = base_url.rstrip("/") if base_url else None
        self.api_key = api_key
        self.local = None
        if not self.base_url:
            settings = Settings(
                app_env="test",
                scraper_api_key=api_key,
                source_mode="fixture",
                enable_publication=False,
                max_products_per_run=5,
                max_pages_per_run=1,
            )
            self.local = TestClient(create_app(settings))

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None, protected: bool = True):
        headers = {"X-API-Key": self.api_key} if protected else {}
        if self.local:
            return self.local.request(method, path, json=payload, headers=headers)
        return requests.request(
            method,
            f"{self.base_url}{path}",
            json=payload,
            headers=headers,
            timeout=150,
        )


def validate(base_url: str | None, api_key: str, execution_id: str) -> dict[str, Any]:
    client = ApiClient(base_url, api_key)
    health = client.request("GET", "/health", protected=False)
    health.raise_for_status()
    health_data = health.json()
    if health_data.get("build_info", {}).get("source_mode") != "fixture":
        raise RuntimeError("La API no esta en SOURCE_MODE=fixture")
    if base_url and not health_data.get("staging_ready"):
        raise RuntimeError("Staging no esta listo: Supabase durable no esta configurado")

    scrape_payload = {
        "source": "vea",
        "dry_run": True,
        "max_products": 3,
        "max_pages": 1,
        "execution_id": execution_id,
        "trigger_type": "manual_staging",
    }
    first_response = client.request("POST", "/jobs/scrape", scrape_payload)
    first_response.raise_for_status()
    first = first_response.json()
    second_response = client.request("POST", "/jobs/scrape", scrape_payload)
    second_response.raise_for_status()
    second = second_response.json()

    if first["run_id"] != second["run_id"] or not second.get("duplicate_execution"):
        raise RuntimeError("El mismo execution_id no devolvio una corrida idempotente")

    process_payload = {"run_id": first["run_id"], "dry_run": True, "max_invalid_pct": 10}
    process_first = client.request("POST", "/pipeline/process", process_payload)
    process_first.raise_for_status()
    process_second = client.request("POST", "/pipeline/process", process_payload)
    process_second.raise_for_status()
    if process_first.json() != process_second.json():
        raise RuntimeError("El procesamiento repetido no fue idempotente")

    blocked = client.request(
        "POST",
        "/pipeline/publish",
        {"run_id": first["run_id"], "approved": False, "dry_run": True},
    )
    if blocked.status_code != 409:
        raise RuntimeError("La publicacion sin aprobacion no fue bloqueada")

    dry_publish = client.request(
        "POST",
        "/pipeline/publish",
        {"run_id": first["run_id"], "approved": True, "approved_by": "staging-validator", "dry_run": True},
    )
    dry_publish.raise_for_status()
    if dry_publish.json().get("status") != "DRY_RUN":
        raise RuntimeError("El gate de publicacion no permanecio en DRY_RUN")

    return {
        "mode": "remote" if base_url else "local",
        "execution_id": execution_id,
        "run_id": first["run_id"],
        "duplicate_execution": second["duplicate_execution"],
        "products": first["products_valid"],
        "process_status": process_first.json()["status"],
        "publication_without_approval": "BLOCKED",
        "publication_with_approval": dry_publish.json()["status"],
        "source_mode": health_data["build_info"]["source_mode"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida idempotencia staging sin imprimir credenciales")
    parser.add_argument("--base-url", help="URL FastAPI staging; si se omite usa TestClient y fixture local")
    parser.add_argument("--api-key-env", default="SCRAPER_API_KEY")
    parser.add_argument("--execution-id", default=DEFAULT_EXECUTION_ID)
    args = parser.parse_args()

    api_key = os.getenv(args.api_key_env, "local-staging-test-key" if not args.base_url else "")
    if not api_key:
        raise SystemExit(f"Falta la variable de entorno {args.api_key_env}")
    report = validate(args.base_url, api_key, args.execution_id)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

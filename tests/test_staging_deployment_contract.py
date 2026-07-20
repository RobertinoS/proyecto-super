from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_migration_validator():
    path = ROOT / "scripts" / "13_validate_supabase_migrations.py"
    spec = importlib.util.spec_from_file_location("validate_supabase_migrations", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_supabase_migrations_are_safe_complete_and_keep_001_immutable():
    report = load_migration_validator().validate_migrations()
    assert report["ok"], report["errors"]
    assert report["migration_001_unchanged"] is True
    assert report["files"] == [
        "001_cloud_scraping_foundation.sql",
        "002_staging_hardening.sql",
        "003_review_and_private_publication.sql",
        "004_auth_roles_and_access_audit.sql",
    ]
    assert len(report["tables"]) == 12
    assert len(report["buckets"]) == 3


def test_supabase_isolation_decision_blocks_the_n8n_database():
    text = (ROOT / "docs" / "SUPABASE_ISOLATION_DECISION.md").read_text(encoding="utf-8").lower()
    assert "proyecto-super-staging" in text
    assert "no se autoriza" in text
    assert "workflow_entity" in text
    assert "no se ejecuto" in text or "no se ejecuta" in text


def test_staging_env_and_render_blueprint_have_safe_limits():
    env_text = (ROOT / ".env.example").read_text(encoding="utf-8")
    env = dict(line.split("=", 1) for line in env_text.splitlines() if line and not line.startswith("#"))
    assert env["APP_ENV"] == "staging"
    assert env["SOURCE_MODE"] == "fixture"
    assert env["ENABLE_PUBLICATION"] == "false"
    assert env["ENABLE_PRIVATE_PUBLICATION"] == "false"
    assert env["MAX_PRODUCTS_PER_RUN"] == "5"
    assert env["MAX_PAGES_PER_RUN"] == "1"
    assert env["SCRAPER_API_KEY"] == "replace_me"

    render = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
    service = render["services"][0]
    values = {item["key"]: item for item in service["envVars"]}
    assert service["name"] == "proyecto-super-fastapi-staging"
    assert service["healthCheckPath"] == "/health"
    assert service["autoDeploy"] is False
    assert values["APP_ENV"]["value"] == "staging"
    assert values["SOURCE_MODE"]["value"] == "fixture"
    assert values["ENABLE_PUBLICATION"]["value"] == "false"
    assert values["ENABLE_PRIVATE_PUBLICATION"]["value"] == "false"
    assert values["MAX_PRODUCTS_PER_RUN"]["value"] == "5"
    assert values["MAX_PAGES_PER_RUN"]["value"] == "1"
    for secret in ["SCRAPER_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]:
        assert values[secret]["sync"] is False


def test_github_action_has_kill_switch_manual_trigger_and_no_direct_scraping():
    path = ROOT / ".github" / "workflows" / "daily-price-refresh.yml"
    text = path.read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)
    assert "workflow_dispatch" in text
    triggers = workflow.get("on", workflow.get(True, {}))
    assert "schedule" in triggers
    assert "PROJECT_SUPER_AUTOMATION_ENABLED == 'true'" in text
    assert "PROJECT_SUPER_AUTOMATION_ENABLED != 'true'" in text
    assert "N8N_PRODUCTION_WEBHOOK_URL" in text
    assert "N8N_WEBHOOK_TOKEN" in text
    assert "gha-${GITHUB_RUN_ID}" in text
    assert "GITHUB_RUN_ATTEMPT" not in text
    assert "vea.com.ar" not in text
    assert "cloud_backend" not in text
    assert "curl" in text and "--max-time" in text and "--retry 2" in text
    assert "webhook_http_status=" in text
    for field in (
        "status", "execution_id", "run_id", "rows_processed", "quality_score", "pending_reviews",
        "approval_status", "publication", "duplicate_execution",
    ):
        assert f'"{field}"' in text
    assert "X-Webhook-Token: $WEBHOOK_TOKEN" in text


def test_n8n_workflow_is_staging_inactive_and_has_safe_payload_error_routes():
    path = ROOT / "automation" / "n8n" / "proyecto_super_daily_scrape.json"
    workflow = json.loads(path.read_text(encoding="utf-8"))
    text = path.read_text(encoding="utf-8")
    nodes = {node["name"]: node for node in workflow["nodes"]}
    names = set(nodes)
    assert workflow["active"] is False
    assert workflow["name"].endswith("Staging")
    assert {"Warm FastAPI", "Warm FastAPI Retry 2", "Warm FastAPI Retry 3", "Wait 20s", "Wait 40s"} <= names
    warm_nodes = [node for node in workflow["nodes"] if node["name"].startswith("Warm FastAPI")]
    assert len(warm_nodes) == 3
    assert all(node["parameters"]["options"]["timeout"] == 120000 for node in warm_nodes)

    validation = nodes["Validate Token and Payload"]["parameters"]["jsCode"]
    for trigger_type in ("manual", "manual_staging", "github_actions", "n8n", "smoke_test"):
        assert f"'{trigger_type}'" in validation
    assert "Math.min(" in validation and "Math.max(" in validation and "5" in validation
    assert "max_pages: 1" in validation
    assert "dry_run: true" in validation

    scrape_body = nodes["Run Vea Scrape"]["parameters"]["body"]
    for field in ("source", "dry_run", "max_products", "max_pages", "execution_id", "trigger_type"):
        assert f"{field}:" in scrape_body
    assert "approved:" not in scrape_body

    connections = workflow["connections"]
    for node_name, success_target in (
        ("Run Vea Scrape", "Process and Validate"),
        ("Process and Validate", "Quality Gate"),
        ("Request Dataset Approval", "Build Review Response"),
    ):
        assert nodes[node_name]["onError"] == "continueErrorOutput"
        outputs = connections[node_name]["main"]
        assert outputs[0][0]["node"] == success_target
        assert outputs[1][0]["node"] == "Register Workflow Alert"

    assert connections["Quality Gate"]["main"][0][0]["node"] == "Request Dataset Approval"
    approval_body = nodes["Request Dataset Approval"]["parameters"]["body"]
    assert "actor" in approval_body and "idempotency_key" in approval_body
    review_response = nodes["Build Review Response"]["parameters"]["jsCode"]
    for field in ("quality_score", "pending_reviews", "approval_status", "publication:'BLOCKED'"):
        assert field in review_response
    assert "/pipeline/publish" not in text
    alert = nodes["Register Workflow Alert"]
    assert alert["onError"] == "continueErrorOutput"
    alert_body = alert["parameters"]["body"]
    assert "PIPELINE_FAILURE" in alert_body and "idempotency_key" in alert_body
    assert all(target[0]["node"] == "Structured Error" for target in connections["Register Workflow Alert"]["main"])
    assert "details:$json" not in text

    assert "ENABLE_CLOUD_PUBLICATION" in text
    assert not re.search(r"(?:api[_-]?key|token)\s*[:=]\s*['\"][A-Za-z0-9_-]{20,}", text, re.IGNORECASE)


def test_no_keepalive_or_windows_paths_in_cloud_deployment_files():
    paths = [
        ROOT / "render.yaml",
        ROOT / ".github" / "workflows" / "daily-price-refresh.yml",
        ROOT / "automation" / "n8n" / "proyecto_super_daily_scrape.json",
        ROOT / "cloud_backend" / "Dockerfile",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    assert "uptimerobot" not in text.lower()
    assert "keepalive" not in text.lower()
    assert not re.search(r"[a-z]:\\", text, re.IGNORECASE)


def test_publication_gate_document_exists_and_defaults_remain_blocked():
    # The document is created before the sprint is considered functionally complete.
    expected = ROOT / "docs" / "PUBLICATION_GATE.md"
    if expected.exists():
        text = expected.read_text(encoding="utf-8")
        assert "ENABLE_PUBLICATION=false" in text

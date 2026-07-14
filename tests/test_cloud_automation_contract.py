from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_n8n_workflow_is_importable_and_has_safe_gates():
    path = ROOT / "automation" / "n8n" / "proyecto_super_daily_scrape.json"
    workflow = json.loads(path.read_text(encoding="utf-8"))
    names = {node["name"] for node in workflow["nodes"]}
    assert {
        "Webhook Trigger",
        "Validate Token and Payload",
        "Warm FastAPI",
        "Run Vea Scrape",
        "Process and Validate",
        "Quality Gate",
        "Publication Approved?",
        "Structured Error",
    } <= names
    assert workflow["active"] is False
    assert "ENABLE_CLOUD_PUBLICATION" in path.read_text(encoding="utf-8")


def test_github_action_is_single_daily_trigger_not_keepalive():
    path = ROOT / ".github" / "workflows" / "daily-price-refresh.yml"
    workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
    text = path.read_text(encoding="utf-8")
    assert "workflow_dispatch" in text
    assert '17 10 * * *' in text
    assert "N8N_PRODUCTION_WEBHOOK_URL" in text
    assert "N8N_WEBHOOK_TOKEN" in text
    assert "scrape" not in " ".join(workflow["jobs"].keys()).lower()
    assert "keepalive" not in text.lower()


def test_render_and_env_are_safe_by_default():
    render = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
    service = render["services"][0]
    assert service["healthCheckPath"] == "/health"
    assert service["autoDeploy"] is False
    env = {item["key"]: item for item in service["envVars"]}
    assert env["SOURCE_MODE"]["value"] == "fixture"
    assert env["ENABLE_PUBLICATION"]["value"] == "false"
    assert env["SCRAPER_API_KEY"]["sync"] is False


def test_cloud_artifacts_contain_no_plausible_real_secrets():
    paths = [
        ROOT / ".env.example",
        ROOT / "render.yaml",
        ROOT / ".github" / "workflows" / "daily-price-refresh.yml",
        ROOT / "automation" / "n8n" / "proyecto_super_daily_scrape.json",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    forbidden = ["eyJhbGciOi", "sbp_", "ghp_", "github_pat_", "postgresql://"]
    assert not any(value in text for value in forbidden)
    assert "SCRAPER_API_KEY=replace_me" in text
    assert "SUPABASE_SERVICE_ROLE_KEY=replace_me" in text


def test_supabase_migration_defines_idempotency_constraints():
    sql = (ROOT / "supabase" / "migrations" / "001_cloud_scraping_foundation.sql").read_text(encoding="utf-8").lower()
    for table in ["scrape_runs", "price_observations", "publication_runs", "source_health", "execution_events"]:
        assert f"table if not exists public.{table}" in sql
    assert "execution_id text not null unique" in sql
    assert "unique (run_id, raw_hash)" in sql
    assert "enable row level security" in sql

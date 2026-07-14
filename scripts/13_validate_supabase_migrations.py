from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MIGRATIONS = ROOT / "supabase" / "migrations"
MIGRATION_001_SHA256 = "4afda1982b27bfaab29a7f9b5793787331a32278152623be13bb3a531e6d55de"

EXPECTED_TABLES = {
    "scrape_runs": {"id", "execution_id", "source", "status", "started_at", "extractor_version"},
    "price_observations": {"id", "run_id", "raw_hash", "precio_efectivo", "observed_at", "quality_status"},
    "publication_runs": {"id", "scrape_run_id", "status", "dataset_path"},
    "source_health": {"source", "extractor_version", "updated_at"},
    "execution_events": {"id", "execution_id", "run_id", "event_type", "status", "created_at"},
}
EXPECTED_BUCKETS = {
    "raw-price-snapshots",
    "processed-price-datasets",
    "published-price-datasets",
}
FORBIDDEN_N8N_TABLES = {
    "workflow_entity",
    "execution_entity",
    "credentials_entity",
    "webhook_entity",
    "installed_packages",
    "installed_nodes",
}
DESTRUCTIVE_PATTERNS = {
    "drop_table_or_schema": r"\bdrop\s+(?:table|schema|database)\b",
    "truncate": r"\btruncate\b",
    "delete": r"\bdelete\s+from\b",
    "drop_column": r"\balter\s+table\b[\s\S]*?\bdrop\s+column\b",
}


def _without_comments(sql: str) -> str:
    return re.sub(r"--[^\n]*", "", sql)


def validate_migrations(directory: Path = DEFAULT_MIGRATIONS) -> dict:
    files = sorted(directory.glob("[0-9][0-9][0-9]_*.sql"))
    errors: list[str] = []
    warnings: list[str] = []
    if not files:
        return {"ok": False, "files": [], "errors": ["No se encontraron migraciones SQL"], "warnings": []}

    numbers = [int(path.name.split("_", 1)[0]) for path in files]
    if numbers != list(range(numbers[0], numbers[0] + len(numbers))):
        errors.append("La numeracion de migraciones no es consecutiva")

    migration_001 = directory / "001_cloud_scraping_foundation.sql"
    if not migration_001.exists():
        errors.append("Falta 001_cloud_scraping_foundation.sql")
        migration_001_unchanged = False
    else:
        digest = hashlib.sha256(migration_001.read_bytes()).hexdigest()
        migration_001_unchanged = digest == MIGRATION_001_SHA256
        if not migration_001_unchanged:
            errors.append("La migracion 001 fue modificada retroactivamente")

    combined = "\n".join(path.read_text(encoding="utf-8") for path in files)
    sql = _without_comments(combined).lower()

    for name, pattern in DESTRUCTIVE_PATTERNS.items():
        if re.search(pattern, sql, re.IGNORECASE):
            errors.append(f"Operacion destructiva detectada: {name}")

    for table in sorted(FORBIDDEN_N8N_TABLES):
        if re.search(rf"\b{re.escape(table)}\b", sql):
            errors.append(f"Referencia prohibida a tabla interna: {table}")

    for table, columns in EXPECTED_TABLES.items():
        if not re.search(rf"create\s+table\s+if\s+not\s+exists\s+public\.{table}\b", sql):
            errors.append(f"Falta tabla esperada: {table}")
        for column in columns:
            if not re.search(rf"\b{re.escape(column)}\b", sql):
                errors.append(f"Falta columna esperada: {table}.{column}")
        if f"alter table public.{table} enable row level security" not in sql:
            errors.append(f"RLS no habilitado: {table}")

    required_contracts = {
        "execution_id_unique": r"execution_id\s+text\s+not\s+null\s+unique",
        "observation_idempotency": r"unique\s*\(\s*run_id\s*,\s*raw_hash\s*\)",
        "run_foreign_key": r"references\s+public\.scrape_runs\s*\(\s*id\s*\)",
        "private_buckets": r"insert\s+into\s+storage\.buckets",
        "browser_role_revoke": r"revoke\s+all\s+on\s+table\s+public\.scrape_runs\s+from\s+anon\s*,\s*authenticated",
        "event_idempotency": r"unique\s+index[^;]+execution_events\s*\(\s*execution_id\s*,\s*event_type\s*,\s*status\s*\)",
    }
    for name, pattern in required_contracts.items():
        if not re.search(pattern, sql, re.IGNORECASE | re.DOTALL):
            errors.append(f"Contrato SQL ausente: {name}")

    missing_buckets = sorted(bucket for bucket in EXPECTED_BUCKETS if f"'{bucket}'" not in sql)
    if missing_buckets:
        errors.append(f"Buckets ausentes: {', '.join(missing_buckets)}")
    if re.search(r"create\s+policy[\s\S]+\bto\s+(?:public|anon|authenticated)\b", sql):
        errors.append("Se detecto una politica RLS para roles de navegador")
    if re.search(r"[a-z]:\\", sql, re.IGNORECASE):
        errors.append("Se detecto una ruta local de Windows en SQL")

    warnings.append("El esquema public solo es aceptable dentro del proyecto Supabase staging exclusivo")

    return {
        "ok": not errors,
        "files": [path.name for path in files],
        "migration_001_unchanged": migration_001_unchanged,
        "tables": sorted(EXPECTED_TABLES),
        "buckets": sorted(EXPECTED_BUCKETS),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida migraciones Supabase sin conectarse a servicios externos")
    parser.add_argument("--migrations", type=Path, default=DEFAULT_MIGRATIONS)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = validate_migrations(args.migrations)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Migraciones: {', '.join(report['files'])}")
        print(f"Tablas: {len(report.get('tables', []))}")
        print(f"Buckets: {len(report.get('buckets', []))}")
        print(f"Migracion 001 sin cambios: {'SI' if report.get('migration_001_unchanged') else 'NO'}")
        for warning in report["warnings"]:
            print(f"ADVERTENCIA: {warning}")
        for error in report["errors"]:
            print(f"ERROR: {error}")
        print(f"Resultado: {'OK' if report['ok'] else 'INVALIDO'}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

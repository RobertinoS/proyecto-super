from __future__ import annotations

import csv
import hashlib
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from normalize import clean_text, normalize_price_record

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None


DEFAULT_DB_PATH = Path("database/precios_san_juan.sqlite")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def stable_id(*parts: Any, prefix: str = "") -> str:
    raw = "|".join(clean_text(part) for part in parts if part is not None)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}{digest}" if prefix else digest


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path or os.getenv("DATABASE_PATH", DEFAULT_DB_PATH))
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sources (
            source_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            source_type TEXT,
            base_url TEXT,
            priority INTEGER,
            status TEXT,
            requires_js INTEGER DEFAULT 0,
            requires_location INTEGER DEFAULT 0,
            has_prices INTEGER DEFAULT 0,
            has_promotions INTEGER DEFAULT 0,
            confidence_score INTEGER DEFAULT 0,
            last_checked_at TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS stores (
            store_id TEXT PRIMARY KEY,
            source_id TEXT,
            chain TEXT,
            branch_name TEXT,
            province TEXT,
            department TEXT,
            city TEXT,
            address TEXT,
            latitude REAL,
            longitude REAL,
            external_store_id TEXT,
            active INTEGER DEFAULT 1,
            UNIQUE(source_id, chain, branch_name, city, address)
        );

        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            source_product_id TEXT,
            ean TEXT,
            name_raw TEXT,
            name_clean TEXT,
            brand TEXT,
            category TEXT,
            presentation_qty REAL,
            presentation_unit TEXT,
            normalized_unit TEXT,
            source_id TEXT,
            search_key TEXT,
            UNIQUE(source_id, ean, name_clean, brand, category)
        );

        CREATE TABLE IF NOT EXISTS prices (
            price_id TEXT PRIMARY KEY,
            capture_date TEXT,
            source_id TEXT,
            store_id TEXT,
            product_id TEXT,
            chain TEXT,
            branch_name TEXT,
            city TEXT,
            product_name_raw TEXT,
            product_name_clean TEXT,
            brand TEXT,
            category TEXT,
            price_list REAL,
            price_promo_1 REAL,
            promo_1_text TEXT,
            price_promo_2 REAL,
            promo_2_text TEXT,
            best_general_price REAL,
            best_conditional_price REAL,
            reference_price REAL,
            reference_unit TEXT,
            url TEXT,
            confidence_score INTEGER,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS scrape_runs (
            run_id TEXT PRIMARY KEY,
            source_id TEXT,
            started_at TEXT,
            finished_at TEXT,
            status TEXT,
            records_found INTEGER DEFAULT 0,
            records_saved INTEGER DEFAULT 0,
            errors_count INTEGER DEFAULT 0,
            error_summary TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_prices_product_clean ON prices(product_name_clean);
        CREATE INDEX IF NOT EXISTS idx_prices_chain_city ON prices(chain, city);
        CREATE INDEX IF NOT EXISTS idx_prices_best_price ON prices(best_general_price);
        """
    )
    conn.commit()


def bool_int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, str):
        return int(value.strip().lower() in {"true", "1", "yes", "si"})
    return int(bool(value))


def upsert_source(conn: sqlite3.Connection, source: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO sources (
            source_id, name, source_type, base_url, priority, status,
            requires_js, requires_location, has_prices, has_promotions,
            confidence_score, last_checked_at, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_id) DO UPDATE SET
            name=excluded.name,
            source_type=excluded.source_type,
            base_url=excluded.base_url,
            priority=excluded.priority,
            status=excluded.status,
            requires_js=excluded.requires_js,
            requires_location=excluded.requires_location,
            has_prices=excluded.has_prices,
            has_promotions=excluded.has_promotions,
            confidence_score=excluded.confidence_score,
            notes=excluded.notes
        """,
        (
            source.get("source_id"),
            source.get("name"),
            source.get("source_type"),
            source.get("base_url"),
            source.get("priority"),
            source.get("status"),
            bool_int(source.get("requires_js")),
            bool_int(source.get("requires_location")),
            bool_int(source.get("has_prices")),
            bool_int(source.get("has_promotions")),
            source.get("confidence_score"),
            source.get("last_checked_at"),
            source.get("notes"),
        ),
    )


def load_sources_from_config(config_path: str | Path = "config/fuentes.yml") -> list[dict[str, Any]]:
    path = Path(config_path)
    if not path.exists() or yaml is None:
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(data.get("sources", []))


def upsert_sources_from_config(conn: sqlite3.Connection, config_path: str | Path = "config/fuentes.yml") -> int:
    sources = load_sources_from_config(config_path)
    for source in sources:
        upsert_source(conn, source)
    active_ids = [str(source.get("source_id")) for source in sources if source.get("source_id")]
    if active_ids:
        placeholders = ",".join("?" for _ in active_ids)
        for table in ("prices", "products", "stores", "scrape_runs", "sources"):
            conn.execute(f"DELETE FROM {table} WHERE source_id NOT IN ({placeholders})", active_ids)
    conn.commit()
    return len(sources)


def upsert_store(conn: sqlite3.Connection, row: dict[str, Any]) -> str:
    store_id = row.get("store_id") or stable_id(
        row.get("source_id"), row.get("chain"), row.get("branch_name"), row.get("city"), row.get("address"), prefix="store_"
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO stores (
            store_id, source_id, chain, branch_name, province, department, city,
            address, latitude, longitude, external_store_id, active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            store_id,
            row.get("source_id"),
            row.get("chain"),
            row.get("branch_name"),
            row.get("province"),
            row.get("department"),
            row.get("city"),
            row.get("address"),
            row.get("latitude"),
            row.get("longitude"),
            row.get("external_store_id"),
            bool_int(row.get("active", True)),
        ),
    )
    return store_id


def upsert_product(conn: sqlite3.Connection, row: dict[str, Any]) -> str:
    product_id = row.get("product_id") or stable_id(
        row.get("source_id"), row.get("ean"), row.get("product_name_clean") or row.get("name_clean"), row.get("brand"), row.get("category"), prefix="prod_"
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO products (
            product_id, source_product_id, ean, name_raw, name_clean, brand,
            category, presentation_qty, presentation_unit, normalized_unit,
            source_id, search_key
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            product_id,
            row.get("source_product_id"),
            row.get("ean"),
            row.get("product_name_raw") or row.get("name_raw"),
            row.get("product_name_clean") or row.get("name_clean"),
            row.get("brand"),
            row.get("category"),
            row.get("presentation_qty"),
            row.get("presentation_unit"),
            row.get("normalized_unit"),
            row.get("source_id"),
            row.get("search_key"),
        ),
    )
    return product_id


def insert_price(conn: sqlite3.Connection, row: dict[str, Any]) -> str:
    normalized = normalize_price_record(row)
    store_id = upsert_store(conn, normalized)
    normalized["store_id"] = store_id
    product_id = upsert_product(conn, normalized)
    normalized["product_id"] = product_id
    price_id = normalized.get("price_id") or stable_id(
        normalized.get("capture_date"),
        normalized.get("source_id"),
        store_id,
        product_id,
        normalized.get("price_list"),
        normalized.get("price_promo_1"),
        normalized.get("price_promo_2"),
        prefix="price_",
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO prices (
            price_id, capture_date, source_id, store_id, product_id, chain,
            branch_name, city, product_name_raw, product_name_clean, brand,
            category, price_list, price_promo_1, promo_1_text, price_promo_2,
            promo_2_text, best_general_price, best_conditional_price,
            reference_price, reference_unit, url, confidence_score, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            price_id,
            normalized.get("capture_date"),
            normalized.get("source_id"),
            store_id,
            product_id,
            normalized.get("chain"),
            normalized.get("branch_name"),
            normalized.get("city"),
            normalized.get("product_name_raw"),
            normalized.get("product_name_clean"),
            normalized.get("brand"),
            normalized.get("category"),
            normalized.get("price_list"),
            normalized.get("price_promo_1"),
            normalized.get("promo_1_text"),
            normalized.get("price_promo_2"),
            normalized.get("promo_2_text"),
            normalized.get("best_general_price"),
            normalized.get("best_conditional_price"),
            normalized.get("reference_price"),
            normalized.get("reference_unit"),
            normalized.get("url"),
            normalized.get("confidence_score"),
            normalized.get("created_at") or utc_now(),
        ),
    )
    return price_id


def insert_price_rows(conn: sqlite3.Connection, rows: Iterable[dict[str, Any]]) -> int:
    before = conn.total_changes
    for row in rows:
        insert_price(conn, row)
    conn.commit()
    return conn.total_changes - before


def start_run(conn: sqlite3.Connection, source_id: str) -> str:
    run_id = stable_id(source_id, utc_now(), prefix="run_")
    conn.execute(
        "INSERT INTO scrape_runs (run_id, source_id, started_at, status) VALUES (?, ?, ?, ?)",
        (run_id, source_id, utc_now(), "running"),
    )
    conn.commit()
    return run_id


def finish_run(
    conn: sqlite3.Connection,
    run_id: str,
    status: str,
    records_found: int = 0,
    records_saved: int = 0,
    errors_count: int = 0,
    error_summary: str | None = None,
) -> None:
    conn.execute(
        """
        UPDATE scrape_runs
        SET finished_at=?, status=?, records_found=?, records_saved=?, errors_count=?, error_summary=?
        WHERE run_id=?
        """,
        (utc_now(), status, records_found, records_saved, errors_count, error_summary, run_id),
    )
    conn.commit()


def read_csv_flexible(path: Path) -> pd.DataFrame:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;|\t")
            sep = dialect.delimiter
        except csv.Error:
            sep = ","
    return pd.read_csv(path, sep=sep, encoding="utf-8", encoding_errors="replace")


def historical_rows(project_root: str | Path = ".") -> list[dict[str, Any]]:
    root = Path(project_root)
    combined_path = root / "data" / "Supermercados.csv"
    capture_date = datetime.fromtimestamp(combined_path.stat().st_mtime).date().isoformat() if combined_path.exists() else datetime.now().date().isoformat()
    rows: list[dict[str, Any]] = []
    if combined_path.exists():
        df = read_csv_flexible(combined_path)
        for _, item in df.iterrows():
            product = item.get("Producto")
            if not product or pd.isna(product):
                continue
            rows.append(
                {
                    "capture_date": capture_date,
                    "source_id": "historical_csv",
                    "chain": item.get("Supermercado") or "Historico",
                    "branch_name": "Historico San Juan",
                    "province": "San Juan",
                    "department": None,
                    "city": "San Juan",
                    "product_name_raw": product,
                    "brand": item.get("Marca"),
                    "category": item.get("Categoria") or item.get("CategorÃ­a") or item.get("Categoría"),
                    "price_list": item.get("Precio"),
                    "url": None,
                    "confidence_score": 65,
                    "source_product_id": None,
                }
            )
        return rows

    for path in sorted((root / "data").glob("*.csv")):
        if path.name.lower() == "supermercados.csv":
            continue
        df = read_csv_flexible(path)
        parts = path.stem.split("_")
        chain = parts[0]
        category = parts[1] if len(parts) > 1 else None
        capture = datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
        for _, item in df.iterrows():
            product = item.get("Producto")
            if not product or pd.isna(product):
                continue
            rows.append(
                {
                    "capture_date": capture,
                    "source_id": "historical_csv",
                    "chain": chain,
                    "branch_name": "Historico San Juan",
                    "province": "San Juan",
                    "department": None,
                    "city": "San Juan",
                    "product_name_raw": product,
                    "brand": item.get("Marca"),
                    "category": item.get("Categoria") or item.get("CategorÃ­a") or category,
                    "price_list": item.get("Precio"),
                    "url": None,
                    "confidence_score": 65,
                }
            )
    return rows


def import_historical_data(conn: sqlite3.Connection, project_root: str | Path = ".") -> int:
    upsert_source(
        conn,
        {
            "source_id": "historical_csv",
            "name": "CSV historicos del proyecto",
            "source_type": "local_historical_csv",
            "base_url": None,
            "priority": 9,
            "status": "loaded",
            "requires_js": False,
            "requires_location": False,
            "has_prices": True,
            "has_promotions": False,
            "confidence_score": 65,
            "last_checked_at": utc_now(),
            "notes": "Datos historicos extraidos por notebooks previos. Utiles como demo y respaldo, no como precio actualizado.",
        },
    )
    rows = historical_rows(project_root)
    return insert_price_rows(conn, rows)


def init_database(db_path: str | Path | None = None, config_path: str | Path = "config/fuentes.yml") -> sqlite3.Connection:
    conn = connect(db_path)
    create_schema(conn)
    upsert_sources_from_config(conn, config_path)
    return conn

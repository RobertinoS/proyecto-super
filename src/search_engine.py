from __future__ import annotations

import sqlite3
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from normalize import clean_text

try:
    from rapidfuzz import fuzz
except Exception:  # pragma: no cover
    fuzz = None


def similarity(query: str, candidate: str) -> float:
    q = clean_text(query)
    c = clean_text(candidate)
    if not q or not c:
        return 0.0
    if q in c:
        return 100.0
    if fuzz:
        return float(fuzz.token_set_ratio(q, c))
    return SequenceMatcher(None, q, c).ratio() * 100


def connect(db_path: str | Path = "database/precios_san_juan.sqlite") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def search_prices(
    query: str,
    db_path: str | Path = "database/precios_san_juan.sqlite",
    chain: str | None = None,
    city: str | None = None,
    category: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    conn = connect(db_path)
    params: list[Any] = []
    clauses = ["best_general_price IS NOT NULL"]
    if chain:
        clauses.append("LOWER(chain) = LOWER(?)")
        params.append(chain)
    if city:
        clauses.append("LOWER(city) = LOWER(?)")
        params.append(city)
    if category:
        clauses.append("LOWER(category) = LOWER(?)")
        params.append(category)
    sql = f"""
        SELECT *
        FROM prices
        WHERE {" AND ".join(clauses)}
        ORDER BY capture_date DESC
        LIMIT 3000
    """
    records = [dict(row) for row in conn.execute(sql, params).fetchall()]
    conn.close()
    scored = []
    for record in records:
        text = " ".join(
            str(record.get(key) or "")
            for key in ("product_name_clean", "product_name_raw", "brand", "category")
        )
        score = similarity(query, text)
        if score >= 45 or clean_text(query) in clean_text(text):
            record["similarity_score"] = round(score, 2)
            scored.append(record)
    scored.sort(
        key=lambda item: (
            -item.get("similarity_score", 0),
            item.get("best_general_price") if item.get("best_general_price") is not None else 10**12,
            -(item.get("confidence_score") or 0),
        )
    )
    return scored[:limit]


def rank_by_price(records: list[dict[str, Any]], conditional: bool = False) -> list[dict[str, Any]]:
    key = "best_conditional_price" if conditional else "best_general_price"
    return sorted(records, key=lambda item: item.get(key) if item.get(key) is not None else 10**12)

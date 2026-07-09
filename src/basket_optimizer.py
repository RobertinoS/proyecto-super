from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from search_engine import search_prices


def optimize_basket(
    products: list[str],
    db_path: str | Path = "database/precios_san_juan.sqlite",
    split_purchase: bool = True,
) -> dict[str, Any]:
    chosen_split = []
    totals_by_chain: dict[str, float] = defaultdict(float)
    candidates_by_product: dict[str, list[dict[str, Any]]] = {}

    for product in products:
        candidates = search_prices(product, db_path=db_path, limit=20)
        candidates_by_product[product] = candidates
        priced = [item for item in candidates if item.get("best_general_price") is not None]
        if not priced:
            chosen_split.append({"query": product, "status": "missing", "candidate": None})
            continue
        best = sorted(priced, key=lambda item: item["best_general_price"])[0]
        chosen_split.append({"query": product, "status": "ok", "candidate": best})
        totals_by_chain[best.get("chain") or "Sin cadena"] += float(best["best_general_price"])

    unified_totals = {}
    chains = sorted({item.get("chain") for values in candidates_by_product.values() for item in values if item.get("chain")})
    for chain in chains:
        total = 0.0
        complete = True
        picks = []
        for product, candidates in candidates_by_product.items():
            chain_candidates = [item for item in candidates if item.get("chain") == chain and item.get("best_general_price") is not None]
            if not chain_candidates:
                complete = False
                break
            best = sorted(chain_candidates, key=lambda item: item["best_general_price"])[0]
            total += float(best["best_general_price"])
            picks.append(best)
        if complete:
            unified_totals[chain] = {"total": round(total, 2), "items": picks}

    split_total = round(sum(totals_by_chain.values()), 2)
    best_unified = None
    if unified_totals:
        best_chain = min(unified_totals, key=lambda key: unified_totals[key]["total"])
        best_unified = {"chain": best_chain, **unified_totals[best_chain]}
    savings = None
    if best_unified:
        savings = round(best_unified["total"] - split_total, 2)

    return {
        "split_purchase": split_purchase,
        "split_total": split_total,
        "split_items": chosen_split,
        "split_totals_by_chain": dict(totals_by_chain),
        "best_unified": best_unified,
        "estimated_savings_split_vs_unified": savings,
    }

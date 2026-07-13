from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cloud_backend.app.config import Settings
from cloud_backend.app.sources.vea import VeaSource


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test controlado de la fuente piloto Vea.")
    parser.add_argument("--live", action="store_true", help="Consulta real minima. Por defecto usa fixture local.")
    parser.add_argument("--max-products", type=int, default=3)
    parser.add_argument("--max-pages", type=int, default=1)
    args = parser.parse_args()
    if not 1 <= args.max_products <= 10 or args.max_pages != 1:
        parser.error("Smoke test limitado a 1 pagina y entre 1 y 10 productos")
    settings = Settings.from_env()
    settings = Settings(
        **{
            **settings.__dict__,
            "source_mode": "live" if args.live else "fixture",
            "max_products_per_run": 10,
            "max_pages_per_run": 1,
        }
    )
    source = VeaSource(settings)
    try:
        rows, incidents = source.fetch_catalog(args.max_products, args.max_pages)
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))
        return 1
    summary = {
        "status": "OK" if rows else "EMPTY",
        "mode": settings.source_mode,
        "dry_run": True,
        "published": False,
        "products": len(rows),
        "incidents": incidents,
        "sample": [{"producto": row["producto"], "precio_efectivo": row["precio_efectivo"]} for row in rows[:3]],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if rows else 2


if __name__ == "__main__":
    raise SystemExit(main())

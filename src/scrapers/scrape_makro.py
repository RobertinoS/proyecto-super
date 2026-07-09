from __future__ import annotations

from scrapers.catalogs import run_catalog_links


def run():
    run_catalog_links("makro")
    return []


if __name__ == "__main__":
    print(f"records={len(run())}")

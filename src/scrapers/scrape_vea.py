from __future__ import annotations

from scrapers.vtex import run_vtex_paths


def run():
    return run_vtex_paths("vea", ["almacen", "bebidas", "carnes", "lacteos", "limpieza"], max_pages=3)


if __name__ == "__main__":
    print(f"records={len(run())}")

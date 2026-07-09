from __future__ import annotations

from scrapers.vtex import run_vtex_clusters


def run():
    return run_vtex_clusters(
        "masonline",
        {
            "Almacen": "268",
            "Bebidas": "3433",
            "Carnes": "3431",
            "Lacteos": "3432",
            "Limpieza": "272",
        },
        max_pages=3,
    )


if __name__ == "__main__":
    print(f"records={len(run())}")

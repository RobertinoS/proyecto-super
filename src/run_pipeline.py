from __future__ import annotations

import argparse
import importlib
import os
from pathlib import Path

from database import finish_run, init_database, insert_price_rows, start_run
from export_dashboard import export_dashboard
from source_discovery import run_discovery

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    def load_dotenv(*args, **kwargs):
        return False


SCRAPER_MODULES = {
    "vea": "scrapers.scrape_vea",
    "carrefour": "scrapers.scrape_carrefour",
    "masonline": "scrapers.scrape_masonline",
    "atomo": "scrapers.scrape_atomo",
    "laanonima": "scrapers.scrape_laanonima",
    "cabral": "scrapers.scrape_cabral",
    "la_cumbre": "scrapers.scrape_la_cumbre",
    "yaguar": "scrapers.scrape_yaguar",
    "makro": "scrapers.scrape_makro",
    "cafe_america": "scrapers.scrape_cafe_america",
    "la_nobleza": "scrapers.scrape_la_nobleza",
    "la_estrella": "scrapers.scrape_la_estrella",
    "basualdo": "scrapers.scrape_basualdo",
    "maxiconsumo": "scrapers.scrape_maxiconsumo",
}


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def setup_environment(root: Path) -> tuple[Path, Path]:
    load_dotenv(root / ".env")
    db_path = root / os.getenv("DATABASE_PATH", "database/precios_san_juan.sqlite")
    export_dir = root / os.getenv("EXPORT_DIR", "data/export")
    return db_path, export_dir


def run_init(root: Path, db_path: Path) -> None:
    conn = init_database(db_path, root / "config" / "fuentes.yml")
    conn.close()
    print("Base lista. Fuentes oficiales inicializadas.")


def run_discover(root: Path) -> None:
    results = run_discovery(
        root / "config" / "fuentes.yml",
        root / "data" / "processed" / "source_discovery.csv",
        root / "docs" / "SOURCE_DISCOVERY.md",
        timeout=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30")),
        user_agent=os.getenv("SCRAPER_USER_AGENT", "Mozilla/5.0 ComparadorPreciosSanJuan/1.0"),
    )
    print(f"Descubrimiento terminado. URLs revisadas: {len(results)}")


def run_scraper(name: str, db_path: Path) -> None:
    names = list(SCRAPER_MODULES) if name == "all" else [name]
    unknown = [item for item in names if item not in SCRAPER_MODULES]
    if unknown:
        raise SystemExit(f"Scraper desconocido: {', '.join(unknown)}")
    conn = init_database(db_path)
    for scraper_name in names:
        run_id = start_run(conn, scraper_name)
        try:
            module = importlib.import_module(SCRAPER_MODULES[scraper_name])
            records = module.run()
            saved = insert_price_rows(conn, records)
            finish_run(conn, run_id, "ok", records_found=len(records), records_saved=saved)
            print(f"Scraper {scraper_name}: records={len(records)} saved={saved}")
        except Exception as exc:
            finish_run(conn, run_id, "error", errors_count=1, error_summary=f"{type(exc).__name__}: {exc}")
            print(f"Scraper {scraper_name}: ERROR {type(exc).__name__}: {exc}")
    conn.close()


def run_export(root: Path, db_path: Path, export_dir: Path) -> None:
    result = export_dashboard(db_path, export_dir)
    print(f"Export JSON: {result}")


def run_all(root: Path, db_path: Path, export_dir: Path) -> None:
    run_init(root, db_path)
    run_discover(root)
    run_scraper("all", db_path)
    run_export(root, db_path, export_dir)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Init DB, discovery, scrapers oficiales y export.")
    parser.add_argument("--init-db", action="store_true", help="Crea SQLite e inicializa fuentes oficiales.")
    parser.add_argument("--discover", action="store_true", help="Revisa URLs de config/fuentes.yml.")
    parser.add_argument("--scrape", choices=["all", *SCRAPER_MODULES.keys()], help="Ejecuta un scraper diagnostico.")
    parser.add_argument("--export", action="store_true", help="Exporta JSON para dashboard.")
    args = parser.parse_args()

    root = project_root()
    os.chdir(root)
    db_path, export_dir = setup_environment(root)

    if args.all:
        run_all(root, db_path, export_dir)
    else:
        if args.init_db:
            run_init(root, db_path)
        if args.discover:
            run_discover(root)
        if args.scrape:
            run_scraper(args.scrape, db_path)
        if args.export:
            run_export(root, db_path, export_dir)
    if not any(vars(args).values()):
        parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

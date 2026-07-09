from __future__ import annotations

from scrapers.atomo import run_atomo


def run():
    return run_atomo(max_pages=3)


if __name__ == "__main__":
    print(f"records={len(run())}")

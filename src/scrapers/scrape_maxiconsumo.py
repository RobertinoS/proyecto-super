from __future__ import annotations

from scrapers.maxiconsumo import run_maxiconsumo


def run():
    return run_maxiconsumo()


if __name__ == "__main__":
    print(f"records={len(run())}")

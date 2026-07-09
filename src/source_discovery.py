from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None


KEYWORDS = [
    "precio",
    "$",
    "oferta",
    "ofertas",
    "sucursal",
    "carrito",
    "stock",
    "promocion",
    "catalogo",
    "folleto",
    "tienda",
    "whatsapp",
    "instagram",
    "facebook",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_sources(config_path: Path) -> list[dict[str, Any]]:
    if yaml is None:
        raise RuntimeError("PyYAML no esta instalado. Ejecuta pip install -r requirements.txt")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return list(data.get("sources", []))


def inspect_url(url: str, timeout: int, user_agent: str) -> dict[str, Any]:
    headers = {"User-Agent": user_agent}
    started = utc_now()
    try:
        response = requests.get(url, timeout=timeout, headers=headers, allow_redirects=True)
        text = response.text[:500000]
        soup = BeautifulSoup(text, "lxml")
        visible_text = soup.get_text(" ", strip=True).lower()
        scripts_text = " ".join(script.get_text(" ", strip=True) for script in soup.find_all("script"))[:200000].lower()
        combined = f"{visible_text} {scripts_text}"
        found = [keyword for keyword in KEYWORDS if keyword in combined]
        json_ld_count = len(soup.find_all("script", attrs={"type": "application/ld+json"}))
        return {
            "checked_at": started,
            "url": url,
            "status_code": response.status_code,
            "final_url": response.url,
            "content_type": response.headers.get("content-type", ""),
            "bytes": len(response.content),
            "html_title": soup.title.get_text(" ", strip=True) if soup.title else "",
            "has_useful_html": bool(visible_text and len(visible_text) > 200),
            "json_ld_count": json_ld_count,
            "keyword_hits": "|".join(found),
            "requires_js_signal": "window.__" in text or "__NEXT_DATA__" in text or "vtex" in combined,
            "error": "",
        }
    except Exception as exc:
        return {
            "checked_at": started,
            "url": url,
            "status_code": None,
            "final_url": "",
            "content_type": "",
            "bytes": 0,
            "html_title": "",
            "has_useful_html": False,
            "json_ld_count": 0,
            "keyword_hits": "",
            "requires_js_signal": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def run_discovery(
    config_path: str | Path = "config/fuentes.yml",
    output_csv: str | Path = "data/processed/source_discovery.csv",
    output_md: str | Path = "docs/SOURCE_DISCOVERY.md",
    timeout: int = 30,
    user_agent: str = "Mozilla/5.0 ComparadorPreciosSanJuan/1.0",
) -> list[dict[str, Any]]:
    sources = load_sources(Path(config_path))
    results = []
    for source in sources:
        for url_type in ("base_url", "offers_url"):
            url = source.get(url_type)
            if not url:
                continue
            result = inspect_url(url, timeout, user_agent)
            result.update(
                {
                    "source_id": source.get("source_id"),
                    "name": source.get("name"),
                    "url_type": url_type,
                    "configured_requires_js": source.get("requires_js"),
                    "configured_requires_location": source.get("requires_location"),
                }
            )
            results.append(result)
    out = Path(output_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    if results:
        with out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(results[0].keys()))
            writer.writeheader()
            writer.writerows(results)
    write_markdown(results, Path(output_md))
    return results


def write_markdown(results: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Descubrimiento tecnico de fuentes",
        "",
        f"Generado: {utc_now()}",
        "",
        "| Fuente | URL | HTTP | HTML util | Keywords | JS senal | Error |",
        "|---|---|---:|---:|---|---:|---|",
    ]
    for item in results:
        lines.append(
            f"| {item.get('name')} | {item.get('url')} | {item.get('status_code') or ''} | "
            f"{item.get('has_useful_html')} | {item.get('keyword_hits')} | {item.get('requires_js_signal')} | "
            f"{str(item.get('error') or '').replace('|', '/')} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/fuentes.yml")
    parser.add_argument("--output", default="data/processed/source_discovery.csv")
    parser.add_argument("--report", default="docs/SOURCE_DISCOVERY.md")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()
    results = run_discovery(args.config, args.output, args.report, timeout=args.timeout)
    print(f"Fuentes revisadas: {len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from datetime import datetime
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, load_source_config


CATALOG_TARGETS = {
    "makro": ["https://makro.com.ar/ofertas/san-juan/"],
    "yaguar": ["https://yaguar.com.ar/san-juan/catalogos-y-ofertas/", "https://yaguar.com.ar/catalogos/"],
    "laanonima": ["https://www.laanonima.com.ar/empresa/catalogos", "https://www.laanonima.com.ar/empresa/sucursales/381-san-juan"],
    "cafe_america": ["https://www.americamayorista.com/", "https://www.americamayorista.com/ofertasimperdibles"],
    "cabral": ["https://cabralmayorista.com/", "https://cabralmayorista.com/sucursales/"],
    "la_cumbre": ["https://lacumbresanjuanina.com.ar/"],
    "la_nobleza": ["https://www.instagram.com/lanoblezamayorista/", "https://www.facebook.com/lanoblezamayorista/"],
    "la_estrella": ["https://www.instagram.com/laestrellamayorista.ar/", "https://www.facebook.com/p/La-Estrella-Mayorista-61560457916462/"],
    "basualdo": ["https://linktr.ee/basualdomayorista"],
}


class CatalogScraper(BaseScraper):
    EXCLUDE_TERMS = (
        "#content",
        "elementor-action",
        "carrito#",
        "info.pdf",
        "cybermonday",
        "/login/",
        "/auth/login",
        "#descubri-premios",
        "/features/",
        "link-in-bio",
        "social-planner",
        "cookie",
        "privacy",
        "report",
        "trabaja",
        "trabajo",
        "acceso comerciantes",
        "marcas propias",
        "tienda de puntos",
        "inicio",
        "caba",
        "gba",
        "parque chacabuco",
        "preguntas",
        "defensa",
        "receta",
        "gift-card",
        "contacto",
        "conoce",
        "nosotros",
        "tasas",
        "quejas",
        "opiniones",
    )
    INCLUDE_TERMS = (
        ".pdf",
        "catalog",
        "oferta",
        "promo",
        "folleto",
        "ofertas/san-juan",
        "ofertasimperdibles",
        "catalogos-y-ofertas",
        "promociones-bancarias",
        "sucursal",
        "san-juan",
        "tienda",
    )

    def is_relevant_link(self, text: str, href: str) -> bool:
        low = f"{text} {href}".lower()
        if any(term in low for term in self.EXCLUDE_TERMS):
            return False
        if self.config.source_id == "basualdo":
            return (
                "drive.google.com" in low
                or "instagram.com/mayorista.basualdo" in low
                or "facebook.com/mayoristabasualdo" in low
            )
        if "linktr.ee/" in low and self.config.source_id != "basualdo":
            return False
        if any(term in low for term in self.INCLUDE_TERMS):
            return True
        return (
            "instagram.com" in low
            or "facebook.com" in low
            or "whatsapp.com/channel" in low
            or "wa.me/" in low
        )

    def discover_links(self, url: str) -> list[dict]:
        response = self.fetch(url)
        self.save_raw(f"catalog_{self.config.source_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html", response.text)
        soup = BeautifulSoup(response.text, "lxml")
        links = []
        for anchor in soup.find_all("a", href=True):
            text = anchor.get_text(" ", strip=True)
            href = urljoin(response.url, anchor["href"])
            if self.is_relevant_link(text, href):
                title = text or href.rsplit("/", 1)[-1]
                if len(title) > 140:
                    title = title[:137] + "..."
                links.append(
                    {
                        "capture_date": datetime.now().date().isoformat(),
                        "source_id": self.config.source_id,
                        "chain": self.config.name,
                        "title": title,
                        "url": href,
                        "source_type": "official_catalog_link",
                        "confidence_score": min(self.config.confidence_score, 85),
                    }
                )
        return dedupe_links(links)


def dedupe_links(rows: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for row in rows:
        key = row["url"]
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def run_catalog_links(source_id: str) -> list[dict]:
    scraper = CatalogScraper(load_source_config(source_id))
    rows = []
    for url in CATALOG_TARGETS[source_id]:
        if is_social_target(url):
            rows.append(make_link_row(scraper, url))
        else:
            rows.extend(scraper.discover_links(url))
    rows = dedupe_links(rows)
    path = scraper.processed_dir / f"{source_id}_catalog_links.csv"
    if rows:
        import pandas as pd

        pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8")
    else:
        path.write_text("", encoding="utf-8")
    return rows


def is_social_target(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return "instagram.com" in host or "facebook.com" in host


def make_link_row(scraper: CatalogScraper, url: str) -> dict:
    host = urlparse(url).netloc.lower()
    if "instagram" in host:
        title = "Instagram oficial"
    elif "facebook" in host:
        title = "Facebook oficial"
    else:
        title = "Canal oficial"
    return {
        "capture_date": datetime.now().date().isoformat(),
        "source_id": scraper.config.source_id,
        "chain": scraper.config.name,
        "title": title,
        "url": url,
        "source_type": "official_social_link",
        "confidence_score": min(scraper.config.confidence_score, 75),
    }

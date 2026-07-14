from __future__ import annotations

import os
from dataclasses import dataclass


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _bool_env(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "si"}


@dataclass(frozen=True)
class Settings:
    app_env: str = "local"
    app_version: str = "1.6.0"
    scraper_api_key: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    raw_bucket: str = "raw-price-snapshots"
    processed_bucket: str = "processed-price-datasets"
    published_bucket: str = "published-price-datasets"
    request_timeout_seconds: int = 120
    request_delay_seconds: float = 2.0
    max_products_per_run: int = 5
    max_pages_per_run: int = 1
    log_level: str = "INFO"
    source_mode: str = "fixture"
    enable_publication: bool = False
    build_sha: str = "local"

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_env=os.getenv("APP_ENV", "local"),
            app_version=os.getenv("APP_VERSION", "1.6.0"),
            scraper_api_key=os.getenv("SCRAPER_API_KEY", ""),
            supabase_url=os.getenv("SUPABASE_URL", "").rstrip("/"),
            supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
            raw_bucket=os.getenv("RAW_BUCKET", "raw-price-snapshots"),
            processed_bucket=os.getenv("PROCESSED_BUCKET", "processed-price-datasets"),
            published_bucket=os.getenv("PUBLISHED_BUCKET", "published-price-datasets"),
            request_timeout_seconds=max(1, _int_env("REQUEST_TIMEOUT_SECONDS", 120)),
            request_delay_seconds=max(0.0, _float_env("REQUEST_DELAY_SECONDS", 2.0)),
            max_products_per_run=max(1, _int_env("MAX_PRODUCTS_PER_RUN", 5)),
            max_pages_per_run=max(1, _int_env("MAX_PAGES_PER_RUN", 1)),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            source_mode=os.getenv("SOURCE_MODE", "fixture").lower(),
            enable_publication=_bool_env("ENABLE_PUBLICATION", False),
            build_sha=os.getenv("RENDER_GIT_COMMIT", os.getenv("BUILD_SHA", "local")),
        )

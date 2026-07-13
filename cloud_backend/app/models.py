from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ScrapeJobRequest(BaseModel):
    source: str = "vea"
    dry_run: bool = True
    max_products: int = Field(default=25, ge=1, le=500)
    max_pages: int = Field(default=1, ge=1, le=10)
    execution_id: str | None = Field(default=None, max_length=120)
    trigger_type: Literal["manual", "github_actions", "n8n", "smoke_test"] = "manual"


class RunSummary(BaseModel):
    run_id: str
    execution_id: str
    source: str
    status: str
    products_read: int = 0
    products_valid: int = 0
    products_invalid: int = 0
    incidents: int = 0
    started_at: datetime
    finished_at: datetime | None = None
    error_summary: str | None = None
    duplicate_execution: bool = False


class ProcessRequest(BaseModel):
    run_id: str
    dry_run: bool = True
    max_invalid_pct: float = Field(default=10.0, ge=0.0, le=100.0)


class ProcessResponse(BaseModel):
    run_id: str
    status: str
    rows_processed: int
    rows_invalid: int
    quality_score: float
    incidents: list[str]
    approval_required: bool = True


class PublishRequest(BaseModel):
    run_id: str
    approved: bool = False
    approved_by: str | None = Field(default=None, max_length=120)
    dry_run: bool = True


class PublishResponse(BaseModel):
    run_id: str
    status: str
    dataset_path: str | None = None
    rows_published: int = 0
    dry_run: bool = True


class SourceInfo(BaseModel):
    name: str
    version: str
    status: str
    mode: str
    last_run: dict[str, Any] | None = None

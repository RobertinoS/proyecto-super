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
    trigger_type: Literal["manual", "manual_staging", "github_actions", "n8n", "smoke_test"] = "manual"


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


class ReviewDecisionRequest(BaseModel):
    actor: str = Field(min_length=2, max_length=120)
    notes: str | None = Field(default=None, max_length=2000)
    corrected_value: dict[str, Any] | None = None
    idempotency_key: str | None = Field(default=None, max_length=160)


class DatasetApprovalRequest(BaseModel):
    actor: str = Field(min_length=2, max_length=120)
    reason: str | None = Field(default=None, max_length=2000)
    idempotency_key: str | None = Field(default=None, max_length=160)


class PrivatePublicationRequest(BaseModel):
    actor: str = Field(min_length=2, max_length=120)
    dry_run: bool = True
    idempotency_key: str | None = Field(default=None, max_length=160)


class OperationalAlertRequest(BaseModel):
    source: str | None = Field(default=None, max_length=80)
    run_id: str | None = Field(default=None, max_length=80)
    alert_type: str = Field(min_length=3, max_length=120)
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "HIGH"
    message: str = Field(min_length=3, max_length=1000)
    idempotency_key: str | None = Field(default=None, max_length=160)


class SourceInfo(BaseModel):
    name: str
    version: str
    status: str
    mode: str
    last_run: dict[str, Any] | None = None


class AuthMeResponse(BaseModel):
    user_id: str
    roles: list[Literal["viewer", "reviewer", "dataset_admin", "operator"]]
    capabilities: list[str]
    token_expires_at: datetime
    authentication_type: Literal["supabase_jwt"]


class AuthCapabilitiesResponse(BaseModel):
    roles: list[Literal["viewer", "reviewer", "dataset_admin", "operator"]]
    capabilities: list[str]


# Contracts reserved for Sprint 17B. They are documented but are not routes or
# download implementations in Sprint 17A.
class FuturePrivateDatasetMetadata(BaseModel):
    dataset_id: str
    status: Literal["APPROVED", "PUBLISHED_PRIVATE", "REVOKED", "SUPERSEDED", "ARCHIVED"]
    run_id: str
    row_count: int = Field(ge=0)
    quality_score: float | None = Field(default=None, ge=0, le=100)
    created_at: datetime


class FutureDatasetAccessRequest(BaseModel):
    request_id: str = Field(min_length=8, max_length=160)


class FutureDatasetAccessResponse(BaseModel):
    dataset_id: str
    status: Literal["PENDING", "GRANTED", "DENIED"]
    expires_at: datetime | None = None

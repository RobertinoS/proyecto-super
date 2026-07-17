from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query

from .config import Settings
from .dependencies import (
    get_pipeline_service,
    get_private_publication_service,
    get_publication_service,
    get_review_service,
    get_run_service,
)
from .models import (
    DatasetApprovalRequest,
    OperationalAlertRequest,
    PrivatePublicationRequest,
    ProcessRequest,
    ProcessResponse,
    PublishRequest,
    PublishResponse,
    ReviewDecisionRequest,
    RunSummary,
    ScrapeJobRequest,
    SourceInfo,
)
from .security import require_api_key
from .services.pipeline_service import PipelineService
from .services.private_publication_service import PrivatePublicationError, PrivatePublicationService
from .services.publication_service import PublicationError, PublicationService
from .services.review_service import ReviewError, ReviewService
from .services.run_service import RunService
from .services.supabase_service import SupabaseService
from .sources.vea import VeaSource


def create_app(settings: Settings | None = None, sources: dict | None = None) -> FastAPI:
    config = settings or Settings.from_env()
    logging.basicConfig(level=getattr(logging, config.log_level, logging.INFO), format="%(asctime)s %(levelname)s %(name)s %(message)s")
    app = FastAPI(title="Proyecto Super Cloud API", version=config.app_version)
    app.state.settings = config
    app.state.started_monotonic = time.monotonic()
    app.state.supabase_service = SupabaseService(config)
    app.state.sources = sources or {"vea": VeaSource(config)}
    app.state.run_service = RunService(app.state.sources, app.state.supabase_service)
    app.state.pipeline_service = PipelineService(app.state.run_service)
    app.state.publication_service = PublicationService(config, app.state.run_service, app.state.supabase_service)
    app.state.review_service = ReviewService(app.state.run_service, app.state.supabase_service)
    app.state.private_publication_service = PrivatePublicationService(
        config,
        app.state.run_service,
        app.state.review_service,
        app.state.supabase_service,
    )

    @app.get("/health")
    def health() -> dict:
        staging_ready = config.app_env != "staging" or config.supabase_configured
        return {
            "status": "ok" if staging_ready else "degraded",
            "app_version": config.app_version,
            "environment": config.app_env,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "supabase_configured": config.supabase_configured,
            "staging_ready": staging_ready,
            "available_sources": sorted(app.state.sources),
            "uptime": round(time.monotonic() - app.state.started_monotonic, 3),
            "build_info": {"sha": config.build_sha, "source_mode": config.source_mode},
        }

    @app.get("/sources", response_model=list[SourceInfo])
    def list_sources() -> list[SourceInfo]:
        result = []
        for name, source in app.state.sources.items():
            last = app.state.run_service.last_for_source(name)
            health_data = source.health_check()
            result.append(
                SourceInfo(
                    name=name,
                    version=source.source_version,
                    status=health_data.get("status", "unknown"),
                    mode=config.source_mode,
                    last_run=last.model_dump(mode="json") if last else None,
                )
            )
        return result

    @app.post("/jobs/scrape", response_model=RunSummary, dependencies=[Depends(require_api_key)])
    def scrape_job(payload: ScrapeJobRequest, runs: RunService = Depends(get_run_service)) -> RunSummary:
        try:
            return runs.execute(payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/jobs/{run_id}", response_model=RunSummary, dependencies=[Depends(require_api_key)])
    def get_job(run_id: str, runs: RunService = Depends(get_run_service)) -> RunSummary:
        record = runs.get(run_id)
        if not record:
            raise HTTPException(status_code=404, detail="Run no encontrado")
        return record["summary"]

    @app.post("/pipeline/process", response_model=ProcessResponse, dependencies=[Depends(require_api_key)])
    def process_pipeline(payload: ProcessRequest, pipeline: PipelineService = Depends(get_pipeline_service)) -> ProcessResponse:
        try:
            return pipeline.process(payload.run_id, payload.max_invalid_pct, payload.dry_run)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Run no encontrado") from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.post("/pipeline/publish", response_model=PublishResponse, dependencies=[Depends(require_api_key)])
    def publish_pipeline(payload: PublishRequest, publication: PublicationService = Depends(get_publication_service)) -> PublishResponse:
        try:
            return publication.publish(payload.run_id, payload.approved, payload.approved_by, payload.dry_run)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Run no encontrado") from exc
        except PublicationError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/reviews", dependencies=[Depends(require_api_key)])
    def list_reviews(
        status: str | None = Query(default=None),
        severity: str | None = Query(default=None),
        source: str | None = Query(default=None),
        run_id: str | None = Query(default=None),
        review_type: str | None = Query(default=None),
        reviews: ReviewService = Depends(get_review_service),
    ) -> list[dict]:
        return reviews.list_reviews(status, severity, source, run_id, review_type)

    @app.get("/reviews/{review_id}", dependencies=[Depends(require_api_key)])
    def get_review(review_id: str, reviews: ReviewService = Depends(get_review_service)) -> dict:
        review = reviews.get_review(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Revision no encontrada")
        return review

    def _decide_review(review_id: str, action: str, payload: ReviewDecisionRequest, reviews: ReviewService) -> dict:
        try:
            return reviews.decide_review(
                review_id,
                action,
                payload.actor,
                payload.notes,
                payload.corrected_value,
                payload.idempotency_key,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Revision no encontrada") from exc
        except ReviewError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/reviews/{review_id}/approve", dependencies=[Depends(require_api_key)])
    def approve_review(review_id: str, payload: ReviewDecisionRequest, reviews: ReviewService = Depends(get_review_service)) -> dict:
        return _decide_review(review_id, "approve", payload, reviews)

    @app.post("/reviews/{review_id}/reject", dependencies=[Depends(require_api_key)])
    def reject_review(review_id: str, payload: ReviewDecisionRequest, reviews: ReviewService = Depends(get_review_service)) -> dict:
        return _decide_review(review_id, "reject", payload, reviews)

    @app.post("/reviews/{review_id}/correct", dependencies=[Depends(require_api_key)])
    def correct_review(review_id: str, payload: ReviewDecisionRequest, reviews: ReviewService = Depends(get_review_service)) -> dict:
        return _decide_review(review_id, "correct", payload, reviews)

    @app.post("/reviews/{review_id}/dismiss", dependencies=[Depends(require_api_key)])
    def dismiss_review(review_id: str, payload: ReviewDecisionRequest, reviews: ReviewService = Depends(get_review_service)) -> dict:
        return _decide_review(review_id, "dismiss", payload, reviews)

    @app.post("/runs/{run_id}/request-approval", dependencies=[Depends(require_api_key)])
    def request_dataset_approval(
        run_id: str,
        payload: DatasetApprovalRequest,
        reviews: ReviewService = Depends(get_review_service),
    ) -> dict:
        try:
            return reviews.request_approval(run_id, payload.actor, payload.idempotency_key)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Ejecucion no encontrada") from exc

    @app.get("/runs/{run_id}/approval-status", dependencies=[Depends(require_api_key)])
    def dataset_approval_status(run_id: str, reviews: ReviewService = Depends(get_review_service)) -> dict:
        approval = reviews.approval_status(run_id)
        if not approval:
            raise HTTPException(status_code=404, detail="Solicitud de aprobacion no encontrada")
        return approval

    @app.post("/runs/{run_id}/approve-dataset", dependencies=[Depends(require_api_key)])
    def approve_dataset(run_id: str, payload: DatasetApprovalRequest, reviews: ReviewService = Depends(get_review_service)) -> dict:
        try:
            return reviews.approve_dataset(run_id, payload.actor, payload.idempotency_key)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Ejecucion no encontrada") from exc
        except ReviewError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/runs/{run_id}/reject-dataset", dependencies=[Depends(require_api_key)])
    def reject_dataset(run_id: str, payload: DatasetApprovalRequest, reviews: ReviewService = Depends(get_review_service)) -> dict:
        try:
            return reviews.reject_dataset(run_id, payload.actor, payload.reason or "", payload.idempotency_key)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Ejecucion no encontrada") from exc
        except ReviewError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/runs/{run_id}/private-publish", dependencies=[Depends(require_api_key)])
    def private_publish(
        run_id: str,
        payload: PrivatePublicationRequest,
        publication: PrivatePublicationService = Depends(get_private_publication_service),
    ) -> dict:
        try:
            return publication.publish(run_id, payload.actor, payload.dry_run)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Ejecucion no encontrada") from exc
        except PrivatePublicationError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/datasets/latest-approved", dependencies=[Depends(require_api_key)])
    def latest_approved_dataset(publication: PrivatePublicationService = Depends(get_private_publication_service)) -> dict:
        dataset = publication.latest()
        if not dataset:
            raise HTTPException(status_code=404, detail="No hay dataset privado aprobado")
        return dataset

    @app.get("/datasets/{dataset_id}", dependencies=[Depends(require_api_key)])
    def get_dataset(dataset_id: str, publication: PrivatePublicationService = Depends(get_private_publication_service)) -> dict:
        dataset = publication.get(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset no encontrado")
        return dataset

    @app.get("/datasets/{dataset_id}/download-url", dependencies=[Depends(require_api_key)])
    def dataset_download_url(dataset_id: str, publication: PrivatePublicationService = Depends(get_private_publication_service)) -> dict:
        try:
            return publication.download_url(dataset_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Dataset no encontrado") from exc
        except PrivatePublicationError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/operations/summary", dependencies=[Depends(require_api_key)])
    def operations_summary(reviews: ReviewService = Depends(get_review_service)) -> dict:
        return reviews.operations_summary()

    @app.get("/operations/sources", dependencies=[Depends(require_api_key)])
    def operations_sources(reviews: ReviewService = Depends(get_review_service)) -> list[dict]:
        return reviews.operations_sources()

    @app.get("/operations/alerts", dependencies=[Depends(require_api_key)])
    def operations_alerts(reviews: ReviewService = Depends(get_review_service)) -> list[dict]:
        return reviews.list_alerts()

    @app.post("/operations/alerts", dependencies=[Depends(require_api_key)])
    def create_operational_alert(payload: OperationalAlertRequest, reviews: ReviewService = Depends(get_review_service)) -> dict:
        return reviews.create_alert(
            payload.source,
            payload.run_id,
            payload.alert_type,
            payload.severity,
            payload.message,
            idempotency_key=payload.idempotency_key,
        )

    @app.post("/operations/alerts/{alert_id}/acknowledge", dependencies=[Depends(require_api_key)])
    def acknowledge_alert(alert_id: str, payload: DatasetApprovalRequest, reviews: ReviewService = Depends(get_review_service)) -> dict:
        try:
            return reviews.acknowledge_alert(alert_id, payload.actor)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Alerta no encontrada") from exc

    return app


app = create_app()

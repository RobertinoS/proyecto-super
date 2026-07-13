from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException

from .config import Settings
from .dependencies import get_pipeline_service, get_publication_service, get_run_service
from .models import ProcessRequest, ProcessResponse, PublishRequest, PublishResponse, RunSummary, ScrapeJobRequest, SourceInfo
from .security import require_api_key
from .services.pipeline_service import PipelineService
from .services.publication_service import PublicationError, PublicationService
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

    @app.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "app_version": config.app_version,
            "environment": config.app_env,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "supabase_configured": config.supabase_configured,
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

    return app


app = create_app()

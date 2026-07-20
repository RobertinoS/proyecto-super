from __future__ import annotations

from fastapi import Request


def get_run_service(request: Request):
    return request.app.state.run_service


def get_pipeline_service(request: Request):
    return request.app.state.pipeline_service


def get_publication_service(request: Request):
    return request.app.state.publication_service


def get_review_service(request: Request):
    return request.app.state.review_service


def get_private_publication_service(request: Request):
    return request.app.state.private_publication_service


def get_role_service(request: Request):
    return request.app.state.role_service


def get_internal_dataset_access_service(request: Request):
    return request.app.state.internal_dataset_access_service

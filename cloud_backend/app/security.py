from __future__ import annotations

import secrets
import uuid

from fastapi import Depends, Header, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .services.auth_service import CurrentUser, JwtConfigurationError, JwtValidationError


def require_api_key(request: Request, x_api_key: str | None = Header(default=None)) -> None:
    expected = request.app.state.settings.scraper_api_key
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Falta el header X-API-Key")
    if not expected:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Autenticacion no configurada")
    if not secrets.compare_digest(x_api_key.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="X-API-Key invalida")


# Explicit name for new code. The alias preserves the established n8n/GitHub
# dependency name and prevents a JWT from silently replacing machine auth.
require_service_api_key = require_api_key

_bearer_scheme = HTTPBearer(auto_error=False)


def _request_id(request: Request) -> str:
    supplied = request.headers.get("X-Request-ID", "").strip()
    if 8 <= len(supplied) <= 160 and all(char.isalnum() or char in {"-", "_", "."} for char in supplied):
        return supplied
    return str(uuid.uuid4())


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de usuario requerido")
    try:
        identity = request.app.state.jwt_validator.validate(credentials.credentials)
    except JwtConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Autenticacion de usuarios no configurada") from exc
    except JwtValidationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de usuario invalido") from exc

    role_service = request.app.state.role_service
    roles = role_service.get_active_roles(identity.user_id)
    request_id = _request_id(request)
    role_service.audit(
        user_id=identity.user_id,
        action="AUTHENTICATED",
        result="ALLOWED",
        request_id=request_id,
        roles=roles,
    )
    return CurrentUser(
        user_id=identity.user_id,
        roles=roles,
        capabilities=role_service.capabilities_for(roles),
        token_expires_at=identity.token_expires_at,
        request_id=request_id,
    )


require_authenticated_user = get_current_user


def require_any_role(*required_roles: str):
    expected = frozenset(required_roles)

    def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not expected.intersection(current_user.roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes")
        return current_user

    return dependency


def require_all_roles(*required_roles: str):
    expected = frozenset(required_roles)

    def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not expected.issubset(current_user.roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes")
        return current_user

    return dependency


def require_distinct_actors(first_actor_id: str, second_actor_id: str) -> None:
    """Contract guard reserved for two-person restore approval in Sprint 17C."""
    if first_actor_id == second_actor_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Se requieren dos responsables distintos")

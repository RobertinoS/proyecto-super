from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

import jwt
import requests

from ..config import Settings
from .supabase_service import SupabaseService


VALID_ROLES = frozenset({"viewer", "reviewer", "dataset_admin", "operator"})
ROLE_CAPABILITIES = {
    "viewer": frozenset({"dataset.metadata.read", "dataset.access.request"}),
    "reviewer": frozenset({"dataset.metadata.read", "dataset.access.request", "review.decide", "dataset.restore.participate"}),
    "dataset_admin": frozenset({"dataset.metadata.read", "dataset.access.request", "dataset.activate", "dataset.revoke", "role.assignment.manage"}),
    "operator": frozenset({"operations.read", "live.window.request"}),
}


class JwtValidationError(Exception):
    """Safe error raised when a human JWT cannot be accepted."""


class JwtConfigurationError(Exception):
    """Safe error raised when the server lacks the public JWT configuration."""


@dataclass(frozen=True)
class AuthenticatedIdentity:
    user_id: str
    token_expires_at: datetime
    authentication_type: str = "supabase_jwt"


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    roles: tuple[str, ...]
    capabilities: tuple[str, ...]
    token_expires_at: datetime
    request_id: str
    authentication_type: str = "supabase_jwt"


def _default_jwks_fetcher(url: str, timeout_seconds: int) -> dict[str, Any]:
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("JWKS response must be an object")
    return payload


class JwksCache:
    """Small in-memory JWKS cache with one refresh on an unknown key ID."""

    def __init__(
        self,
        settings: Settings,
        fetcher: Callable[[str, int], dict[str, Any]] | None = None,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.settings = settings
        self.fetcher = fetcher or _default_jwks_fetcher
        self.monotonic = monotonic
        self._keys: dict[str, dict[str, Any]] = {}
        self._expires_at = 0.0
        self._lock = threading.Lock()

    def _refresh(self, force: bool = False) -> None:
        if not self.settings.supabase_auth_jwks_url:
            raise JwtConfigurationError("JWKS URL is not configured")
        now = self.monotonic()
        with self._lock:
            if not force and self._keys and now < self._expires_at:
                return
            try:
                document = self.fetcher(self.settings.supabase_auth_jwks_url, self.settings.request_timeout_seconds)
                keys = document.get("keys") if isinstance(document, dict) else None
                if not isinstance(keys, list):
                    raise ValueError("JWKS does not contain keys")
                parsed = {str(item["kid"]): item for item in keys if isinstance(item, dict) and item.get("kid")}
                if not parsed:
                    raise ValueError("JWKS contains no usable keys")
            except Exception as exc:  # Never leak provider details into an API response.
                raise JwtConfigurationError("JWKS is unavailable") from exc
            self._keys = parsed
            self._expires_at = now + self.settings.auth_jwks_cache_seconds

    def signing_key_for(self, token: str) -> tuple[Any, str]:
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            algorithm = header.get("alg")
        except Exception as exc:
            raise JwtValidationError("Malformed JWT") from exc
        if not isinstance(kid, str) or not kid or algorithm not in {"RS256", "ES256"}:
            raise JwtValidationError("Unexpected JWT header")

        self._refresh()
        jwk = self._keys.get(kid)
        if jwk is None:
            self._refresh(force=True)
            jwk = self._keys.get(kid)
        if jwk is None:
            raise JwtValidationError("Unknown signing key")
        try:
            parsed = jwt.PyJWK.from_dict(jwk)
            if parsed.algorithm_name != algorithm:
                raise JwtValidationError("Signing algorithm mismatch")
            return parsed.key, algorithm
        except JwtValidationError:
            raise
        except Exception as exc:
            raise JwtValidationError("Invalid signing key") from exc


class JwtValidator:
    def __init__(
        self,
        settings: Settings,
        jwks_cache: JwksCache | None = None,
    ) -> None:
        self.settings = settings
        self.jwks_cache = jwks_cache or JwksCache(settings)

    def validate(self, token: str) -> AuthenticatedIdentity:
        if not self.settings.supabase_auth_issuer or not self.settings.supabase_auth_jwks_url:
            raise JwtConfigurationError("Supabase Auth is not configured")
        key, algorithm = self.jwks_cache.signing_key_for(token)
        options = {"require": ["sub", "exp", "iss"], "verify_aud": bool(self.settings.supabase_auth_audience)}
        try:
            claims = jwt.decode(
                token,
                key=key,
                algorithms=[algorithm],
                issuer=self.settings.supabase_auth_issuer,
                audience=self.settings.supabase_auth_audience or None,
                options=options,
            )
        except Exception as exc:
            raise JwtValidationError("JWT validation failed") from exc
        subject = claims.get("sub")
        expires_at = claims.get("exp")
        if not isinstance(subject, str) or not subject or not isinstance(expires_at, (int, float)):
            raise JwtValidationError("JWT claims are incomplete")
        return AuthenticatedIdentity(
            user_id=subject,
            token_expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc),
        )


class RoleService:
    """Server-side role lookup and minimal access audit abstraction."""

    def __init__(self, supabase: SupabaseService) -> None:
        self.supabase = supabase
        self._test_roles: dict[str, set[str]] = {}
        self._test_access_logs: dict[tuple[str, str], dict[str, Any]] = {}

    @property
    def test_access_logs(self) -> list[dict[str, Any]]:
        return list(self._test_access_logs.values())

    def set_roles_for_testing(self, user_id: str, roles: set[str] | list[str] | tuple[str, ...]) -> None:
        selected = set(roles)
        if not selected <= VALID_ROLES:
            raise ValueError("Unknown role")
        self._test_roles[user_id] = selected

    def get_active_roles(self, user_id: str) -> tuple[str, ...]:
        if self.supabase.configured:
            roles = self.supabase.list_active_user_roles(user_id)
        else:
            roles = self._test_roles.get(user_id, set())
        return tuple(sorted(role for role in roles if role in VALID_ROLES))

    @staticmethod
    def capabilities_for(roles: tuple[str, ...] | list[str]) -> tuple[str, ...]:
        capabilities: set[str] = set()
        for role in roles:
            capabilities.update(ROLE_CAPABILITIES.get(role, frozenset()))
        return tuple(sorted(capabilities))

    def audit(
        self,
        *,
        user_id: str,
        action: str,
        result: str,
        request_id: str,
        roles: tuple[str, ...],
        dataset_id: str | None = None,
        expires_at: datetime | None = None,
        denial_reason: str | None = None,
        client_fingerprint_hash: str | None = None,
    ) -> dict[str, Any]:
        record = {
            "id": str(uuid.uuid4()),
            "dataset_id": dataset_id,
            "user_id": user_id,
            "action": action,
            "result": result,
            "request_id": request_id,
            "role_snapshot": list(roles),
            "expires_at": expires_at.isoformat() if expires_at else None,
            "denial_reason": denial_reason,
            "client_fingerprint_hash": client_fingerprint_hash,
        }
        if self.supabase.configured:
            return self.supabase.save_dataset_access_log(record)
        key = (user_id, request_id)
        existing = self._test_access_logs.get(key)
        if existing:
            return existing
        self._test_access_logs[key] = record
        return record

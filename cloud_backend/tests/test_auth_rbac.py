from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends, HTTPException
from fastapi.testclient import TestClient

from cloud_backend.app.config import Settings
from cloud_backend.app.main import create_app
from cloud_backend.app.security import require_all_roles, require_any_role, require_distinct_actors
from cloud_backend.app.services.auth_service import JwksCache, JwtValidator, RoleService
from cloud_backend.app.services.supabase_service import SupabaseService


API_KEY = "machine-test-key"
ISSUER = "https://example.supabase.co/auth/v1"
AUDIENCE = "authenticated"
USER_ID = "11111111-1111-4111-8111-111111111111"


def _number_bytes(value: int) -> bytes:
    return value.to_bytes((value.bit_length() + 7) // 8, "big")


def make_key(kid: str) -> tuple[Any, dict[str, str]]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    numbers = private_key.public_key().public_numbers()
    jwk = {
        "kty": "RSA",
        "kid": kid,
        "use": "sig",
        "alg": "RS256",
        "n": jwt.utils.base64url_encode(_number_bytes(numbers.n)).decode("ascii"),
        "e": jwt.utils.base64url_encode(_number_bytes(numbers.e)).decode("ascii"),
    }
    return private_key, jwk


def make_token(
    private_key: Any,
    kid: str,
    *,
    subject: str = USER_ID,
    issuer: str = ISSUER,
    audience: str = AUDIENCE,
    expires_delta: timedelta = timedelta(minutes=10),
) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": subject, "iss": issuer, "aud": audience, "iat": now, "exp": now + expires_delta},
        private_key,
        algorithm="RS256",
        headers={"kid": kid},
    )


class JwksFetcher:
    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self.documents = documents
        self.calls = 0

    def __call__(self, url: str, timeout: int) -> dict[str, Any]:
        assert url == f"{ISSUER}/.well-known/jwks.json"
        assert timeout > 0
        value = self.documents[min(self.calls, len(self.documents) - 1)]
        self.calls += 1
        return value


def build_client(documents: list[dict[str, Any]]) -> tuple[TestClient, JwksFetcher]:
    settings = Settings(
        scraper_api_key=API_KEY,
        source_mode="fixture",
        supabase_auth_issuer=ISSUER,
        supabase_auth_audience=AUDIENCE,
        supabase_auth_jwks_url=f"{ISSUER}/.well-known/jwks.json",
        auth_jwks_cache_seconds=3600,
    )
    app = create_app(settings)
    fetcher = JwksFetcher(documents)
    app.state.jwt_validator = JwtValidator(settings, JwksCache(settings, fetcher=fetcher))
    return TestClient(app), fetcher


def bearer(token: str, request_id: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if request_id:
        headers["X-Request-ID"] = request_id
    return headers


def test_auth_me_validates_signed_jwt_roles_capabilities_and_audits_once():
    private_key, jwk = make_key("key-one")
    client, _ = build_client([{"keys": [jwk]}])
    client.app.state.role_service.set_roles_for_testing(USER_ID, {"viewer", "reviewer"})
    token = make_token(private_key, "key-one")

    first = client.get("/auth/me", headers=bearer(token, "request-auth-001"))
    second = client.get("/auth/me", headers=bearer(token, "request-auth-001"))

    assert first.status_code == 200
    assert second.status_code == 200
    body = first.json()
    assert body["user_id"] == USER_ID
    assert body["roles"] == ["reviewer", "viewer"]
    assert {"dataset.metadata.read", "dataset.access.request", "review.decide"} <= set(body["capabilities"])
    assert body["authentication_type"] == "supabase_jwt"
    logs = client.app.state.role_service.test_access_logs
    assert len(logs) == 1
    assert logs[0]["action"] == "AUTHENTICATED"
    assert token not in str(logs)


@pytest.mark.parametrize(
    ("roles", "expected"),
    [
        ({"viewer"}, {"dataset.metadata.read", "dataset.access.request"}),
        ({"reviewer"}, {"review.decide", "dataset.restore.participate"}),
        ({"dataset_admin"}, {"dataset.activate", "dataset.revoke", "role.assignment.manage"}),
        ({"operator"}, {"operations.read", "live.window.request"}),
        ({"viewer", "operator"}, {"dataset.metadata.read", "operations.read"}),
    ],
)
def test_capabilities_derive_from_active_roles(roles: set[str], expected: set[str]):
    private_key, jwk = make_key("key-roles")
    client, _ = build_client([{"keys": [jwk]}])
    client.app.state.role_service.set_roles_for_testing(USER_ID, roles)
    response = client.get("/auth/capabilities", headers=bearer(make_token(private_key, "key-roles")))
    assert response.status_code == 200
    assert expected <= set(response.json()["capabilities"])


def test_valid_jwt_without_active_roles_is_authenticated_but_not_authorized():
    private_key, jwk = make_key("key-no-role")
    client, _ = build_client([{"keys": [jwk]}])
    response = client.get("/auth/me", headers=bearer(make_token(private_key, "key-no-role")))
    assert response.status_code == 200
    assert response.json()["roles"] == []
    assert response.json()["capabilities"] == []


@pytest.mark.parametrize("kind", ["missing", "malformed", "expired", "issuer", "audience", "signature", "algorithm"])
def test_invalid_human_tokens_are_rejected(kind: str):
    private_key, jwk = make_key("key-invalid")
    client, _ = build_client([{"keys": [jwk]}])
    if kind == "missing":
        response = client.get("/auth/me")
    elif kind == "malformed":
        response = client.get("/auth/me", headers=bearer("not.a.jwt"))
    elif kind == "expired":
        response = client.get("/auth/me", headers=bearer(make_token(private_key, "key-invalid", expires_delta=timedelta(seconds=-1))))
    elif kind == "issuer":
        response = client.get("/auth/me", headers=bearer(make_token(private_key, "key-invalid", issuer="https://wrong.invalid")))
    elif kind == "audience":
        response = client.get("/auth/me", headers=bearer(make_token(private_key, "key-invalid", audience="wrong")))
    elif kind == "signature":
        other, _ = make_key("key-invalid")
        response = client.get("/auth/me", headers=bearer(make_token(other, "key-invalid")))
    else:
        now = datetime.now(timezone.utc)
        token = jwt.encode(
            {"sub": USER_ID, "iss": ISSUER, "aud": AUDIENCE, "exp": now + timedelta(minutes=10)},
            "untrusted-secret-with-at-least-thirty-two-characters",
            algorithm="HS256",
            headers={"kid": "key-invalid"},
        )
        response = client.get("/auth/me", headers=bearer(token))
    assert response.status_code == 401
    assert "invalido" in response.json()["detail"].lower() or "requerido" in response.json()["detail"].lower()


def test_jwks_rotation_refreshes_only_when_new_kid_is_seen():
    first_key, first_jwk = make_key("old-key")
    second_key, second_jwk = make_key("new-key")
    client, fetcher = build_client([{"keys": [first_jwk]}, {"keys": [first_jwk, second_jwk]}])
    client.app.state.role_service.set_roles_for_testing(USER_ID, {"viewer"})
    assert client.get("/auth/me", headers=bearer(make_token(first_key, "old-key"))).status_code == 200
    assert client.get("/auth/me", headers=bearer(make_token(second_key, "new-key"))).status_code == 200
    assert fetcher.calls == 2


def test_bearer_and_service_api_key_are_separated_without_machine_regression():
    private_key, jwk = make_key("key-split")
    client, _ = build_client([{"keys": [jwk]}])
    token = make_token(private_key, "key-split")
    assert client.post("/jobs/scrape", json={"source": "vea"}, headers=bearer(token)).status_code == 401
    assert client.get("/auth/me", headers={"X-API-Key": API_KEY}).status_code == 401
    assert client.post("/jobs/scrape", json={"source": "vea"}, headers={"X-API-Key": API_KEY}).status_code == 200


def test_role_dependencies_support_any_and_all_without_elevating_user():
    private_key, jwk = make_key("key-dependency")
    client, _ = build_client([{"keys": [jwk]}])
    app = client.app

    @app.get("/test/any")
    def any_role(_user=Depends(require_any_role("reviewer", "dataset_admin"))):
        return {"ok": True}

    @app.get("/test/all")
    def all_roles(_user=Depends(require_all_roles("viewer", "reviewer"))):
        return {"ok": True}

    token = make_token(private_key, "key-dependency")
    app.state.role_service.set_roles_for_testing(USER_ID, {"viewer"})
    assert client.get("/test/any", headers=bearer(token)).status_code == 403
    assert client.get("/test/all", headers=bearer(token)).status_code == 403
    app.state.role_service.set_roles_for_testing(USER_ID, {"viewer", "reviewer"})
    assert client.get("/test/any", headers=bearer(token)).status_code == 200
    assert client.get("/test/all", headers=bearer(token)).status_code == 200


def test_role_service_audit_is_idempotent_by_user_and_request_id():
    service = RoleService(SupabaseService(Settings()))
    service.set_roles_for_testing(USER_ID, {"viewer"})
    first = service.audit(user_id=USER_ID, action="AUTHENTICATED", result="ALLOWED", request_id="same-request", roles=("viewer",))
    second = service.audit(user_id=USER_ID, action="AUTHENTICATED", result="ALLOWED", request_id="same-request", roles=("viewer",))
    assert first["id"] == second["id"]
    assert len(service.test_access_logs) == 1


def test_distinct_actor_contract_rejects_single_person_restore():
    require_distinct_actors("first", "second")
    with pytest.raises(HTTPException) as error:
        require_distinct_actors("same", "same")
    assert error.value.status_code == 409


def test_future_private_dataset_contracts_are_models_not_active_routes():
    private_key, jwk = make_key("key-contract")
    client, _ = build_client([{"keys": [jwk]}])
    assert client.get("/private/datasets/current", headers=bearer(make_token(private_key, "key-contract"))).status_code == 404


def test_openapi_exposes_human_identity_endpoints_without_sensitive_configuration():
    private_key, jwk = make_key("key-openapi")
    client, _ = build_client([{"keys": [jwk]}])
    schema = client.get("/openapi.json").json()
    assert "/auth/me" in schema["paths"]
    assert "/auth/capabilities" in schema["paths"]
    serialized = str(schema)
    assert "replace_me" not in serialized
    assert "SUPABASE_SERVICE_ROLE_KEY" not in serialized
    assert make_token(private_key, "key-openapi") not in serialized

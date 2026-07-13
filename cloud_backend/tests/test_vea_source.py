from __future__ import annotations

import json

import pytest
import requests

from cloud_backend.app.config import Settings
from cloud_backend.app.sources.vea import VeaSource


def source(**kwargs) -> VeaSource:
    settings = Settings(source_mode="fixture", max_products_per_run=kwargs.get("max_products", 100), max_pages_per_run=2)
    return VeaSource(settings)


def test_fixture_adapter_normalizes_required_contract():
    rows, incidents = source().fetch_catalog(max_products=3, max_pages=1)
    assert len(rows) == 3
    assert not incidents
    required = {
        "comercio", "sucursal", "localidad", "canal_precio", "producto", "marca", "categoria",
        "presentacion", "sku", "ean", "precio_regular", "precio_promocional", "precio_efectivo",
        "condicion_promocion", "medio_pago", "stock_publicado", "fecha_hora_extraccion", "url_origen",
        "archivo_origen", "extractor_version", "raw_hash",
    }
    assert required <= set(rows[0])
    assert rows[0]["canal_precio"] == "ONLINE"
    assert len(rows[0]["raw_hash"]) == 64


def test_product_and_page_limits_are_enforced():
    rows, _ = source(max_products=2).fetch_catalog(max_products=50, max_pages=10)
    assert len(rows) == 2


def test_response_validation_and_invalid_product():
    adapter = source()
    assert adapter.validate_response([])
    assert not adapter.validate_response({})
    assert adapter.normalize_product({"productName": "Sin oferta"}) is None


def test_fixture_mode_never_calls_http(monkeypatch):
    adapter = source()

    def forbidden(*args, **kwargs):
        raise AssertionError("No debe llamar internet en fixture mode")

    monkeypatch.setattr(adapter.session, "get", forbidden)
    rows, _ = adapter.fetch_catalog(max_products=1, max_pages=1)
    assert len(rows) == 1


def test_live_timeout_is_reported_with_limited_retries(monkeypatch):
    settings = Settings(source_mode="live", request_delay_seconds=0, request_timeout_seconds=1)
    adapter = VeaSource(settings)
    calls = {"count": 0}

    def timeout(*args, **kwargs):
        calls["count"] += 1
        raise requests.Timeout("test")

    monkeypatch.setattr(adapter.session, "get", timeout)
    with pytest.raises(requests.Timeout):
        adapter.fetch_page(0, 1)
    assert calls["count"] == 3


def test_fixture_contains_no_credentials():
    text = source().fixture_path.read_text(encoding="utf-8").lower()
    data = json.loads(text)
    assert data
    assert "api_key" not in text
    assert "service_role" not in text

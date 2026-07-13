from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseSource(ABC):
    source_name: str
    source_version: str

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def fetch_catalog(self, max_products: int, max_pages: int) -> tuple[list[dict[str, Any]], list[str]]:
        raise NotImplementedError

    @abstractmethod
    def fetch_page(self, page: int, page_size: int) -> Any:
        raise NotImplementedError

    @abstractmethod
    def normalize_product(self, product: dict[str, Any]) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def build_snapshot(self, products: list[dict[str, Any]]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def validate_response(self, payload: Any) -> bool:
        raise NotImplementedError

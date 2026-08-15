from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import partial

import httpx

from concurrency_lab.infrastructure.http import fetch_http_text, fetch_http_text_async


@dataclass(frozen=True, slots=True)
class HttpRequestPlan:
    """Configuração de um lote HTTP I/O-bound."""

    base_url: str
    request_count: int
    delay_ms: int

    def __post_init__(self) -> None:
        if not self.base_url.strip():
            raise ValueError("base_url não pode ser vazio.")
        if self.request_count < 0:
            raise ValueError("request_count não pode ser negativo.")
        if self.delay_ms < 0:
            raise ValueError("delay_ms não pode ser negativo.")

    @property
    def url(self) -> str:
        return f"{self.base_url.rstrip('/')}/delay?ms={self.delay_ms}"


def build_http_sync_tasks(
    plan: HttpRequestPlan,
    client: httpx.Client,
) -> list[Callable[[], str]]:
    return [partial(fetch_http_text, client, plan.url) for _ in range(plan.request_count)]


def build_http_async_tasks(
    plan: HttpRequestPlan,
    client: httpx.AsyncClient,
) -> list[Callable[[], Awaitable[str]]]:
    return [partial(fetch_http_text_async, client, plan.url) for _ in range(plan.request_count)]

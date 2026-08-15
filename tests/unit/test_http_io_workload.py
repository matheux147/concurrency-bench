import asyncio

import httpx
import pytest

from concurrency_lab.application.use_cases import RunAsyncExperiment, RunExperiment
from concurrency_lab.domain.entities import Experiment
from concurrency_lab.domain.enums import ExperimentType
from concurrency_lab.infrastructure.concurrency import AsyncStrategy, SequentialStrategy, ThreadStrategy
from concurrency_lab.infrastructure.http import LocalDelayServer, fetch_http_text, fetch_http_text_async
from concurrency_lab.infrastructure.workloads import (
    HttpRequestPlan,
    build_http_async_tasks,
    build_http_sync_tasks,
)


def test_http_workload_supports_sync_execution() -> None:
    with LocalDelayServer() as server:
        plan = HttpRequestPlan(base_url=server.base_url, request_count=3, delay_ms=5)
        experiment = Experiment(
            name="HTTP síncrono",
            experiment_type=ExperimentType.HTTP,
            task_count=plan.request_count,
        )

        with httpx.Client(timeout=5.0) as client:
            tasks = build_http_sync_tasks(plan, client)
            result = RunExperiment(SequentialStrategy()).execute(experiment, tasks)

        assert result.completed_task_count == 3
        assert result.metadata["workers_used"] == 1
        assert all(payload.startswith("delayed 5 ms") for payload in result.metadata["completed_results"])


def test_http_workload_supports_threaded_execution() -> None:
    with LocalDelayServer() as server:
        plan = HttpRequestPlan(base_url=server.base_url, request_count=3, delay_ms=5)
        experiment = Experiment(
            name="HTTP com threads",
            experiment_type=ExperimentType.HTTP,
            task_count=plan.request_count,
        )

        with httpx.Client(timeout=5.0) as client:
            tasks = build_http_sync_tasks(plan, client)
            result = RunExperiment(ThreadStrategy(max_workers=2)).execute(experiment, tasks)

        assert result.completed_task_count == 3
        assert result.metadata["workers_used"] == 2
        assert all(payload.startswith("delayed 5 ms") for payload in result.metadata["completed_results"])


def test_http_workload_supports_async_execution() -> None:
    async def scenario() -> None:
        with LocalDelayServer() as server:
            plan = HttpRequestPlan(base_url=server.base_url, request_count=3, delay_ms=5)
            experiment = Experiment(
                name="HTTP assíncrono",
                experiment_type=ExperimentType.HTTP,
                task_count=plan.request_count,
            )

            async with httpx.AsyncClient(timeout=5.0) as client:
                tasks = build_http_async_tasks(plan, client)
                result = await RunAsyncExperiment(AsyncStrategy()).execute(experiment, tasks)

            assert result.completed_task_count == 3
            assert result.metadata["workers_used"] is None
            assert all(payload.startswith("delayed 5 ms") for payload in result.metadata["completed_results"])

    asyncio.run(scenario())


def test_http_client_raises_for_error_status() -> None:
    with LocalDelayServer() as server:
        with httpx.Client(timeout=5.0) as client:
            with pytest.raises(httpx.HTTPStatusError):
                fetch_http_text(client, f"{server.base_url}/missing")


def test_async_http_client_raises_for_error_status() -> None:
    async def scenario() -> None:
        with LocalDelayServer() as server:
            async with httpx.AsyncClient(timeout=5.0) as client:
                with pytest.raises(httpx.HTTPStatusError):
                    await fetch_http_text_async(client, f"{server.base_url}/missing")

    asyncio.run(scenario())

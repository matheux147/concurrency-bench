import asyncio

import pytest

from concurrency_bench.infrastructure.concurrency import AsyncStrategy


async def _failing_async_task() -> int:
    raise ValueError("falha assíncrona")


def test_async_strategy_executes_coroutines_concurrently() -> None:
    async def scenario() -> None:
        started_count = 0
        started_all = asyncio.Event()
        release = asyncio.Event()
        completed: list[str] = []

        async def task(label: str) -> str:
            nonlocal started_count

            started_count += 1
            if started_count == 3:
                started_all.set()
            await release.wait()
            completed.append(label)
            return label

        tasks = [lambda label=label: task(label) for label in ("a", "b", "c")]
        execution = asyncio.create_task(AsyncStrategy().execute(tasks))

        await asyncio.wait_for(started_all.wait(), timeout=1.0)
        release.set()

        report = await asyncio.wait_for(execution, timeout=1.0)

        assert report.completed_results == ("a", "b", "c")
        assert report.completed_count == 3
        assert report.workers_used is None
        assert completed == ["a", "b", "c"]

    asyncio.run(scenario())


def test_async_strategy_propagates_exceptions() -> None:
    async def scenario() -> None:
        with pytest.raises(ValueError, match="falha assíncrona"):
            await AsyncStrategy().execute([_failing_async_task])

    asyncio.run(scenario())

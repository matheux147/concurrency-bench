import pytest

from concurrency_lab.infrastructure.concurrency import ThreadStrategy


def double(value: int) -> int:
    return value * 2


def failing_task() -> int:
    raise ValueError("falha no worker")


def test_thread_strategy_executes_tasks_and_returns_results() -> None:
    tasks = [lambda value=value: double(value) for value in (1, 2, 3)]

    report = ThreadStrategy(max_workers=2).execute(tasks)

    assert report.completed_results == (2, 4, 6)
    assert report.completed_count == 3
    assert report.workers_used == 2


def test_thread_strategy_propagates_worker_exception() -> None:
    with pytest.raises(ValueError, match="falha no worker"):
        ThreadStrategy(max_workers=2).execute([lambda: 1, failing_task])


def test_thread_strategy_rejects_invalid_worker_count() -> None:
    with pytest.raises(ValueError, match="maior que zero"):
        ThreadStrategy(max_workers=0)

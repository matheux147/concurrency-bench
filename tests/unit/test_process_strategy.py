import pytest
from functools import partial

from concurrency_bench.infrastructure.concurrency import ProcessStrategy


def triple(value: int) -> int:
    return value * 3


def failing_process_task() -> int:
    raise ValueError("falha no processo")


def test_process_strategy_executes_picklable_tasks() -> None:
    tasks = [partial(triple, value) for value in (1, 2, 3)]

    report = ProcessStrategy(max_workers=2).execute(tasks)

    assert report.completed_results == (3, 6, 9)
    assert report.completed_count == 3
    assert report.workers_used == 2


def test_process_strategy_propagates_worker_exception() -> None:
    with pytest.raises(ValueError, match="falha no processo"):
        ProcessStrategy(max_workers=2).execute([failing_process_task])


def test_process_strategy_rejects_invalid_worker_count() -> None:
    with pytest.raises(ValueError, match="maior que zero"):
        ProcessStrategy(max_workers=0)

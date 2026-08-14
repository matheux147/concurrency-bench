import pytest

from concurrency_lab.domain.exceptions import DomainValidationError
from concurrency_lab.infrastructure.concurrency import SequentialStrategy


def test_sequential_strategy_executes_all_tasks_in_order() -> None:
    execution_order: list[int] = []

    def make_task(number: int):
        def task() -> int:
            execution_order.append(number)
            return number * 2

        return task

    report = SequentialStrategy().execute([make_task(1), make_task(2), make_task(3)])

    assert execution_order == [1, 2, 3]
    assert report.completed_results == (2, 4, 6)
    assert report.completed_count == 3


def test_sequential_strategy_propagates_task_exception() -> None:
    def failing_task() -> None:
        raise DomainValidationError("falha esperada")

    with pytest.raises(DomainValidationError, match="falha esperada"):
        SequentialStrategy().execute([lambda: 1, failing_task, lambda: 3])

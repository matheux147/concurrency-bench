import pytest

from concurrency_lab.infrastructure.workloads import build_cpu_bound_tasks, cpu_bound_work


def test_cpu_bound_work_is_deterministic() -> None:
    assert cpu_bound_work(0) == 0
    assert cpu_bound_work(5) == cpu_bound_work(5)


def test_cpu_bound_work_rejects_negative_iterations() -> None:
    with pytest.raises(ValueError, match="não pode ser negativo"):
        cpu_bound_work(-1)


def test_build_cpu_bound_tasks_creates_configurable_task_list() -> None:
    tasks = build_cpu_bound_tasks(task_count=3, work_iterations=7)

    assert len(tasks) == 3
    assert tuple(task() for task in tasks) == (cpu_bound_work(7),) * 3


def test_build_cpu_bound_tasks_rejects_negative_task_count() -> None:
    with pytest.raises(ValueError, match="não pode ser negativo"):
        build_cpu_bound_tasks(task_count=-1, work_iterations=1)

from collections.abc import Callable
from functools import partial


def cpu_bound_work(work_iterations: int) -> int:
    """Executa operações aritméticas determinísticas e consome CPU."""

    if work_iterations < 0:
        raise ValueError("work_iterations não pode ser negativo.")

    result = 0
    for value in range(1, work_iterations + 1):
        result = (result + value * value + value) % 1_000_000_007
    return result


def build_cpu_bound_tasks(
    task_count: int,
    work_iterations: int,
) -> list[Callable[[], int]]:
    """Cria tarefas picklable com a mesma carga configurável."""

    if task_count < 0:
        raise ValueError("task_count não pode ser negativo.")
    return [partial(cpu_bound_work, work_iterations) for _ in range(task_count)]

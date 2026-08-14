import pytest

from concurrency_lab.domain.entities import ExperimentResult
from concurrency_lab.domain.enums import ExecutionStrategy
from concurrency_lab.domain.exceptions import DomainValidationError


def test_result_calculates_throughput_and_average_time() -> None:
    result = ExperimentResult(
        experiment_name="Leitura simulada",
        strategy=ExecutionStrategy.THREADS,
        task_count=4,
        completed_task_count=4,
        total_time_seconds=2.0,
    )

    assert result.throughput_tasks_per_second == pytest.approx(2.0)
    assert result.average_task_time_seconds == pytest.approx(0.5)


def test_result_uses_completed_tasks_for_throughput() -> None:
    result = ExperimentResult(
        experiment_name="Falha parcial",
        strategy=ExecutionStrategy.PROCESSES,
        task_count=10,
        completed_task_count=4,
        total_time_seconds=2.0,
    )

    assert result.throughput_tasks_per_second == pytest.approx(2.0)


def test_result_allows_optional_metrics_and_empty_metadata() -> None:
    result = ExperimentResult(
        experiment_name="CPU inicial",
        strategy=ExecutionStrategy.SEQUENTIAL,
        task_count=0,
        completed_task_count=0,
        total_time_seconds=0.0,
        cpu_usage_percent=18.5,
        memory_usage_mb=42.0,
        metadata={"source": "unit-test"},
    )

    assert result.throughput_tasks_per_second == 0.0
    assert result.average_task_time_seconds == 0.0
    assert result.metadata["source"] == "unit-test"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("experiment_name", ""),
        ("task_count", -1),
        ("total_time_seconds", -0.1),
        ("cpu_usage_percent", -1.0),
        ("memory_usage_mb", -1.0),
    ],
)
def test_result_rejects_invalid_values(field: str, value: object) -> None:
    values: dict[str, object] = {
        "experiment_name": "Experimento válido",
        "strategy": ExecutionStrategy.SEQUENTIAL,
        "task_count": 1,
        "completed_task_count": 1,
        "total_time_seconds": 1.0,
    }
    values[field] = value

    with pytest.raises(DomainValidationError):
        ExperimentResult(**values)  # type: ignore[arg-type]

from collections.abc import Sequence

from concurrency_lab.application.strategies import ExecutionReport, Task
from concurrency_lab.application.use_cases import RunExperiment
from concurrency_lab.domain.entities import Experiment, ExperimentResult
from concurrency_lab.domain.enums import ExperimentType
import concurrency_lab.domain.enums as domain_enums


class FakeStrategy:
    """Stub pequeno para provar que o Use Case usa apenas o contrato."""

    kind = domain_enums.ExecutionStrategy.SEQUENTIAL

    def __init__(self) -> None:
        self.received_tasks: Sequence[Task] | None = None

    def execute(self, tasks: Sequence[Task]) -> ExecutionReport:
        self.received_tasks = tasks
        return ExecutionReport(completed_results=tuple(task() for task in tasks))


def test_run_experiment_depends_on_strategy_abstraction() -> None:
    strategy = FakeStrategy()
    experiment = Experiment(
        name="Exemplo determinístico",
        experiment_type=ExperimentType.CUSTOM,
        task_count=3,
    )
    tasks = [lambda: 10, lambda: 20, lambda: 30]

    result = RunExperiment(strategy).execute(experiment, tasks)

    assert isinstance(result, ExperimentResult)
    assert result.strategy is domain_enums.ExecutionStrategy.SEQUENTIAL
    assert result.task_count == 3
    assert result.completed_task_count == 3
    assert result.total_time_seconds >= 0
    assert result.metadata["completed_results"] == (10, 20, 30)
    assert strategy.received_tasks is tasks


def test_run_experiment_rejects_task_count_mismatch() -> None:
    experiment = Experiment(
        name="Quantidade inválida",
        experiment_type=ExperimentType.CUSTOM,
        task_count=2,
    )

    try:
        RunExperiment(FakeStrategy()).execute(experiment, [lambda: 1])
    except ValueError as error:
        assert "corresponder" in str(error)
    else:
        raise AssertionError("Era esperado erro para quantidade de tarefas inconsistente")

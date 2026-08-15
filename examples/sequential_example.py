from concurrency_bench.application.use_cases import RunExperiment
from concurrency_bench.domain.entities import Experiment
from concurrency_bench.domain.enums import ExperimentType
from concurrency_bench.infrastructure.concurrency import SequentialStrategy


def main() -> None:
    experiment = Experiment(
        name="Soma determinística",
        experiment_type=ExperimentType.CUSTOM,
        task_count=10,
    )
    tasks = [lambda number=number: number * number for number in range(10)]

    result = RunExperiment(SequentialStrategy()).execute(experiment, tasks)
    print(f"Experimento: {result.experiment_name}")
    print(f"Estratégia: {result.strategy.value}")
    print(
        f"Tarefas concluídas: {result.completed_task_count}/{result.task_count}")
    print(f"Tempo total: {result.total_time_seconds:.9f}s")
    print(f"Resultados: {result.metadata['completed_results']}")


if __name__ == "__main__":
    main()

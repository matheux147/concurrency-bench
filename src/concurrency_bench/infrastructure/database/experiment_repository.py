import json
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from concurrency_bench.application.ports.experiment_repository import ExperimentRepository
from concurrency_bench.domain.entities import Experiment, ExperimentResult
from concurrency_bench.domain.enums import ExperimentType, ExecutionStrategy
from concurrency_bench.infrastructure.database.models import ExperimentModel, ExperimentResultModel


class SqlAlchemyExperimentRepository(ExperimentRepository):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def save(self, experiment: Experiment) -> None:
        with self._session_factory() as session:
            with session.begin():
                existing = session.get(ExperimentModel, experiment.id)
                params_str = json.dumps(dict(experiment.parameters))

                if existing is None:
                    session.add(
                        ExperimentModel(
                            id=experiment.id,
                            name=experiment.name,
                            experiment_type=experiment.experiment_type.value,
                            task_count=experiment.task_count,
                            description=experiment.description,
                            parameters_json=params_str,
                            created_at=experiment.created_at,
                        )
                    )
                else:
                    existing.name = experiment.name
                    existing.experiment_type = experiment.experiment_type.value
                    existing.task_count = experiment.task_count
                    existing.description = experiment.description
                    existing.parameters_json = params_str
                    existing.created_at = experiment.created_at

    def get_by_id(self, experiment_id: UUID) -> Experiment | None:
        with self._session_factory() as session:
            row = session.get(ExperimentModel, experiment_id)
            if row is None:
                return None
            return self._to_domain_experiment(row)

    def save_results(self, experiment_id: UUID, results: list[ExperimentResult]) -> None:
        with self._session_factory() as session:
            with session.begin():
                for result in results:
                    meta_str = json.dumps(dict(result.metadata))
                    session.add(
                        ExperimentResultModel(
                            experiment_id=experiment_id,
                            strategy=result.strategy.value,
                            completed_task_count=result.completed_task_count,
                            total_time_seconds=result.total_time_seconds,
                            cpu_usage_percent=result.cpu_usage_percent,
                            memory_usage_mb=result.memory_usage_mb,
                            workers_used=result.metadata.get("workers_used"),
                            speedup=result.metadata.get("speedup"),
                            metadata_json=meta_str,
                        )
                    )

    def get_results_by_experiment_id(self, experiment_id: UUID) -> list[ExperimentResult]:
        with self._session_factory() as session:
            statement = (
                select(ExperimentResultModel)
                .where(ExperimentResultModel.experiment_id == experiment_id)
            )
            rows = session.execute(statement).scalars().all()
            return [self._to_domain_result(row) for row in rows]

    def list_all(self) -> list[tuple[Experiment, list[ExperimentResult]]]:
        with self._session_factory() as session:
            statement = select(ExperimentModel).order_by(
                ExperimentModel.created_at.desc())
            rows = session.execute(statement).scalars().all()

            output = []
            for row in rows:
                exp = self._to_domain_experiment(row)
                res = [self._to_domain_result(r) for r in row.results]
                output.append((exp, res))
            return output

    def _to_domain_experiment(self, row: ExperimentModel) -> Experiment:
        params = json.loads(row.parameters_json)
        created_at = row.created_at.replace(
            tzinfo=timezone.utc) if row.created_at.tzinfo is None else row.created_at
        return Experiment(
            id=row.id,
            name=row.name,
            experiment_type=ExperimentType(row.experiment_type),
            task_count=row.task_count,
            description=row.description,
            parameters=params,
            created_at=created_at,
        )

    def _to_domain_result(self, row: ExperimentResultModel) -> ExperimentResult:
        meta = json.loads(row.metadata_json)

        # Ensure we add database-loaded workers_used & speedup to the metadata dictionary if needed
        # We also need to get experiment name, which we can fetch or use generic
        # To fetch, we can use row.experiment.name
        exp_name = row.experiment.name if row.experiment else "Persistência"

        # Ensure correct strategy mapping
        strategy_val = row.strategy
        if strategy_val == "threads":
            strategy = ExecutionStrategy.THREADS
        elif strategy_val == "processes":
            strategy = ExecutionStrategy.PROCESSES
        elif strategy_val == "async":
            strategy = ExecutionStrategy.ASYNC
        else:
            strategy = ExecutionStrategy.SEQUENTIAL

        return ExperimentResult(
            experiment_name=exp_name,
            strategy=strategy,
            task_count=row.experiment.task_count if row.experiment else row.completed_task_count,
            completed_task_count=row.completed_task_count,
            total_time_seconds=row.total_time_seconds,
            cpu_usage_percent=row.cpu_usage_percent,
            memory_usage_mb=row.memory_usage_mb,
            metadata=meta,
        )

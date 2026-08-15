import pytest
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy.exc import OperationalError

from concurrency_lab.domain.entities import Experiment, ExperimentResult
from concurrency_lab.domain.enums import ExperimentType, ExecutionStrategy
from concurrency_lab.infrastructure.database import (
    build_engine,
    build_session_factory,
    reset_schema,
)
from concurrency_lab.infrastructure.database.experiment_repository import SqlAlchemyExperimentRepository

@pytest.fixture(scope="module")
def database_engine():
    engine = build_engine()
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
    except OperationalError as error:
        pytest.skip(f"PostgreSQL indisponível: {error}")

    reset_schema(engine)
    yield engine
    engine.dispose()

@pytest.fixture()
def session_factory(database_engine):
    return build_session_factory(database_engine.url.render_as_string(hide_password=False))

def test_postgres_experiment_repository_saves_and_retrieves(session_factory) -> None:
    repository = SqlAlchemyExperimentRepository(session_factory)
    
    experiment_id = uuid4()
    experiment = Experiment(
        id=experiment_id,
        name="Teste Concorrente Integrado",
        experiment_type=ExperimentType.CPU_BOUND,
        task_count=10,
        description="Teste de persistência do repositório",
        parameters={"max_workers": 4, "carga": 1000},
    )
    
    # Save experiment
    repository.save(experiment)
    
    # Retrieve experiment
    retrieved = repository.get_by_id(experiment_id)
    assert retrieved is not None
    assert retrieved.name == "Teste Concorrente Integrado"
    assert retrieved.task_count == 10
    assert retrieved.experiment_type == ExperimentType.CPU_BOUND
    assert retrieved.parameters == {"max_workers": 4, "carga": 1000}
    
    # Save results
    result1 = ExperimentResult(
        experiment_name="Teste Concorrente Integrado",
        strategy=ExecutionStrategy.THREADS,
        task_count=10,
        completed_task_count=10,
        total_time_seconds=0.15,
        cpu_usage_percent=12.5,
        memory_usage_mb=45.0,
        metadata={"workers_used": 4},
    )
    
    result2 = ExperimentResult(
        experiment_name="Teste Concorrente Integrado",
        strategy=ExecutionStrategy.SEQUENTIAL,
        task_count=10,
        completed_task_count=10,
        total_time_seconds=0.45,
        cpu_usage_percent=4.2,
        memory_usage_mb=40.0,
        metadata={"workers_used": 1},
    )
    
    repository.save_results(experiment_id, [result1, result2])
    
    # Retrieve results
    results = repository.get_results_by_experiment_id(experiment_id)
    assert len(results) == 2
    
    strategies = [r.strategy for r in results]
    assert ExecutionStrategy.THREADS in strategies
    assert ExecutionStrategy.SEQUENTIAL in strategies
    
    # Check details of thread result
    thread_res = next(r for r in results if r.strategy == ExecutionStrategy.THREADS)
    assert thread_res.completed_task_count == 10
    assert thread_res.total_time_seconds == pytest.approx(0.15)
    assert thread_res.cpu_usage_percent == pytest.approx(12.5)
    assert thread_res.memory_usage_mb == pytest.approx(45.0)
    assert thread_res.metadata == {"workers_used": 4}
    
    # List all
    all_exps = repository.list_all()
    assert len(all_exps) >= 1
    found = next((e for e in all_exps if e[0].id == experiment_id), None)
    assert found is not None
    assert len(found[1]) == 2

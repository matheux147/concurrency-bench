import pytest
import pandas as pd
from concurrency_bench.presentation.streamlit.config import (
    validate_cpu_params,
    validate_http_params,
    validate_stock_params,
)
from concurrency_bench.presentation.streamlit.tables import (
    build_comparison_table,
    build_stock_table,
)
from concurrency_bench.application.benchmarks import BenchmarkComparison, BenchmarkSummary
from concurrency_bench.domain.entities import ExperimentResult
from concurrency_bench.domain.enums import ExecutionStrategy


def test_validate_cpu_params():
    # Valid
    assert validate_cpu_params(["sequential"], 10, 2, 1000, 3) == []

    # Invalid
    errors = validate_cpu_params([], 0, 0, 0, 0)
    assert len(errors) == 5
    assert "Selecione ao menos uma estratégia." in errors
    assert "A quantidade de tarefas deve ser maior que zero." in errors
    assert "A quantidade de workers deve ser maior que zero." in errors
    assert "A carga (iterações) deve ser maior que zero." in errors
    assert "O número de repetições deve ser maior que zero." in errors


def test_validate_http_params():
    # Valid
    assert validate_http_params(["threads"], 20, 100, 4, 3) == []

    # Invalid
    errors = validate_http_params([], 0, -50, 0, 0)
    assert len(errors) == 5
    assert "Selecione ao menos uma estratégia." in errors
    assert "A quantidade de requisições deve ser maior que zero." in errors
    assert "O atraso HTTP (ms) não pode ser negativo." in errors
    assert "A quantidade de workers deve ser maior que zero." in errors
    assert "O número de repetições deve ser maior que zero." in errors


def test_validate_stock_params():
    # Valid
    assert validate_stock_params(["Memória sem Lock"], 10, 50, 10, 3) == []

    # Invalid
    errors = validate_stock_params([], -10, 0, 0, 0)
    assert len(errors) == 5
    assert "Selecione ao menos um cenário de estoque." in errors
    assert "O estoque inicial não pode ser negativo." in errors
    assert "A quantidade de tentativas deve ser maior que zero." in errors
    assert "A concorrência (workers) deve ser maior que zero." in errors
    assert "O número de repetições deve ser maior que zero." in errors


def _mock_result(total_time_seconds: float, completed_results: list[bool] | None = None) -> ExperimentResult:
    metadata = {}
    if completed_results is not None:
        metadata["completed_results"] = completed_results
    return ExperimentResult(
        experiment_name="stock_test",
        strategy=ExecutionStrategy.THREADS,
        task_count=len(completed_results) if completed_results else 4,
        completed_task_count=len(
            completed_results) if completed_results else 4,
        total_time_seconds=total_time_seconds,
        cpu_usage_percent=5.0,
        memory_usage_mb=15.0,
        metadata=metadata,
    )


def test_build_comparison_table():
    summary_seq = BenchmarkSummary.from_results(
        "sequential",
        [_mock_result(2.0), _mock_result(2.0)],
    )
    summary_thr = BenchmarkSummary.from_results(
        "threads",
        [_mock_result(0.5), _mock_result(0.5)],
    )

    comparison = BenchmarkComparison.from_summaries(
        scenario_name="Test Comparison",
        summaries=[summary_seq, summary_thr],
        baseline_strategy="sequential",
    )

    df = build_comparison_table(comparison)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == [
        "Estratégia",
        "Tempo Médio (s)",
        "Tempo Mediano (s)",
        "Throughput Médio (tarefas/s)",
        "Speedup",
        "CPU Médio",
        "Memória Média",
        "Workers",
    ]
    assert df.loc[0, "Estratégia"] == "sequential"
    assert df.loc[0, "Speedup"] == "1.00x"
    assert df.loc[1, "Estratégia"] == "threads"
    assert df.loc[1, "Speedup"] == "4.00x"


def test_build_stock_table():
    summary_no_lock = BenchmarkSummary.from_results(
        "Memória sem Lock",
        [_mock_result(0.1, [True] * 30 + [False] * 20)],
    )
    summary_with_lock = BenchmarkSummary.from_results(
        "Memória com Lock",
        [_mock_result(0.2, [True] * 10 + [False] * 40)],
    )

    comparison = BenchmarkComparison.from_summaries(
        scenario_name="Stock Test Comparison",
        summaries=[summary_no_lock, summary_with_lock],
        baseline_strategy=None,
    )

    stocks_map = {
        "Memória sem Lock": -10,
        "Memória com Lock": 0,
    }

    df = build_stock_table(comparison, stocks_map, initial_stock=10)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == [
        "Cenário",
        "Estoque Inicial",
        "Tentativas",
        "Aprovadas",
        "Rejeitadas",
        "Estoque Final",
        "Inconsistência",
        "Tempo Médio (s)",
        "Throughput Médio (tentativas/s)",
    ]

    assert df.loc[0, "Cenário"] == "Memória sem Lock"
    assert df.loc[0, "Aprovadas"] == 30
    assert df.loc[0, "Rejeitadas"] == 20
    assert df.loc[0, "Estoque Final"] == -10
    # Inconsistency is expected due to negative stock and more approved than initial
    assert "Sim" in df.loc[0, "Inconsistência"]

    assert df.loc[1, "Cenário"] == "Memória com Lock"
    assert df.loc[1, "Aprovadas"] == 10
    assert df.loc[1, "Rejeitadas"] == 40
    assert df.loc[1, "Estoque Final"] == 0
    assert df.loc[1, "Inconsistência"] == "Não"


def test_rebuild_comparison():
    from concurrency_bench.presentation.streamlit.executor import rebuild_comparison
    from concurrency_bench.domain.entities import Experiment
    from concurrency_bench.domain.enums import ExperimentType

    experiment = Experiment(
        name="Teste Rebuild",
        experiment_type=ExperimentType.DATABASE,
        task_count=10,
        parameters={},
    )

    r1 = ExperimentResult(
        experiment_name="Teste Rebuild",
        strategy=ExecutionStrategy.THREADS,
        task_count=10,
        completed_task_count=5,
        total_time_seconds=0.1,
        strategy_name="Cenário A",
    )
    r2 = ExperimentResult(
        experiment_name="Teste Rebuild",
        strategy=ExecutionStrategy.THREADS,
        task_count=10,
        completed_task_count=6,
        total_time_seconds=0.2,
        strategy_name="Cenário B",
    )

    comp = rebuild_comparison(experiment, [r1, r2])
    assert comp.scenario_name == "Teste Rebuild"
    assert len(comp.summaries) == 2

    summary_names = [s.strategy_name for s in comp.summaries]
    assert "Cenário A" in summary_names
    assert "Cenário B" in summary_names

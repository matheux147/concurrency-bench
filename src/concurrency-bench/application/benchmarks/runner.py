from __future__ import annotations

from collections.abc import Callable

from concurrency_lab.application.benchmarks.models import BenchmarkSummary
from concurrency_lab.domain.entities import ExperimentResult


class BenchmarkRunner:
    """Executa um mesmo cenário múltiplas vezes e preserva os resultados brutos."""

    def __init__(self, repetitions: int = 3, warmup_runs: int = 1) -> None:
        if repetitions <= 0:
            raise ValueError("repetitions deve ser maior que zero.")
        if warmup_runs < 0:
            raise ValueError("warmup_runs não pode ser negativo.")
        self._repetitions = repetitions
        self._warmup_runs = warmup_runs

    def run(
        self,
        *,
        strategy_name: str,
        execute_once: Callable[[], ExperimentResult],
    ) -> BenchmarkSummary:
        for _ in range(self._warmup_runs):
            execute_once()

        runs = tuple(execute_once() for _ in range(self._repetitions))
        return BenchmarkSummary.from_results(strategy_name=strategy_name, runs=runs)

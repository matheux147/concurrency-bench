from __future__ import annotations

from itertools import count

import pytest

from concurrency_bench.application.benchmarks import BenchmarkComparison, BenchmarkRunner, BenchmarkSummary, StatisticalSummary
from concurrency_bench.domain.entities import ExperimentResult
from concurrency_bench.domain.enums import ExecutionStrategy
from concurrency_bench.infrastructure.monitoring import ProcessSample, build_process_usage
from concurrency_bench.infrastructure.monitoring import process_measurement as measurement_module


def _result(total_time_seconds: float, *, workers_used: int | None = None) -> ExperimentResult:
    metadata = {}
    if workers_used is not None:
        metadata["workers_used"] = workers_used
    return ExperimentResult(
        experiment_name="benchmark",
        strategy=ExecutionStrategy.SEQUENTIAL,
        task_count=4,
        completed_task_count=4,
        total_time_seconds=total_time_seconds,
        cpu_usage_percent=10.0,
        memory_usage_mb=20.0,
        metadata=metadata,
    )


def test_statistical_summary_calculates_average_median_min_max_and_stddev() -> None:
    summary = StatisticalSummary.from_values([1.0, 2.0, 3.0, 4.0])

    assert summary.average == pytest.approx(2.5)
    assert summary.median == pytest.approx(2.5)
    assert summary.minimum == pytest.approx(1.0)
    assert summary.maximum == pytest.approx(4.0)
    assert summary.standard_deviation == pytest.approx(1.2909944487)


def test_benchmark_summary_aggregates_raw_results() -> None:
    summary = BenchmarkSummary.from_results(
        "threads",
        [_result(1.0, workers_used=4), _result(
            2.0, workers_used=4), _result(3.0, workers_used=4)],
    )

    assert summary.strategy_name == "threads"
    assert summary.elapsed.average == pytest.approx(2.0)
    assert summary.elapsed.median == pytest.approx(2.0)
    assert summary.throughput.minimum == pytest.approx(4 / 3.0)
    assert summary.cpu_usage_percent is not None
    assert summary.memory_usage_mb is not None
    assert summary.workers_used == 4


def test_benchmark_runner_discards_warmup_runs() -> None:
    runner = BenchmarkRunner(repetitions=3, warmup_runs=1)
    calls = count(1)

    def execute_once() -> ExperimentResult:
        index = next(calls)
        return _result(float(index), workers_used=2)

    summary = runner.run(strategy_name="threads", execute_once=execute_once)

    assert summary.strategy_name == "threads"
    assert len(summary.runs) == 3
    assert [result.total_time_seconds for result in summary.runs] == [
        2.0, 3.0, 4.0]
    assert summary.elapsed.median == pytest.approx(3.0)
    assert summary.workers_used == 2


def test_benchmark_comparison_applies_speedup_against_baseline() -> None:
    baseline = BenchmarkSummary.from_results(
        "sequential",
        [_result(4.0), _result(4.0), _result(4.0)],
    )
    faster = BenchmarkSummary.from_results(
        "threads",
        [_result(2.0, workers_used=4), _result(
            2.0, workers_used=4), _result(2.0, workers_used=4)],
    )

    comparison = BenchmarkComparison.from_summaries(
        scenario_name="cpu",
        summaries=[baseline, faster],
        baseline_strategy="sequential",
    )

    assert comparison.scenario_name == "cpu"
    assert comparison.summaries[0].speedup == pytest.approx(1.0)
    assert comparison.summaries[1].speedup == pytest.approx(2.0)


def test_benchmark_comparison_without_baseline_keeps_speedup_empty() -> None:
    summary = BenchmarkSummary.from_results(
        "threads", [_result(1.0, workers_used=4)])

    comparison = BenchmarkComparison.from_summaries(
        scenario_name="cpu",
        summaries=[summary],
        baseline_strategy=None,
    )

    assert comparison.summaries[0].speedup is None


def test_benchmark_runner_rejects_invalid_configuration() -> None:
    with pytest.raises(ValueError):
        BenchmarkRunner(repetitions=0)

    with pytest.raises(ValueError):
        BenchmarkRunner(warmup_runs=-1)


def test_build_process_usage_uses_elapsed_time_and_cpu_count(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(measurement_module, "cpu_count", lambda: 2)

    usage = build_process_usage(
        ProcessSample(cpu_time_seconds=2.0, rss_bytes=10 * 1024 * 1024),
        ProcessSample(cpu_time_seconds=6.0, rss_bytes=30 * 1024 * 1024),
        elapsed_seconds=2.0,
    )

    assert usage.cpu_usage_percent == pytest.approx(100.0)
    assert usage.memory_usage_mb == pytest.approx(30.0)


def test_process_measurement_measures_duration_and_usage(monkeypatch: pytest.MonkeyPatch) -> None:
    before = ProcessSample(cpu_time_seconds=1.0, rss_bytes=10 * 1024 * 1024)
    after = ProcessSample(cpu_time_seconds=3.0, rss_bytes=14 * 1024 * 1024)
    times = iter([10.0, 13.0])

    monkeypatch.setattr(measurement_module,
                        "capture_process_usage", lambda: before)
    monkeypatch.setattr(measurement_module, "perf_counter",
                        lambda: next(times))
    monkeypatch.setattr(measurement_module, "cpu_count", lambda: 2)
    monkeypatch.setattr(measurement_module,
                        "capture_process_usage", lambda: before)

    def fake_capture() -> ProcessSample:
        calls = getattr(fake_capture, "calls", 0)
        setattr(fake_capture, "calls", calls + 1)
        return before if calls == 0 else after

    monkeypatch.setattr(measurement_module,
                        "capture_process_usage", fake_capture)

    measurement = measurement_module.ProcessMeasurement()
    result, elapsed_seconds, usage = measurement.measure(lambda: "ok")

    assert result == "ok"
    assert elapsed_seconds == pytest.approx(3.0)
    assert usage.cpu_usage_percent == pytest.approx((2.0 / 3.0 / 2.0) * 100)
    assert usage.memory_usage_mb == pytest.approx(14.0)

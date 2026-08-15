import streamlit as st
import pandas as pd
from concurrency_bench.application.benchmarks.models import BenchmarkComparison


def render_charts(comparison: BenchmarkComparison):
    strategies = [s.strategy_name for s in comparison.summaries]

    times = [s.elapsed.median for s in comparison.summaries]
    df_time = pd.DataFrame({"Tempo Mediano (s)": times}, index=strategies)
    st.subheader("Tempo Mediano por Estratégia (segundos)")
    st.bar_chart(df_time, x_label="Estratégia",
                 y_label="Tempo Mediano (segundos)")

    throughputs = [s.throughput.average for s in comparison.summaries]
    df_throughput = pd.DataFrame(
        {"Throughput Médio (tarefas/s)": throughputs}, index=strategies)
    st.subheader("Throughput Médio por Estratégia (tarefas/s)")
    st.bar_chart(df_throughput, x_label="Estratégia",
                 y_label="Throughput (tarefas por segundo)")

    speedup_values = [
        s.speedup for s in comparison.summaries if s.speedup is not None]
    if speedup_values and len(comparison.summaries) > 1:
        speedup_strategies = [
            s.strategy_name for s in comparison.summaries if s.speedup is not None]
        df_speedup = pd.DataFrame(
            {"Speedup": speedup_values}, index=speedup_strategies)
        st.subheader("Speedup Relativo")
        st.bar_chart(df_speedup, x_label="Estratégia",
                     y_label="Fator de Speedup")

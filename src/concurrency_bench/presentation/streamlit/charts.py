import io
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
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


def generate_matplotlib_figure(comparison: BenchmarkComparison):
    strategies = [s.strategy_name for s in comparison.summaries]
    times = [s.elapsed.median for s in comparison.summaries]
    throughputs = [s.throughput.average for s in comparison.summaries]

    cpu_usages = []
    mem_usages = []
    for s in comparison.summaries:
        cpu_avg = s.cpu_usage_percent.average if s.cpu_usage_percent else 0.0
        mem_avg = s.memory_usage_mb.average if s.memory_usage_mb else 0.0
        cpu_usages.append(cpu_avg)
        mem_usages.append(mem_avg)

    has_hw_metrics = any(c > 0 for c in cpu_usages) or any(m > 0 for m in mem_usages)

    num_plots = 4 if has_hw_metrics else 2
    nrows = 2 if num_plots == 4 else 1
    ncols = 2

    fig, axes = plt.subplots(
        nrows=nrows, ncols=ncols, figsize=(12, 8 if nrows == 2 else 5)
    )
    axes = axes.flatten() if num_plots > 1 else [axes]

    colors = ["#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78", "#2ca02c", "#98df8a"]

    ax1 = axes[0]
    bars1 = ax1.bar(strategies, times, color=colors[:len(strategies)], edgecolor="grey", alpha=0.85)
    ax1.set_title("Tempo Mediano de Execução\n(Menor é Melhor)", fontsize=10, fontweight="bold")
    ax1.set_ylabel("Tempo (segundos)", fontsize=8)
    ax1.grid(True, linestyle="--", alpha=0.5, axis="y")
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            yval,
            f"{yval:.4f}s",
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold"
        )

    ax2 = axes[1]
    bars2 = ax2.bar(strategies, throughputs, color=colors[:len(strategies)], edgecolor="grey", alpha=0.85)
    ax2.set_title("Throughput Médio\n(Maior é Melhor)", fontsize=10, fontweight="bold")
    ax2.set_ylabel("Tarefas por Segundo", fontsize=8)
    ax2.grid(True, linestyle="--", alpha=0.5, axis="y")
    for bar in bars2:
        yval = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            yval,
            f"{yval:.2f}",
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold"
        )

    if has_hw_metrics:
        ax3 = axes[2]
        bars3 = ax3.bar(strategies, cpu_usages, color=colors[:len(strategies)], edgecolor="grey", alpha=0.85)
        ax3.set_title("Uso Médio de CPU\n(Normalizado por Cores)", fontsize=10, fontweight="bold")
        ax3.set_ylabel("Consumo (%)", fontsize=8)
        ax3.grid(True, linestyle="--", alpha=0.5, axis="y")
        for bar in bars3:
            yval = bar.get_height()
            ax3.text(
                bar.get_x() + bar.get_width() / 2,
                yval,
                f"{yval:.1f}%",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold"
            )

        ax4 = axes[3]
        bars4 = ax4.bar(strategies, mem_usages, color=colors[:len(strategies)], edgecolor="grey", alpha=0.85)
        ax4.set_title("Uso Máximo de Memória (RSS)", fontsize=10, fontweight="bold")
        ax4.set_ylabel("Memória (MB)", fontsize=8)
        ax4.grid(True, linestyle="--", alpha=0.5, axis="y")
        for bar in bars4:
            yval = bar.get_height()
            ax4.text(
                bar.get_x() + bar.get_width() / 2,
                yval,
                f"{yval:.1f} MB",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold"
            )

    for ax in axes:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(axis="x", labelsize=8, rotation=15)

    fig.suptitle(f"Análise Especializada: {comparison.scenario_name}", fontsize=12, fontweight="bold", y=0.98)
    plt.tight_layout()
    return fig


def render_specialized_plots_and_export(comparison: BenchmarkComparison, key_prefix: str = ""):
    st.markdown("---")
    st.subheader("Gráficos Especializados (Matplotlib)")

    fig = generate_matplotlib_figure(comparison)
    st.pyplot(fig)

    img_buffer = io.BytesIO()
    fig.savefig(img_buffer, format="png", dpi=200, bbox_inches="tight")
    img_buffer.seek(0)

    metrics_data = []
    for s in comparison.summaries:
        cpu_avg = s.cpu_usage_percent.average if s.cpu_usage_percent else None
        mem_avg = s.memory_usage_mb.average if s.memory_usage_mb else None
        metrics_data.append({
            "strategy": s.strategy_name,
            "median_time_seconds": s.elapsed.median,
            "average_throughput_tasks_per_sec": s.throughput.average,
            "speedup": s.speedup,
            "cpu_avg_percent": cpu_avg,
            "memory_avg_mb": mem_avg,
            "workers_used": s.workers_used
        })

    import json
    json_data = json.dumps({
        "scenario_name": comparison.scenario_name,
        "results": metrics_data
    }, indent=2)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="Baixar Gráfico Comparativo (PNG)",
            data=img_buffer,
            file_name=f"grafico_{comparison.scenario_name.lower().replace(' ', '_')}.png",
            mime="image/png",
            key=f"{key_prefix}_download_png"
        )
    with col2:
        st.download_button(
            label="Exportar Métricas (JSON)",
            data=json_data,
            file_name=f"metricas_{comparison.scenario_name.lower().replace(' ', '_')}.json",
            mime="application/json",
            key=f"{key_prefix}_download_json"
        )

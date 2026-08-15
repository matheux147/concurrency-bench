import streamlit as st
import traceback

from concurrency_bench.domain.enums import ExperimentType
from concurrency_bench.presentation.streamlit.config import render_config
from concurrency_bench.presentation.streamlit.executor import (
    run_cpu_bound_experiment,
    run_io_bound_experiment,
    run_stock_experiment,
    load_experiment_history,
)
from concurrency_bench.presentation.streamlit.tables import (
    build_comparison_table,
    build_stock_table,
)
from concurrency_bench.presentation.streamlit.charts import (
    render_charts,
    render_specialized_plots_and_export,
)


def main():
    st.set_page_config(
        page_title="Concurrency Lab - Painel de Controle",
        page_icon=None,
        layout="wide",
    )

    st.title("Laboratório Concorrente")
    st.markdown(
        """
        Este painel permite simular e analisar o desempenho de diferentes estratégias de concorrência 
        em Python sob cargas de trabalho variadas: CPU-bound, I/O-bound (HTTP) e transações concorrentes de estoque (PostgreSQL / Memória).
        """
    )

    tab_exec, tab_hist = st.tabs(
        ["Executar Novo Experimento", "Histórico de Experimentos"])

    with tab_exec:
        scenario_type, config, is_valid = render_config()

        if not is_valid:
            st.warning(
                "Por favor, corrija as configurações incorretas na barra lateral antes de continuar.")
        else:
            st.sidebar.markdown("---")
            run_clicked = st.sidebar.button(
                "Executar Experimento", type="primary")

            if run_clicked:
                st.session_state["last_scenario"] = scenario_type
                st.session_state["results"] = None
                st.session_state["stocks_map"] = None

                with st.spinner("Executando o benchmark, por favor aguarde..."):
                    try:
                        if scenario_type == "CPU-bound":
                            comparison = run_cpu_bound_experiment(config)
                            st.session_state["results"] = comparison
                        elif scenario_type == "I/O-bound HTTP":
                            comparison = run_io_bound_experiment(config)
                            st.session_state["results"] = comparison
                        elif scenario_type == "Stock / PostgreSQL":
                            comparison, stocks_map = run_stock_experiment(
                                config)
                            st.session_state["results"] = comparison
                            st.session_state["stocks_map"] = stocks_map
                    except Exception as e:
                        st.error(
                            "Ocorreu um erro durante a execução do experimento.")
                        st.exception(e)
                        st.text_area("Traceback detalhado para diagnóstico:",
                                     value=traceback.format_exc(), height=200)

            if (
                st.session_state.get("results") is not None
                and st.session_state.get("last_scenario") == scenario_type
            ):
                comparison = st.session_state["results"]
                st.success(
                    f"Experimento '{comparison.scenario_name}' concluído com sucesso!")

                st.header("Resumo dos Resultados")

                if scenario_type == "Stock / PostgreSQL":
                    stocks_map = st.session_state.get("stocks_map", {})
                    stock_df = build_stock_table(
                        comparison, stocks_map, config.initial_stock)

                    st.dataframe(stock_df, use_container_width=True)

                    for idx, row in stock_df.iterrows():
                        with st.expander(f"Cenário: {row['Cenário']}", expanded=True):
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric(
                                "Estoque Inicial -> Final", f"{row['Estoque Inicial']} -> {row['Estoque Final']}")
                            c2.metric("Aprovadas / Rejeitadas",
                                      f"{row['Aprovadas']} / {row['Rejeitadas']}")
                            c3.metric("Tempo Médio",
                                      f"{row['Tempo Médio (s)']}")
                            c4.metric(
                                "Throughput Médio", f"{row['Throughput Médio (tentativas/s)']} tent/s")

                            if row["Inconsistência"] != "Não":
                                st.error(
                                    f"Inconsistências detectadas: {row['Inconsistência']}")
                            else:
                                st.info(
                                    "Consistência do estoque mantida com sucesso.")
                else:
                    comp_df = build_comparison_table(comparison)
                    st.dataframe(comp_df, use_container_width=True)

                    for summary in comparison.summaries:
                        with st.expander(f"Estratégia: {summary.strategy_name}", expanded=True):
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("Tempo Mediano",
                                      f"{summary.elapsed.median:.4f}s")
                            c2.metric(
                                "Throughput Médio", f"{summary.throughput.average:.2f} tarefas/s")

                            speedup_str = f"{summary.speedup:.2f}x" if summary.speedup is not None else "N/D"
                            c3.metric("Speedup (vs Sequential)", speedup_str)

                            cpu_avg = summary.cpu_usage_percent.average if summary.cpu_usage_percent else None
                            mem_avg = summary.memory_usage_mb.average if summary.memory_usage_mb else None
                            cpu_str = f"{cpu_avg:.1f}%" if cpu_avg is not None else "N/D"
                            mem_str = f"{mem_avg:.1f} MB" if mem_avg is not None else "N/D"
                            c4.metric("CPU / Memória",
                                      f"{cpu_str} / {mem_str}")

                st.markdown("---")
                st.header("Gráficos Comparativos")
                render_charts(comparison)
                render_specialized_plots_and_export(comparison, key_prefix="exec")
            else:
                st.info(
                    "Configure os parâmetros na barra lateral e clique em 'Executar Experimento' para iniciar.")

    with tab_hist:
        st.subheader("Histórico de Experimentos Salvos")
        history = load_experiment_history()

        if not history:
            st.info("Nenhum experimento encontrado no histórico do banco de dados.")
        else:
            options = []
            lookup = {}
            for exp, comp, stocks_map in history:
                label = f"[{exp.experiment_type.value.upper()}] - {exp.name} ({exp.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC) - ID: {str(exp.id)[:8]}"
                options.append(label)
                lookup[label] = (exp, comp, stocks_map)

            selected_label = st.selectbox(
                "Selecione o experimento para visualizar", options)

            if selected_label:
                exp, comp, stocks_map = lookup[selected_label]

                st.markdown("### Detalhes do Experimento")
                c1, c2, c3 = st.columns(3)
                c1.write(f"**Nome:** {exp.name}")
                c2.write(f"**Tipo:** {exp.experiment_type.value}")
                c3.write(
                    f"**Data:** {exp.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC")

                st.write(f"**ID:** {str(exp.id)}")
                st.write(f"**Carga de Tarefas:** {exp.task_count}")
                st.write(f"**Parâmetros:** {dict(exp.parameters)}")

                st.markdown("---")
                st.subheader("Resumo dos Resultados Salvos")

                if exp.experiment_type == ExperimentType.DATABASE:
                    initial_stock = exp.parameters.get("initial_stock", 10)
                    stock_df = build_stock_table(
                        comp, stocks_map, initial_stock)
                    st.dataframe(stock_df, use_container_width=True)

                    for idx, row in stock_df.iterrows():
                        with st.expander(f"Cenário: {row['Cenário']}", expanded=True):
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric(
                                "Estoque Inicial -> Final", f"{row['Estoque Inicial']} -> {row['Estoque Final']}")
                            c2.metric("Aprovadas / Rejeitadas",
                                      f"{row['Aprovadas']} / {row['Rejeitadas']}")
                            c3.metric("Tempo Médio",
                                      f"{row['Tempo Médio (s)']}")
                            c4.metric(
                                "Throughput Médio", f"{row['Throughput Médio (tentativas/s)']} tent/s")

                            if row["Inconsistência"] != "Não":
                                st.error(
                                    f"Inconsistências detectadas: {row['Inconsistência']}")
                            else:
                                st.info(
                                    "Consistência do estoque mantida com sucesso.")
                else:
                    comp_df = build_comparison_table(comp)
                    st.dataframe(comp_df, use_container_width=True)

                    for summary in comp.summaries:
                        with st.expander(f"Estratégia: {summary.strategy_name}", expanded=True):
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("Tempo Mediano",
                                      f"{summary.elapsed.median:.4f}s")
                            c2.metric(
                                "Throughput Médio", f"{summary.throughput.average:.2f} tarefas/s")

                            speedup_str = f"{summary.speedup:.2f}x" if summary.speedup is not None else "N/D"
                            c3.metric("Speedup (vs Sequential)", speedup_str)

                            cpu_avg = summary.cpu_usage_percent.average if summary.cpu_usage_percent else None
                            mem_avg = summary.memory_usage_mb.average if summary.memory_usage_mb else None
                            cpu_str = f"{cpu_avg:.1f}%" if cpu_avg is not None else "N/D"
                            mem_str = f"{mem_avg:.1f} MB" if mem_avg is not None else "N/D"
                            c4.metric("CPU / Memória",
                                      f"{cpu_str} / {mem_str}")

                st.markdown("---")
                st.subheader("Gráficos do Experimento")
                render_charts(comp)
                render_specialized_plots_and_export(comp, key_prefix=f"hist_{exp.id}")


if __name__ == "__main__":
    main()

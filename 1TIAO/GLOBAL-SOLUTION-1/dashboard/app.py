
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)


# ==================================================
# 1. CONFIGURAÇÕES
# ==================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

RAW_FILE = (
    ROOT_DIR / "data" / "raw" / "smart_meter_data.csv"
)

AI_FILE = (
    ROOT_DIR / "data" / "processed"
    / "anomaly_detection_results.csv"
)

st.set_page_config(
    page_title="Smart Energy AI",
    page_icon="⚡",
    layout="wide",
)


# ==================================================
# 2. IDENTIDADE VISUAL
# ==================================================

st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }

    [data-testid="stSidebar"] {
        background-color: #111B2B;
    }

    [data-testid="stMetric"] {
        background-color: #172333;
        border: 1px solid #26364A;
        padding: 18px;
        border-radius: 12px;
    }

    [data-testid="stMetricLabel"] {
        color: #A8B8CC;
    }

    [data-testid="stMetricValue"] {
        color: #F1F5F9;
    }

    div[data-testid="stPlotlyChart"] {
        background-color: #111B2B;
        border: 1px solid #26364A;
        border-radius: 12px;
        padding: 10px;
    }

    hr {
        border-color: #26364A;
    }
</style>
""", unsafe_allow_html=True)


# ==================================================
# 3. CABEÇALHO
# ==================================================

st.markdown("""
# ⚡ Smart Energy AI

**ENERGY INTELLIGENCE PLATFORM**

Sistema inteligente de monitoramento e análise
do consumo de energia elétrica.

<small>
Monitoramento energético | Análise de padrões |
Detecção de anomalias com Inteligência Artificial
</small>
""", unsafe_allow_html=True)

st.divider()


# ==================================================
# 4. CARREGAMENTO DOS DADOS
# ==================================================

@st.cache_data
def load_monitoring_data(file_path, file_mtime):

    df = pd.read_csv(file_path)

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df = df.sort_values("timestamp").reset_index(drop=True)

    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour

    return df


@st.cache_data
def load_ai_data(file_path, file_mtime):

    df = pd.read_csv(file_path)

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df = df.sort_values("timestamp").reset_index(drop=True)

    df["date"] = df["timestamp"].dt.date

    df["is_injected_anomaly"] = (
        df["is_injected_anomaly"]
        .astype(str)
        .str.lower()
        .map({
            "true": 1,
            "false": 0,
            "1": 1,
            "0": 0,
        })
    )

    if df["is_injected_anomaly"].isna().any():
        raise ValueError("Rótulos de validação inválidos.")

    df["is_injected_anomaly"] = (
        df["is_injected_anomaly"].astype(int)
    )

    df["predicted_anomaly"] = (
        df["predicted_anomaly"].astype(int)
    )

    return df


try:

    monitoring_df = load_monitoring_data(
        str(RAW_FILE),
        RAW_FILE.stat().st_mtime,
    )

    ai_df = load_ai_data(
        str(AI_FILE),
        AI_FILE.stat().st_mtime,
    )

except FileNotFoundError as error:

    st.error(f"Arquivo não encontrado: {error}")
    st.stop()

except Exception as error:

    st.error(f"Erro ao carregar os dados: {error}")
    st.stop()


# ==================================================
# 5. ABAS PRINCIPAIS
# ==================================================

tab_monitoring, tab_ai = st.tabs([
    "⚡ Monitoramento",
    "🤖 Validação da IA",
])


# ==================================================
# ABA 1 - MONITORAMENTO ENERGÉTICO
# ==================================================

with tab_monitoring:

    st.header("Monitoramento energético")

    st.caption(
        "Análise do comportamento original de consumo "
        "do estabelecimento, sem anomalias artificiais."
    )

    # Filtro de período
    min_date = monitoring_df["date"].min()
    max_date = monitoring_df["date"].max()

    selected_dates = st.date_input(
        "Período de monitoramento",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="monitoring_dates",
    )

    if isinstance(selected_dates, (tuple, list)):

        if len(selected_dates) == 2:
            start_date, end_date = selected_dates
        else:
            start_date = selected_dates[0]
            end_date = selected_dates[0]

    else:
        start_date = selected_dates
        end_date = selected_dates

    monitor = monitoring_df[
        (monitoring_df["date"] >= start_date)
        & (monitoring_df["date"] <= end_date)
    ].copy()

    if monitor.empty:

        st.warning("Não existem medições nesse período.")

    else:

        # Indicadores
        total_energy = monitor["energy_kwh_interval"].sum()

        average_power = monitor["power_w"].mean()

        maximum_power = monitor["power_w"].max()

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Consumo acumulado",
            f"{total_energy:.2f} kWh",
        )

        col2.metric(
            "Potência média",
            f"{average_power:.2f} W",
        )

        col3.metric(
            "Potência máxima",
            f"{maximum_power:.2f} W",
        )

        st.divider()

        # Histórico de potência
        st.subheader("Histórico de potência")

        fig_power = px.line(
            monitor,
            x="timestamp",
            y="power_w",
            labels={
                "timestamp": "Data e hora",
                "power_w": "Potência (W)",
            },
            title="Comportamento da potência elétrica",
        )

        fig_power.update_traces(
            line=dict(color="#38BDF8", width=1.5)
        )

        fig_power.update_layout(
            template="plotly_dark",
            paper_bgcolor="#111B2B",
            plot_bgcolor="#111B2B",
            height=420,
            hovermode="x unified",
        )

        st.plotly_chart(
            fig_power,
            use_container_width=True,
        )

        # Consumo diário
        st.subheader("Consumo diário")

        daily_energy = (
            monitor
            .groupby("date", as_index=False)
            ["energy_kwh_interval"]
            .sum()
        )

        fig_daily = px.bar(
            daily_energy,
            x="date",
            y="energy_kwh_interval",
            labels={
                "date": "Data",
                "energy_kwh_interval": "Energia (kWh)",
            },
            title="Energia consumida por dia",
        )

        fig_daily.update_traces(
            marker_color="#38BDF8"
        )

        fig_daily.update_layout(
            template="plotly_dark",
            paper_bgcolor="#111B2B",
            plot_bgcolor="#111B2B",
            height=350,
        )

        st.plotly_chart(
            fig_daily,
            use_container_width=True,
        )

        # Perfil por horário
        st.subheader("Perfil médio de consumo por horário")

        hourly_profile = (
            monitor
            .groupby("hour", as_index=False)["power_w"]
            .mean()
        )

        fig_hourly = px.bar(
            hourly_profile,
            x="hour",
            y="power_w",
            labels={
                "hour": "Hora do dia",
                "power_w": "Potência média (W)",
            },
            title="Potência média em cada hora",
        )

        fig_hourly.update_traces(
            marker_color="#F59E0B"
        )

        fig_hourly.update_layout(
            template="plotly_dark",
            paper_bgcolor="#111B2B",
            plot_bgcolor="#111B2B",
            height=350,
            xaxis=dict(
                tickmode="linear",
                dtick=1,
            ),
        )

        st.plotly_chart(
            fig_hourly,
            use_container_width=True,
        )

        st.caption(
            "Fonte: conjunto de dados sintético gerado "
            "pelo projeto Smart Energy AI."
        )


# ==================================================
# ABA 2 - VALIDAÇÃO DA INTELIGÊNCIA ARTIFICIAL
# ==================================================

with tab_ai:

    st.header("Validação da Inteligência Artificial")

    st.caption(
        "Avaliação experimental do Isolation Forest "
        "utilizando medições com anomalias artificiais conhecidas."
    )

    # Filtro de período
    min_ai_date = ai_df["date"].min()
    max_ai_date = ai_df["date"].max()

    selected_ai_dates = st.date_input(
        "Período de validação",
        value=(min_ai_date, max_ai_date),
        min_value=min_ai_date,
        max_value=max_ai_date,
        key="ai_dates",
    )

    if isinstance(selected_ai_dates, (tuple, list)):

        if len(selected_ai_dates) == 2:
            ai_start, ai_end = selected_ai_dates
        else:
            ai_start = selected_ai_dates[0]
            ai_end = selected_ai_dates[0]

    else:
        ai_start = selected_ai_dates
        ai_end = selected_ai_dates

    validation = ai_df[
        (ai_df["date"] >= ai_start)
        & (ai_df["date"] <= ai_end)
    ].copy()

    if validation.empty:

        st.warning("Não existem registros nesse período.")

    else:

        y_true = validation[
            "is_injected_anomaly"
        ].astype(int)

        y_pred = validation[
            "predicted_anomaly"
        ].astype(int)

        detected = int(y_pred.sum())
        known = int(y_true.sum())

        # Indicadores
        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Registros avaliados",
            f"{len(validation):,}".replace(",", "."),
        )

        col2.metric(
            "Anomalias conhecidas",
            known,
        )

        col3.metric(
            "Anomalias detectadas",
            detected,
        )

        st.divider()

        # Métricas
        st.subheader("Desempenho do modelo")

        precision = precision_score(
            y_true,
            y_pred,
            zero_division=0,
        )

        recall = recall_score(
            y_true,
            y_pred,
            zero_division=0,
        )

        f1 = f1_score(
            y_true,
            y_pred,
            zero_division=0,
        )

        metric1, metric2, metric3 = st.columns(3)

        metric1.metric(
            "Precision",
            f"{precision * 100:.2f}%",
        )

        metric2.metric(
            "Recall",
            f"{recall * 100:.2f}%",
        )

        metric3.metric(
            "F1-score",
            f"{f1 * 100:.2f}%",
        )

        st.caption(
            "As métricas comparam as previsões do modelo "
            "com os rótulos artificiais da base de validação."
        )

        st.divider()

        # Gráfico de detecção
        st.subheader("Medições normais e anomalias detectadas")

        plot_df = validation.copy()

        plot_df["classification"] = (
            plot_df["predicted_anomaly"]
            .map({
                0: "Normal",
                1: "Anomalia detectada",
            })
        )

        fig_anomalies = px.scatter(
            plot_df,
            x="timestamp",
            y="power_w",
            color="classification",
            color_discrete_map={
                "Normal": "#38BDF8",
                "Anomalia detectada": "#EF4444",
            },
            category_orders={
                "classification": [
                    "Normal",
                    "Anomalia detectada",
                ]
            },
            labels={
                "timestamp": "Data e hora",
                "power_w": "Potência (W)",
                "classification": "Classificação",
            },
        )

        fig_anomalies.update_layout(
            template="plotly_dark",
            paper_bgcolor="#111B2B",
            plot_bgcolor="#111B2B",
            height=420,
        )

        st.plotly_chart(
            fig_anomalies,
            use_container_width=True,
        )

        # Eventos suspeitos
        st.subheader("Eventos sinalizados pelo modelo")

        events = validation[
            validation["predicted_anomaly"] == 1
        ].copy()

        display_columns = [
            "timestamp",
            "power_w",
            "current_a",
            "hour",
            "power_deviation_ratio",
            "anomaly_score",
        ]

        available_columns = [
            col for col in display_columns
            if col in events.columns
        ]

        events = events[
            available_columns
        ].sort_values(
            "anomaly_score",
            ascending=False,
        )

        st.dataframe(
            events,
            use_container_width=True,
            hide_index=True,
        )

        # Matriz de confusão
        st.subheader("Matriz de confusão")

        matrix = confusion_matrix(
            y_true,
            y_pred,
            labels=[0, 1],
        )

        tn, fp, fn, tp = matrix.ravel()

        matrix_df = pd.DataFrame(
            matrix,
            index=["Real normal", "Real anomalia"],
            columns=["Previsto normal", "Previsto anomalia"],
        )

        st.dataframe(
            matrix_df,
            use_container_width=True,
        )

        st.caption(
            f"Verdadeiros negativos: {tn} | "
            f"Falsos positivos: {fp} | "
            f"Falsos negativos: {fn} | "
            f"Verdadeiros positivos: {tp}"
        )

        st.info(
            "Esta avaliação utiliza anomalias artificiais. "
            "Os resultados não representam uma validação "
            "em medidores ou instalações reais."
        )


# ==================================================
# RODAPÉ
# ==================================================

st.divider()

st.caption(
    "Smart Energy AI | FIAP Global Solution | "
    "Protótipo acadêmico com dados simulados"
)

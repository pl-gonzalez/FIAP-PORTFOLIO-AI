
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"

st.set_page_config(
    page_title="Monitoramento",
    page_icon="📡",
    layout="wide",
)

st.title("📡 Monitoramento da Frota")
st.caption("Acompanhamento da telemetria e identificação de alertas operacionais.")

@st.cache_data
def load_data():
    telemetry = pd.read_csv(DATA_DIR / "telemetry_validated.csv")
    metrics = pd.read_csv(DATA_DIR / "telemetry_metrics.csv")
    return telemetry, metrics

try:
    telemetry, metrics = load_data()
except FileNotFoundError as error:
    st.error(f"Arquivo não encontrado: {error}")
    st.info(
        "Verifique se os arquivos de telemetria processada "
        "estão disponíveis em data/processed."
    )
    st.stop()

# Seleção do veículo
vehicles = sorted(telemetry["vehicle_id"].dropna().unique())

selected_vehicle = st.selectbox(
    "Selecione o veículo:",
    vehicles,
)

vehicle_data = telemetry[
    telemetry["vehicle_id"] == selected_vehicle
].copy()

vehicle_metrics = metrics[
    metrics["vehicle_id"] == selected_vehicle
]

if vehicle_data.empty or vehicle_metrics.empty:
    st.warning("Não existem dados suficientes para este veículo.")
    st.stop()

summary = vehicle_metrics.iloc[0]

st.divider()
st.subheader(f"Indicadores — {selected_vehicle}")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Leituras recebidas",
    int(summary["total_readings"]),
)

col2.metric(
    "Taxa de alertas",
    f'{summary["alert_rate_pct"]:.2f}%',
)

col3.metric(
    "RPM máximo",
    f'{summary["max_rpm"]:.0f}',
)

col4.metric(
    "Temperatura máxima",
    f'{summary["max_engine_temp_c"]:.1f} °C',
)

st.divider()
st.subheader("Comportamento da telemetria")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("**Velocidade (km/h)**")
    st.line_chart(
        vehicle_data.set_index("timestamp_ms")[["speed_kmh"]]
    )

with chart_col2:
    st.markdown("**Rotação do motor (RPM)**")
    st.line_chart(
        vehicle_data.set_index("timestamp_ms")[["rpm"]]
    )

chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    st.markdown("**Nível de combustível (%)**")
    st.line_chart(
        vehicle_data.set_index("timestamp_ms")[["fuel_pct"]]
    )

with chart_col4:
    st.markdown("**Temperatura do motor (°C)**")
    st.line_chart(
        vehicle_data.set_index("timestamp_ms")[["engine_temp_c"]]
    )

st.divider()
st.subheader("Alertas operacionais")

alert_rows = vehicle_data[
    vehicle_data["alerts"].fillna("NONE") != "NONE"
].copy()

if alert_rows.empty:
    st.success("Nenhum alerta identificado nas leituras.")
else:
    st.warning(
        f"{len(alert_rows)} leituras apresentaram alertas "
        "na simulação."
    )

    st.dataframe(
        alert_rows[
            [
                "timestamp_ms",
                "speed_kmh",
                "rpm",
                "engine_temp_c",
                "alerts",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

st.divider()
st.subheader("Histórico completo de telemetria")

st.dataframe(
    vehicle_data,
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "Dados simulados no Wokwi com ESP32. "
    "Os alertas representam condições definidas para fins acadêmicos."
)


from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"

st.set_page_config(
    page_title="Benchmark da Frota",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Benchmark da Frota")
st.caption("Comparação de custos e eficiência energética entre veículos.")

@st.cache_data
def load_data():
    metrics = pd.read_csv(DATA_DIR / "fleet_vehicle_metrics.csv")
    benchmark = pd.read_csv(DATA_DIR / "fleet_benchmark_by_type.csv")
    ranking = pd.read_csv(DATA_DIR / "fleet_efficiency_ranking.csv")
    return metrics, benchmark, ranking

try:
    metrics, benchmark, ranking = load_data()
except FileNotFoundError as error:
    st.error(f"Arquivo não encontrado: {error}")
    st.stop()

st.subheader("Indicadores por tipo de veículo")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Custo médio por quilômetro (R$/km)**")
    st.bar_chart(
        benchmark.set_index("vehicle_type")[["cost_km_mean"]]
    )

with col2:
    st.markdown("**Consumo médio (km/L)**")
    st.bar_chart(
        benchmark.set_index("vehicle_type")[["km_l_mean"]]
    )

st.divider()

st.subheader("Estatísticas do benchmark")
st.dataframe(
    benchmark.round(2),
    use_container_width=True,
    hide_index=True,
)

st.divider()

st.subheader("Ranking individual dos veículos")

metric = st.selectbox(
    "Ordenar ranking por:",
    ["cost_per_km", "km_per_liter"],
    format_func=lambda value: (
        "Custo por km" if value == "cost_per_km"
        else "Consumo (km/L)"
    ),
)

ascending = metric == "cost_per_km"

ranking_view = ranking.sort_values(
    by=metric,
    ascending=ascending,
)

columns = [
    "vehicle_id",
    "vehicle_type",
    "cost_per_km",
    "cost_km_mean",
    "cost_gap_pct",
    "km_per_liter",
    "km_l_mean",
    "km_l_gap_pct",
]

available_columns = [
    column for column in columns
    if column in ranking_view.columns
]

st.dataframe(
    ranking_view[available_columns].round(2),
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "Os indicadores são calculados a partir de dados sintéticos "
    "e devem ser interpretados como demonstração acadêmica."
)


from pathlib import Path

import pandas as pd
import streamlit as st

# --------------------------------------------------
# CONFIGURAÇÃO
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"

st.set_page_config(
    page_title="Fleet Intelligence",
    page_icon="🚘",
    layout="wide",
)

# --------------------------------------------------
# ESTILO
# --------------------------------------------------

st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    [data-testid="stMetric"] {
        background-color: rgba(128, 128, 128, 0.08);
        padding: 16px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# CARREGAMENTO DE DADOS
# --------------------------------------------------

@st.cache_data
def load_data():
    ranking = pd.read_csv(
        DATA_DIR / "fleet_efficiency_ranking.csv"
    )

    diagnosis = pd.read_csv(
        DATA_DIR / "efficiency_diagnosis.csv"
    )

    return ranking, diagnosis


try:
    ranking, diagnosis = load_data()

except FileNotFoundError as error:
    st.error(f"Arquivo não encontrado: {error}")
    st.stop()


# --------------------------------------------------
# CABEÇALHO
# --------------------------------------------------

st.title("🚘 Fleet Intelligence")

st.subheader("Inteligência e diagnóstico de frotas")

st.caption(
    "Plataforma acadêmica de análise de custos, "
    "eficiência operacional e diagnóstico inteligente."
)

st.divider()


# --------------------------------------------------
# INDICADORES
# --------------------------------------------------

total_vehicles = ranking["vehicle_id"].nunique()

total_cost = ranking["total_cost_brl"].sum()

total_distance = ranking["total_distance_km"].sum()

total_liters = ranking["total_fuel_liters"].sum()

average_km_l = (
    total_distance / total_liters
    if total_liters > 0
    else 0
)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Veículos analisados",
    f"{total_vehicles}",
)

col2.metric(
    "Custo total",
    f"R$ {total_cost:,.2f}",
)

col3.metric(
    "Distância percorrida",
    f"{total_distance:,.0f} km",
)

col4.metric(
    "Consumo médio",
    f"{average_km_l:.2f} km/L",
)

st.divider()


# --------------------------------------------------
# DIAGNÓSTICO DA FROTA
# --------------------------------------------------

st.subheader("Diagnóstico da frota")

class_order = [
    "EFICIENTE",
    "ATENÇÃO",
    "INEFICIENTE",
]

class_counts = (
    diagnosis["efficiency_class"]
    .value_counts()
    .reindex(class_order, fill_value=0)
)

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("**Distribuição das classificações**")
    st.dataframe(
        class_counts.rename("Veículos"),
        use_container_width=True,
    )

with col2:
    st.markdown("**Distribuição visual**")
    st.bar_chart(class_counts)


# --------------------------------------------------
# RANKING DE VEÍCULOS
# --------------------------------------------------

st.divider()

st.subheader("Visão geral dos veículos")

columns_to_show = [
    "vehicle_id",
    "vehicle_type",
    "total_cost_brl",
    "cost_per_km",
    "km_per_liter",
    "cost_status",
    "fuel_status",
]

available_columns = [
    col for col in columns_to_show
    if col in ranking.columns
]

st.dataframe(
    ranking[available_columns].round(2),
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "Fonte: dataset acadêmico sintético da Sprint 2. "
    "Os indicadores representam dados simulados."
)

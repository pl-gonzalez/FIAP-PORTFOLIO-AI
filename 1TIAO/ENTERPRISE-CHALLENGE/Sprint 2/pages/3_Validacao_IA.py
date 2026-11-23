
from pathlib import Path
import json

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"
FIGURES_DIR = BASE_DIR / "reports" / "figures"

st.set_page_config(
    page_title="Validação da IA",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Validação da Inteligência Artificial")
st.caption(
    "Avaliação experimental do classificador e comparação "
    "com o diagnóstico baseado em regras."
)


def load_csv(filename):
    path = DATA_DIR / filename
    return pd.read_csv(path) if path.exists() else None


def show_figure(filename, caption):
    path = FIGURES_DIR / filename

    if path.exists():
        st.image(str(path), caption=caption, width=600)
    else:
        st.info(f"Imagem não encontrada: {filename}")


# Carregamento dos dados
diagnosis = load_csv("efficiency_diagnosis.csv")
predictions = load_csv("ml_test_predictions.csv")
comparison = load_csv("ml_rules_comparison.csv")
confusion_matrix = load_csv("ml_confusion_matrix.csv")

if diagnosis is None:
    st.error("Arquivo efficiency_diagnosis.csv não encontrado.")
    st.stop()

st.divider()
st.subheader("1. Diagnóstico da frota")

class_order = ["EFICIENTE", "ATENÇÃO", "INEFICIENTE"]

class_counts = (
    diagnosis["efficiency_class"]
    .value_counts()
    .reindex(class_order, fill_value=0)
)

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Distribuição das classificações**")
    st.bar_chart(class_counts)

with col2:
    st.markdown("**Quantidade por classificação**")
    st.dataframe(
        class_counts.rename("Veículos"),
        use_container_width=True,
    )

st.divider()
st.subheader("2. Desempenho do modelo de Machine Learning")

metrics_path = DATA_DIR / "ml_metrics.json"

if metrics_path.exists():
    with open(metrics_path, "r", encoding="utf-8") as file:
        ml_metrics = json.load(file)

    # Exibe métricas numéricas encontradas no JSON
    numeric_metrics = {
        key: value
        for key, value in ml_metrics.items()
        if isinstance(value, (int, float))
        and not isinstance(value, bool)
    }

    if numeric_metrics:
        metric_cols = st.columns(len(numeric_metrics))

        for column, (name, value) in zip(
            metric_cols, numeric_metrics.items()
        ):
            column.metric(
                name.replace("_", " ").title(),
                f"{value:.2%}" if 0 <= value <= 1 else f"{value:.2f}",
            )
    else:
        st.json(ml_metrics)
else:
    st.info("Arquivo ml_metrics.json não encontrado.")

st.markdown("**Matriz de confusão**")

if confusion_matrix is not None:
    st.dataframe(
        confusion_matrix,
        use_container_width=True,
        hide_index=True,
    )
else:
    show_figure(
        "05_ml_confusion_matrix.png",
        "Matriz de confusão do classificador",
    )

st.divider()
st.subheader("3. Comparação: regras x Machine Learning")

if comparison is not None:
    col1, col2, col3 = st.columns(3)

    total = len(comparison)
    agreements = int(comparison["agreement"].sum())
    disagreements = total - agreements

    col1.metric("Veículos avaliados", total)
    col2.metric("Concordâncias", agreements)
    col3.metric("Divergências", disagreements)

    if total > 0:
        agreement_rate = agreements / total * 100
        st.metric("Taxa de concordância", f"{agreement_rate:.2f}%")

    st.markdown("**Resultado por veículo**")
    st.dataframe(
        comparison,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("Arquivo ml_rules_comparison.csv não encontrado.")

st.divider()
st.subheader("4. Previsões do classificador")

if predictions is not None:
    st.dataframe(
        predictions,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("Arquivo ml_test_predictions.csv não encontrado.")

st.divider()
st.subheader("5. Análise visual")

show_figure(
    "06_rules_vs_ml.png",
    "Comparação entre regras e Machine Learning",
)

st.caption(
    "O classificador é experimental. A base possui apenas 12 veículos, "
    "com 4 amostras no conjunto de teste. As classificações utilizadas "
    "como referência foram produzidas por regras, não por avaliação "
    "independente de especialistas."
)


from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"
FIGURES_DIR = BASE_DIR / "reports" / "figures"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def load_csv(filename):
    path = DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    return pd.read_csv(path)


def save_figure(filename):
    path = FIGURES_DIR / filename
    plt.tight_layout()
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()
    print(f"Gráfico gerado: {path}")


def plot_cost_per_km():
    df = load_csv("fleet_efficiency_ranking.csv")

    required = ["vehicle_id", "cost_per_km", "cost_km_mean"]
    if not set(required).issubset(df.columns):
        raise ValueError("Colunas necessárias para o gráfico de custo/km não encontradas.")

    df = df.sort_values("vehicle_id")

    plt.figure(figsize=(11, 5))
    plt.bar(df["vehicle_id"], df["cost_per_km"], label="Custo por km")
    plt.plot(
        df["vehicle_id"],
        df["cost_km_mean"],
        marker="o",
        label="Média do tipo de veículo",
    )

    plt.title("Custo por quilômetro por veículo")
    plt.xlabel("Veículo")
    plt.ylabel("Custo (R$/km)")
    plt.legend()
    plt.grid(axis="y", alpha=0.3)

    save_figure("01_cost_per_km.png")


def plot_fuel_efficiency():
    df = load_csv("fleet_efficiency_ranking.csv")

    required = ["vehicle_id", "km_per_liter", "km_l_mean"]
    if not set(required).issubset(df.columns):
        raise ValueError("Colunas necessárias para o gráfico de consumo não encontradas.")

    df = df.sort_values("vehicle_id")

    plt.figure(figsize=(11, 5))
    plt.bar(df["vehicle_id"], df["km_per_liter"], label="Consumo do veículo")
    plt.plot(
        df["vehicle_id"],
        df["km_l_mean"],
        marker="o",
        label="Média do tipo de veículo",
    )

    plt.title("Eficiência de combustível por veículo")
    plt.xlabel("Veículo")
    plt.ylabel("Quilômetros por litro (km/L)")
    plt.legend()
    plt.grid(axis="y", alpha=0.3)

    save_figure("02_fuel_efficiency.png")


def plot_diagnosis_distribution():
    df = load_csv("efficiency_diagnosis.csv")

    if "efficiency_class" not in df.columns:
        raise ValueError("Coluna efficiency_class não encontrada.")

    order = ["EFICIENTE", "ATENÇÃO", "INEFICIENTE"]
    counts = (
        df["efficiency_class"]
        .value_counts()
        .reindex(order, fill_value=0)
    )

    plt.figure(figsize=(8, 5))
    bars = plt.bar(counts.index, counts.values)

    plt.title("Distribuição do diagnóstico por regras")
    plt.xlabel("Classificação")
    plt.ylabel("Quantidade de veículos")
    plt.grid(axis="y", alpha=0.3)

    for bar, value in zip(bars, counts.values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            str(value),
            ha="center",
            va="bottom",
        )

    save_figure("03_diagnosis_distribution.png")



def plot_telemetry_alerts():
    df = load_csv("telemetry_metrics.csv")

    if df.empty:
        print("Sem dados de telemetria para gerar o gráfico.")
        return

    row = df.iloc[0]

    total = int(row["total_readings"])
    alerts = int(row["alert_readings"])
    without_alerts = total - alerts

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Distribuição das leituras
    labels = ["Com alertas", "Sem alertas"]
    values = [alerts, without_alerts]

    axes[0].bar(labels, values)
    axes[0].set_title("Leituras da simulação ESP32")
    axes[0].set_ylabel("Quantidade de leituras")
    axes[0].grid(axis="y", alpha=0.3)

    for i, value in enumerate(values):
        axes[0].text(i, value, str(value), ha="center", va="bottom")

    # Indicadores operacionais
    axes[1].axis("off")
    axes[1].set_title("Indicadores operacionais - V007")

    metrics = [
        f"Total de leituras: {total}",
        f"Taxa de alertas: {row['alert_rate_pct']:.2f}%",
        f"Velocidade média: {row['avg_speed_kmh']:.2f} km/h",
        f"RPM máximo: {int(row['max_rpm'])}",
        f"Temperatura média: {row['avg_engine_temp_c']:.2f} °C",
        f"Temperatura máxima: {int(row['max_engine_temp_c'])} °C",
    ]

    for i, metric in enumerate(metrics):
        axes[1].text(
            0.05,
            0.88 - i * 0.15,
            metric,
            fontsize=11,
            transform=axes[1].transAxes,
        )

    save_figure("04_telemetry_alerts.png")


def plot_confusion_matrix(filename, title, output_filename):
    path = DATA_DIR / filename

    if not path.exists():
        print(f"Matriz não encontrada, gráfico ignorado: {path}")
        return

    matrix = pd.read_csv(path, index_col=0)

    plt.figure(figsize=(7, 5))
    plt.imshow(matrix.values)

    plt.xticks(
        range(len(matrix.columns)),
        matrix.columns,
        rotation=25,
        ha="right",
    )
    plt.yticks(range(len(matrix.index)), matrix.index)

    plt.title(title)
    plt.xlabel("Classificação prevista")
    plt.ylabel("Classificação de referência")
    plt.colorbar(label="Quantidade")

    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            plt.text(
                col,
                row,
                str(matrix.iloc[row, col]),
                ha="center",
                va="center",
            )

    save_figure(output_filename)


def plot_fleet_overview():
    df = load_csv("fleet_efficiency_ranking.csv")
    diagnosis = load_csv("efficiency_diagnosis.csv")

    total_vehicles = df["vehicle_id"].nunique()
    total_cost = df["total_cost_brl"].sum()
    total_distance = df["total_distance_km"].sum()

    # Média ponderada: distância total / litros totais.
    total_liters = df["total_fuel_liters"].sum()
    average_km_l = (
        total_distance / total_liters if total_liters > 0 else 0
    )

    class_counts = (
        diagnosis["efficiency_class"]
        .value_counts()
        .reindex(
            ["EFICIENTE", "ATENÇÃO", "INEFICIENTE"],
            fill_value=0
        )
    )

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Indicadores gerais
    labels = [
        f"Veículos: {total_vehicles}",
        f"Custo total: R$ {total_cost:,.2f}",
        f"Distância: {total_distance:,.0f} km",
        f"Consumo médio: {average_km_l:.2f} km/L",
    ]

    axes[0].axis("off")
    axes[0].set_title("Indicadores gerais da frota")

    for i, label in enumerate(labels):
        axes[0].text(
            0.05,
            0.85 - i * 0.22,
            label,
            fontsize=13,
            transform=axes[0].transAxes,
        )

    # Distribuição das classes
    axes[1].bar(class_counts.index, class_counts.values)
    axes[1].set_title("Diagnóstico por regras")
    axes[1].set_ylabel("Quantidade de veículos")
    axes[1].tick_params(axis="x", rotation=20)
    axes[1].grid(axis="y", alpha=0.3)

    for i, value in enumerate(class_counts.values):
        axes[1].text(i, value, str(value), ha="center", va="bottom")

    save_figure("07_fleet_overview.png")


def main():
    print("\nIniciando consolidação visual da Sprint 2...\n")

    plot_cost_per_km()
    plot_fuel_efficiency()
    plot_diagnosis_distribution()
    plot_telemetry_alerts()

    plot_confusion_matrix(
        "ml_confusion_matrix.csv",
        "Matriz de confusão - Machine Learning",
        "05_ml_confusion_matrix.png",
    )

    plot_confusion_matrix(
        "ml_rules_confusion_matrix.csv",
        "Comparação entre regras e Machine Learning",
        "06_rules_vs_ml.png",
    )

    plot_fleet_overview()

    print("\nConsolidação visual concluída!")
    print(f"Imagens salvas em: {FIGURES_DIR}")


if __name__ == "__main__":
    main()

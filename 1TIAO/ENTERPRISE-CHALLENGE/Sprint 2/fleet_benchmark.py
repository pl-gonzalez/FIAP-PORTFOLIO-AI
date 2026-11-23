
from pathlib import Path

import pandas as pd


# =====================================================
# CONFIGURAÇÕES
# =====================================================

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "data" / "processed" / "fleet_integrated.csv"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

# =====================================================
# LEITURA E VALIDAÇÃO
# =====================================================

def load_data():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "vehicle_id",
        "vehicle_type",
        "date_reference",
        "category",
        "amount_brl",
        "quantity_liters",
        "distance_km",
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Colunas obrigatórias ausentes: {missing}"
        )

    if df.empty:
        raise ValueError("O arquivo de integração está vazio.")

    return df


# =====================================================
# INDICADORES POR VEÍCULO
# =====================================================

def calculate_vehicle_metrics(df):

    df = df.copy()

    numeric_columns = [
        "amount_brl",
        "quantity_liters",
        "distance_km",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["date_reference"] = pd.to_datetime(
        df["date_reference"],
        errors="coerce"
    )

    # Total de despesas por veículo
    expenses = (
        df.groupby("vehicle_id")
        .agg(
            vehicle_type=("vehicle_type", "first"),
            total_cost_brl=("amount_brl", "sum"),
        )
        .reset_index()
    )

    # Distância: consolida uma única medida por veículo/período.
    # Não soma os valores repetidos em diferentes despesas.
    monthly_distance = (
        df.dropna(subset=["date_reference"])
        .groupby(["vehicle_id", "date_reference"])
        ["distance_km"]
        .max()
        .reset_index()
    )

    distance = (
        monthly_distance.groupby("vehicle_id")
        ["distance_km"]
        .sum()
        .reset_index(name="total_distance_km")
    )

    # Combustível: considera somente registros da categoria.
    fuel = df[
        df["category"].astype(str).str.strip().str.casefold()
        == "combustível".casefold()
    ]

    fuel_metrics = (
        fuel.groupby("vehicle_id")
        .agg(
            total_fuel_liters=("quantity_liters", "sum")
        )
        .reset_index()
    )

    # Consolidação dos indicadores
    metrics = (
        expenses
        .merge(distance, on="vehicle_id", how="left")
        .merge(fuel_metrics, on="vehicle_id", how="left")
    )

    metrics["total_fuel_liters"] = (
        metrics["total_fuel_liters"].fillna(0)
    )

    metrics["cost_per_km"] = (
        metrics["total_cost_brl"]
        / metrics["total_distance_km"].where(
            metrics["total_distance_km"] > 0
        )
    )

    metrics["km_per_liter"] = (
        metrics["total_distance_km"]
        / metrics["total_fuel_liters"].where(
            metrics["total_fuel_liters"] > 0
        )
    )

    return metrics


# =====================================================
# DESPESAS POR CATEGORIA
# =====================================================

def calculate_category_share(df):

    category = (
        df.groupby(["vehicle_id", "category"])
        ["amount_brl"]
        .sum()
        .reset_index()
    )

    category["vehicle_total_brl"] = (
        category.groupby("vehicle_id")["amount_brl"]
        .transform("sum")
    )

    category["share_pct"] = (
        category["amount_brl"]
        / category["vehicle_total_brl"].where(
            category["vehicle_total_brl"] > 0
        )
    ) * 100

    return category


# =====================================================
# BENCHMARK POR TIPO DE VEÍCULO
# =====================================================

def calculate_benchmark(metrics):

    valid = metrics.dropna(
        subset=["cost_per_km", "km_per_liter"]
    ).copy()

    benchmark = (
        valid.groupby("vehicle_type")
        .agg(
            vehicles=("vehicle_id", "count"),

            cost_km_mean=("cost_per_km", "mean"),
            cost_km_median=("cost_per_km", "median"),
            cost_km_q1=("cost_per_km",
                        lambda x: x.quantile(0.25)),
            cost_km_q3=("cost_per_km",
                        lambda x: x.quantile(0.75)),

            km_l_mean=("km_per_liter", "mean"),
            km_l_median=("km_per_liter", "median"),
            km_l_q1=("km_per_liter",
                     lambda x: x.quantile(0.25)),
            km_l_q3=("km_per_liter",
                     lambda x: x.quantile(0.75)),
        )
        .reset_index()
    )

    return benchmark


# =====================================================
# RANKING E COMPARAÇÃO
# =====================================================

def calculate_ranking(metrics, benchmark):

    ranking = metrics.merge(
        benchmark[
            ["vehicle_type", "cost_km_mean", "km_l_mean"]
        ],
        on="vehicle_type",
        how="left"
    )

    ranking["cost_km_gap_pct"] = (
        (ranking["cost_per_km"] - ranking["cost_km_mean"])
        / ranking["cost_km_mean"].where(
            ranking["cost_km_mean"] > 0
        )
    ) * 100

    ranking["km_l_gap_pct"] = (
        (ranking["km_per_liter"] - ranking["km_l_mean"])
        / ranking["km_l_mean"].where(
            ranking["km_l_mean"] > 0
        )
    ) * 100

    ranking["cost_status"] = ranking[
        "cost_km_gap_pct"
    ].apply(
        lambda x: (
            "ACIMA DA MÉDIA"
            if pd.notna(x) and x > 0
            else "NA MÉDIA OU ABAIXO"
            if pd.notna(x)
            else "SEM DADOS"
        )
    )

    ranking["fuel_status"] = ranking[
        "km_l_gap_pct"
    ].apply(
        lambda x: (
            "ACIMA DA MÉDIA"
            if pd.notna(x) and x > 0
            else "NA MÉDIA OU ABAIXO"
            if pd.notna(x)
            else "SEM DADOS"
        )
    )

    return ranking.sort_values(
        "cost_per_km",
        ascending=False
    )


# =====================================================
# EXECUÇÃO
# =====================================================

def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_data()

    metrics = calculate_vehicle_metrics(df)

    category_share = calculate_category_share(df)

    benchmark = calculate_benchmark(metrics)

    ranking = calculate_ranking(metrics, benchmark)

    metrics.to_csv(
        OUTPUT_DIR / "fleet_vehicle_metrics.csv",
        index=False,
        encoding="utf-8-sig"
    )

    category_share.to_csv(
        OUTPUT_DIR / "fleet_category_share.csv",
        index=False,
        encoding="utf-8-sig"
    )

    benchmark.to_csv(
        OUTPUT_DIR / "fleet_benchmark_by_type.csv",
        index=False,
        encoding="utf-8-sig"
    )

    ranking.to_csv(
        OUTPUT_DIR / "fleet_efficiency_ranking.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("\nBenchmark da frota concluído!")

    print(f"Veículos analisados: {len(metrics)}")

    print("\nIndicadores por veículo:")
    print(
        metrics[
            [
                "vehicle_id",
                "total_cost_brl",
                "total_distance_km",
                "total_fuel_liters",
                "cost_per_km",
                "km_per_liter",
            ]
        ].round(2).to_string(index=False)
    )

    print("\nBenchmark por tipo:")
    print(benchmark.round(2).to_string(index=False))

    print("\nArquivos gerados em:")
    print(OUTPUT_DIR)


if __name__ == "__main__":
    main()

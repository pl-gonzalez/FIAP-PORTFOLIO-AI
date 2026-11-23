
from pathlib import Path

import pandas as pd


# =====================================================
# CONFIGURAÇÕES
# =====================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"

BENCHMARK_FILE = DATA_DIR / "fleet_efficiency_ranking.csv"
TELEMETRY_FILE = DATA_DIR / "telemetry_diagnosis.csv"

OUTPUT_FILE = DATA_DIR / "efficiency_diagnosis.csv"


# =====================================================
# LEITURA DOS DADOS
# =====================================================

def load_data():

    for file in [BENCHMARK_FILE, TELEMETRY_FILE]:
        if not file.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {file}"
            )

    benchmark = pd.read_csv(BENCHMARK_FILE)
    telemetry = pd.read_csv(TELEMETRY_FILE)

    if benchmark.empty:
        raise ValueError("Benchmark está vazio.")

    if telemetry.empty:
        raise ValueError("Diagnóstico de telemetria está vazio.")

    required_benchmark = [
        "vehicle_id",
        "cost_per_km",
        "cost_km_mean",
        "km_per_liter",
        "km_l_mean",
    ]

    required_telemetry = [
        "vehicle_id",
        "diagnostic_class",
        "diagnostic_reasons",
    ]

    for col in required_benchmark:
        if col not in benchmark.columns:
            raise ValueError(
                f"Coluna ausente no benchmark: {col}"
            )

    for col in required_telemetry:
        if col not in telemetry.columns:
            raise ValueError(
                f"Coluna ausente na telemetria: {col}"
            )

    return benchmark, telemetry


# =====================================================
# INTEGRAÇÃO DOS DIAGNÓSTICOS
# =====================================================

def integrate_diagnostics(benchmark, telemetry):

    # A telemetria pode conter mais de uma simulação
    # por veículo. Neste projeto, selecionamos a pior
    # classificação encontrada para cada veículo.

    priority = {
        "EFICIENTE": 0,
        "ATENÇÃO": 1,
        "INEFICIENTE": 2,
    }

    telemetry = telemetry.copy()

    telemetry["priority"] = (
        telemetry["diagnostic_class"]
        .map(priority)
        .fillna(-1)
    )

    telemetry = (
        telemetry.sort_values("priority", ascending=False)
        .drop_duplicates(subset="vehicle_id")
    )

    telemetry = telemetry[
        [
            "vehicle_id",
            "diagnostic_class",
            "diagnostic_reasons",
        ]
    ]

    result = benchmark.merge(
        telemetry,
        on="vehicle_id",
        how="left",
        validate="one_to_one"
    )

    return result


# =====================================================
# CLASSIFICAÇÃO ECONÔMICA E OPERACIONAL
# =====================================================

def classify_efficiency(row):

    score = 0
    reasons = []

    # Regra 1: custo por quilômetro
    if (
        pd.notna(row["cost_per_km"])
        and pd.notna(row["cost_km_mean"])
        and row["cost_per_km"] > row["cost_km_mean"]
    ):
        score += 1
        reasons.append("Custo por km acima da média do grupo")

    # Regra 2: consumo de combustível
    if (
        pd.notna(row["km_per_liter"])
        and pd.notna(row["km_l_mean"])
        and row["km_per_liter"] < row["km_l_mean"]
    ):
        score += 1
        reasons.append("Consumo km/L abaixo da média do grupo")

    # Regra 3: diagnóstico operacional
    operational_class = row["diagnostic_class"]

    if operational_class in ["ATENÇÃO", "INEFICIENTE"]:
        score += 1
        reasons.append(
            f"Alerta operacional: {operational_class}"
        )

    if score == 0:
        classification = "EFICIENTE"

    elif score == 1:
        classification = "ATENÇÃO"

    else:
        classification = "INEFICIENTE"

    return pd.Series({
        "efficiency_score": score,
        "efficiency_class": classification,
        "efficiency_reasons": (
            "; ".join(reasons)
            if reasons
            else "Nenhum critério de atenção identificado"
        )
    })


# =====================================================
# EXECUÇÃO
# =====================================================

def main():

    benchmark, telemetry = load_data()

    result = integrate_diagnostics(
        benchmark,
        telemetry
    )

    diagnosis = result.apply(
        classify_efficiency,
        axis=1
    )

    result = pd.concat(
        [result, diagnosis],
        axis=1
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\nDiagnóstico integrado concluído!")

    print(f"Veículos analisados: {len(result)}")

    print("\nClassificação final:")

    print(
        result[
            [
                "vehicle_id",
                "efficiency_score",
                "efficiency_class",
            ]
        ].to_string(index=False)
    )

    print("\nMotivos identificados:")

    print(
        result[
            [
                "vehicle_id",
                "efficiency_reasons",
            ]
        ].to_string(index=False)
    )

    print(f"\nArquivo gerado: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

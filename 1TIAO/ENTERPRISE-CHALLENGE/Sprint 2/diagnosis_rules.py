
from pathlib import Path

import pandas as pd


# =====================================================
# CONFIGURAÇÕES
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "data" / "processed" / "telemetry_metrics.csv"
OUTPUT_DIR = BASE_DIR / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "telemetry_diagnosis.csv"

THRESHOLDS = {
    "alert_rate_pct": 20,
    "max_engine_temp_c": 105,
    "max_rpm": 5000,
    "max_speed_kmh": 120,
}


# =====================================================
# DIAGNÓSTICO POR REGRAS
# =====================================================

def classify_vehicle(row):
    score = 0
    reasons = []

    if row["alert_rate_pct"] > THRESHOLDS["alert_rate_pct"]:
        score += 1
        reasons.append("Taxa elevada de alertas")

    if row["max_engine_temp_c"] > THRESHOLDS["max_engine_temp_c"]:
        score += 1
        reasons.append("Temperatura máxima elevada")

    if row["max_rpm"] > THRESHOLDS["max_rpm"]:
        score += 1
        reasons.append("RPM máximo elevado")

    if row["max_speed_kmh"] > THRESHOLDS["max_speed_kmh"]:
        score += 1
        reasons.append("Velocidade máxima acima do limite definido")

    if score == 0:
        classification = "EFICIENTE"
        explanation = "Nenhum dos critérios de atenção foi identificado."

    elif score <= 2:
        classification = "ATENÇÃO"
        explanation = "; ".join(reasons)

    else:
        classification = "INEFICIENTE"
        explanation = "; ".join(reasons)

    return pd.Series({
        "diagnostic_score": score,
        "diagnostic_class": classification,
        "diagnostic_reasons": explanation
    })


# =====================================================
# EXECUÇÃO
# =====================================================

def main():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {INPUT_FILE}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "vehicle_id",
        "simulation_id",
        "alert_rate_pct",
        "max_engine_temp_c",
        "max_rpm",
        "max_speed_kmh",
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Colunas obrigatórias ausentes: {missing_columns}"
        )

    if df.empty:
        raise ValueError("O arquivo de métricas está vazio.")

    result = df.copy()

    diagnosis = result.apply(classify_vehicle, axis=1)

    result = pd.concat([result, diagnosis], axis=1)

    result.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\nDiagnóstico concluído!")
    print(f"Registros analisados: {len(result)}")

    print("\nClassificação:")
    print(
        result[
            ["vehicle_id", "diagnostic_score", "diagnostic_class"]
        ].to_string(index=False)
    )

    print("\nMotivos identificados:")
    print(
        result[
            ["vehicle_id", "diagnostic_reasons"]
        ].to_string(index=False)
    )

    print(f"\nArquivo gerado: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

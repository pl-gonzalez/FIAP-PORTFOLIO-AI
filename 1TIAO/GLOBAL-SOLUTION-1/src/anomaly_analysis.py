
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent

RESULT_FILE = (
    ROOT_DIR
    / "data"
    / "processed"
    / "anomaly_detection_results.csv"
)

df = pd.read_csv(RESULT_FILE)

# Anomalias que o modelo não encontrou
missed = df[
    (df["is_injected_anomaly"] == True)
    & (df["predicted_anomaly"] == 0)
]

# Registros normais classificados incorretamente
false_positives = df[
    (df["is_injected_anomaly"] == False)
    & (df["predicted_anomaly"] == 1)
]

print("\n--- ANOMALIAS NÃO DETECTADAS ---")

print(
    missed[
        [
            "timestamp",
            "power_w",
            "hour",
            "anomaly_type",
            "anomaly_score",
        ]
    ].to_string(index=False)
)

print("\n--- FALSOS POSITIVOS ---")

print(
    false_positives[
        [
            "timestamp",
            "power_w",
            "hour",
            "anomaly_score",
        ]
    ].to_string(index=False)
)

print("\n--- DESEMPENHO POR TIPO DE ANOMALIA ---")

print(
    df[df["is_injected_anomaly"] == True]
    .groupby("anomaly_type")["predicted_anomaly"]
    .agg(["count", "sum"])
)


from pathlib import Path
import pandas as pd

# Diretório onde este script está localizado
BASE_DIR = Path(__file__).resolve().parent

# Arquivos de entrada e saída
INPUT_FILE = BASE_DIR / "data" / "processed" / "telemetry_validated.csv"
OUTPUT_DIR = BASE_DIR / "data" / "processed"


def main():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {INPUT_FILE}\n"
            "Execute primeiro: python process_telemetry.py"
        )

    df = pd.read_csv(INPUT_FILE)

    # Considerar somente registros validados
    df = df[df["validation_status"] == "OK"].copy()

    if df.empty:
        raise ValueError(
            "Não existem registros válidos para análise."
        )

    # Identificar leituras com alertas
    df["has_alert"] = (
        df["alerts"].fillna("NONE").str.strip() != "NONE"
    )

    # Agrupar por veículo e simulação
    metrics = (
        df.groupby(["vehicle_id", "simulation_id"])
        .agg(
            total_readings=("timestamp_ms", "count"),
            avg_speed_kmh=("speed_kmh", "mean"),
            max_speed_kmh=("speed_kmh", "max"),
            avg_rpm=("rpm", "mean"),
            max_rpm=("rpm", "max"),
            avg_fuel_pct=("fuel_pct", "mean"),
            avg_engine_temp_c=("engine_temp_c", "mean"),
            max_engine_temp_c=("engine_temp_c", "max"),
            alert_readings=("has_alert", "sum")
        )
        .reset_index()
    )

    metrics["alert_rate_pct"] = (
        metrics["alert_readings"]
        / metrics["total_readings"]
        * 100
    )

    # Contabilizar cada tipo de alerta
    alert_counts = []

    for _, row in df.iterrows():

        if row["alerts"] == "NONE":
            continue

        for alert in str(row["alerts"]).split("|"):
            alert_counts.append({
                "vehicle_id": row["vehicle_id"],
                "simulation_id": row["simulation_id"],
                "alert": alert
            })

    alert_df = pd.DataFrame(
        alert_counts,
        columns=[
            "vehicle_id",
            "simulation_id",
            "alert"
        ]
    )

    if not alert_df.empty:

        alert_summary = (
            alert_df.groupby(
                ["vehicle_id", "simulation_id", "alert"]
            )
            .size()
            .reset_index(name="occurrences")
        )

    else:

        alert_summary = pd.DataFrame(
            columns=[
                "vehicle_id",
                "simulation_id",
                "alert",
                "occurrences"
            ]
        )

    # Criar diretório de saída
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Exportar indicadores
    metrics.to_csv(
        OUTPUT_DIR / "telemetry_metrics.csv",
        index=False
    )

    # Exportar resumo dos alertas
    alert_summary.to_csv(
        OUTPUT_DIR / "telemetry_alert_summary.csv",
        index=False
    )

    print("Análise de telemetria concluída!")
    print(f"Veículos analisados: {metrics['vehicle_id'].nunique()}")
    print(f"Leituras analisadas: {len(df)}")

    print("\nIndicadores:")
    print(metrics.to_string(index=False))

    print("\nResumo dos alertas:")
    print(alert_summary.to_string(index=False))

    print("\nArquivos gerados:")
    print(OUTPUT_DIR / "telemetry_metrics.csv")
    print(OUTPUT_DIR / "telemetry_alert_summary.csv")


if __name__ == "__main__":
    main()

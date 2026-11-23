from pathlib import Path
import json
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "telemetry.csv"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REQUIRED_COLUMNS = [
    "vehicle_id", "simulation_id", "timestamp_ms", "speed_kmh",
    "rpm", "fuel_pct", "engine_temp_c", "alerts"
]
NUMERIC_COLUMNS = [
    "timestamp_ms", "speed_kmh", "rpm", "fuel_pct", "engine_temp_c"
]

def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {INPUT_FILE}. "
            "Coloque telemetry.csv na mesma pasta deste script."
        )

    df = pd.read_csv(INPUT_FILE)

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing}")

    df["vehicle_id"] = df["vehicle_id"].astype("string").str.strip().str.upper()
    df["simulation_id"] = df["simulation_id"].astype("string").str.strip()
    df["alerts"] = df["alerts"].fillna("NONE").astype(str).str.strip()

    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    issues = []

    def add_issue(mask, issue):
        for idx in df.index[mask.fillna(False)]:
            issues.append({
                "row_number": int(idx) + 2,
                "vehicle_id": df.at[idx, "vehicle_id"],
                "simulation_id": df.at[idx, "simulation_id"],
                "issue": issue
            })

    add_issue(df["vehicle_id"].isna() | df["vehicle_id"].eq(""), "MISSING_VEHICLE_ID")
    add_issue(df["simulation_id"].isna() | df["simulation_id"].eq(""), "MISSING_SIMULATION_ID")

    for col in NUMERIC_COLUMNS:
        add_issue(df[col].isna(), f"MISSING_OR_INVALID_{col.upper()}")

    add_issue(df["timestamp_ms"].lt(0), "NEGATIVE_TIMESTAMP")
    add_issue(df["speed_kmh"].lt(0), "NEGATIVE_SPEED")
    add_issue(df["rpm"].lt(0), "NEGATIVE_RPM")
    add_issue(df["fuel_pct"].lt(0) | df["fuel_pct"].gt(100), "FUEL_OUT_OF_RANGE")
    add_issue(df["engine_temp_c"].lt(-40) | df["engine_temp_c"].gt(200), "ENGINE_TEMP_OUT_OF_RANGE")

    duplicate_mask = df.duplicated(
        subset=["vehicle_id", "simulation_id", "timestamp_ms"], keep=False
    )
    add_issue(duplicate_mask, "DUPLICATE_TELEMETRY_TIMESTAMP")

    allowed_alerts = {"NONE", "HIGH_RPM", "HIGH_ENGINE_TEMP", "HIGH_SPEED", "LOW_FUEL"}
    for idx, value in df["alerts"].items():
        found = set() if value == "NONE" else set(value.split("|"))
        unknown = found - allowed_alerts
        if unknown:
            issues.append({
                "row_number": int(idx) + 2,
                "vehicle_id": df.at[idx, "vehicle_id"],
                "simulation_id": df.at[idx, "simulation_id"],
                "issue": "UNKNOWN_ALERT:" + "|".join(sorted(unknown))
            })

    issue_df = pd.DataFrame(issues, columns=[
        "row_number", "vehicle_id", "simulation_id", "issue"
    ])

    issue_rows = set(issue_df["row_number"].tolist()) if not issue_df.empty else set()
    df["validation_status"] = [
        "REVIEW" if (idx + 2) in issue_rows else "OK"
        for idx in range(len(df))
    ]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    integrated_path = OUTPUT_DIR / "telemetry_validated.csv"
    issues_path = OUTPUT_DIR / "telemetry_quality_issues.csv"
    report_path = OUTPUT_DIR / "telemetry_quality_report.json"

    df.to_csv(integrated_path, index=False)
    issue_df.to_csv(issues_path, index=False)

    report = {
        "source_file": INPUT_FILE.name,
        "records_received": int(len(df)),
        "vehicles": sorted(df["vehicle_id"].dropna().unique().tolist()),
        "simulations": sorted(df["simulation_id"].dropna().unique().tolist()),
        "records_ok": int((df["validation_status"] == "OK").sum()),
        "records_review": int((df["validation_status"] == "REVIEW").sum()),
        "issue_count": int(len(issue_df)),
        "alerts_summary": {
            str(alert): int(count)
            for alert, count in df["alerts"].value_counts(dropna=False).items()
        },
        "note": (
            "Telemetria sintética gerada no Wokwi. Não representa medições "
            "reais do veículo. A associação a V007 é um identificador de teste."
        )
    }
    report_path.write_text(json.dumps(report, indent=4, ensure_ascii=False), encoding="utf-8")

    print("Processamento de telemetria concluído!")
    print(f"Registros: {len(df)}")
    print(f"Veículos: {', '.join(report['vehicles'])}")
    print(f"Registros OK: {report['records_ok']}")
    print(f"Registros para revisão: {report['records_review']}")
    print(f"Arquivo integrado: {integrated_path}")
    print(f"Relatório: {report_path}")

if __name__ == "__main__":
    main()

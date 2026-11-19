
from pathlib import Path

import numpy as np
import pandas as pd


# Caminhos do projeto
ROOT_DIR = Path(__file__).resolve().parent.parent

RAW_FILE = ROOT_DIR / "data" / "raw" / "smart_meter_data.csv"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"

OUTPUT_FILE = PROCESSED_DIR / "smart_meter_features.csv"


def load_data():
    """Carrega os dados brutos do medidor."""

    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {RAW_FILE}"
        )

    df = pd.read_csv(RAW_FILE)

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df = df.sort_values("timestamp").reset_index(drop=True)

    return df


def create_time_features(df):
    """Extrai informações temporais."""

    df = df.copy()

    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek

    # Segunda a sexta = 0; sábado e domingo = 1
    df["is_weekend"] = (
        df["day_of_week"] >= 5
    ).astype(int)

    # Representação cíclica da hora
    df["hour_sin"] = np.sin(
        2 * np.pi * df["hour"] / 24
    )

    df["hour_cos"] = np.cos(
        2 * np.pi * df["hour"] / 24
    )

    return df


def create_consumption_features(df):
    """Cria indicadores de comportamento do consumo."""

    df = df.copy()

    # Quatro medições representam uma hora
    df["rolling_mean_1h"] = (
        df["power_w"]
        .rolling(window=4, min_periods=1)
        .mean()
    )

    df["rolling_std_1h"] = (
        df["power_w"]
        .rolling(window=4, min_periods=1)
        .std()
        .fillna(0)
    )

    return df


def validate_data(df):
    """Verifica a integridade dos dados processados."""

    required_columns = [
        "timestamp",
        "power_w",
        "energy_kwh_interval",
        "hour",
        "day_of_week",
        "hour_sin",
        "hour_cos",
        "rolling_mean_1h",
        "rolling_std_1h",
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Colunas ausentes: {missing_columns}"
        )

    if df.isnull().any().any():
        raise ValueError(
            "Existem valores ausentes no conjunto processado."
        )

    if len(df) != 2880:
        raise ValueError(
            f"Quantidade inesperada de registros: {len(df)}"
        )


def main():

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df = load_data()

    df = create_time_features(df)

    df = create_consumption_features(df)

    validate_data(df)

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("Processamento concluído!")
    print(f"Registros processados: {len(df)}")
    print(f"Colunas disponíveis: {len(df.columns)}")
    print(
        f"Consumo total: "
        f"{df['energy_kwh_interval'].sum():.2f} kWh"
    )
    print(f"Arquivo salvo em: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

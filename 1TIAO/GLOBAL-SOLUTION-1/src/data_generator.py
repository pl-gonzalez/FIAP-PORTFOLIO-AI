
import numpy as np
import pandas as pd
from pathlib import Path


# ==========================================
# CONFIGURAÇÕES DO SIMULADOR
# ==========================================

START_DATE = "2026-10-01"
DAYS = 30
INTERVAL_MINUTES = 15

DEVICE_ID = "SM001"

VOLTAGE_NOMINAL = 220

SEED = 42

# Diretório de saída
PROJECT_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"


# ==========================================
# 1. PERFIL DE CONSUMO DO ESTABELECIMENTO
# ==========================================

def get_base_power(hour, weekday):
    """
    Retorna a potência média esperada (W)
    de acordo com o horário e o dia da semana.

    weekday:
    0 = segunda-feira
    6 = domingo
    """

    # Madrugada: equipamentos permanentes
    if 0 <= hour < 6:
        power = 300

    # Preparação para abertura
    elif 6 <= hour < 8:
        power = 650

    # Funcionamento comercial
    elif 8 <= hour < 12:
        power = 1800

    elif 12 <= hour < 14:
        power = 2200

    elif 14 <= hour < 18:
        power = 2000

    # Encerramento
    elif 18 <= hour < 20:
        power = 1200

    # Período noturno
    else:
        power = 350

    # Finais de semana:
    # funcionamento reduzido
    if weekday >= 5:

        if 8 <= hour < 18:
            power *= 0.65
        else:
            power *= 0.85

    return power


# ==========================================
# 2. GERAÇÃO DOS DADOS
# ==========================================

def generate_dataset():

    rng = np.random.default_rng(SEED)

    total_records = (
        DAYS * 24 * 60 // INTERVAL_MINUTES
    )

    timestamps = pd.date_range(
        start=START_DATE,
        periods=total_records,
        freq=f"{INTERVAL_MINUTES}min"
    )

    records = []

    for timestamp in timestamps:

        hour = timestamp.hour
        weekday = timestamp.weekday()

        # Potência esperada para o horário
        base_power = get_base_power(
            hour,
            weekday
        )

        # Variação natural do consumo
        variation = rng.normal(1.0, 0.12)

        power = base_power * variation

        # Evita valores negativos
        power = max(power, 50)

        # Variação da tensão elétrica
        voltage = rng.normal(
            VOLTAGE_NOMINAL,
            2.0
        )

        # Fator de potência
        power_factor = rng.uniform(
            0.90,
            0.99
        )

        # Relação entre potência, tensão e corrente
        current = power / (
            voltage * power_factor
        )

        # Energia consumida em 15 minutos
        energy = (
            power * (INTERVAL_MINUTES / 60)
        ) / 1000

        records.append({

            "timestamp": timestamp,

            "device_id": DEVICE_ID,

            "voltage_v": round(voltage, 2),

            "current_a": round(current, 3),

            "power_w": round(power, 2),

            "power_factor": round(
                power_factor, 3
            ),

            "energy_kwh_interval": round(
                energy, 5
            )

        })

    return pd.DataFrame(records)


# ==========================================
# 3. INSERÇÃO DE ANOMALIAS CONTROLADAS
# ==========================================

def create_validation_dataset(df):

    rng = np.random.default_rng(SEED + 1)

    validation = df.copy()

    validation["is_injected_anomaly"] = False

    validation["anomaly_type"] = "normal"

    # Identificação dos horários
    hours = pd.to_datetime(
        validation["timestamp"]
    ).dt.hour

    # Anomalias 1: picos inesperados
    spike_indices = rng.choice(
        validation.index.to_numpy(),
        size=10,
        replace=False
    )

    for index in spike_indices:

        multiplier = rng.uniform(2.5, 3.5)

        validation.loc[index, "power_w"] *= multiplier

        validation.loc[index, "is_injected_anomaly"] = True

        validation.loc[index, "anomaly_type"] = "power_spike"

    # Anomalias 2: consumo elevado na madrugada
    night_candidates = validation.index[
        (hours >= 1) & (hours < 5)
    ].to_numpy()

    night_indices = rng.choice(
        night_candidates,
        size=10,
        replace=False
    )

    for index in night_indices:

        multiplier = rng.uniform(3.0, 4.0)

        validation.loc[index, "power_w"] *= multiplier

        validation.loc[index, "is_injected_anomaly"] = True

        validation.loc[index, "anomaly_type"] = "night_consumption"

    # Atualização das variáveis elétricas
    validation["current_a"] = (
        validation["power_w"] /
        (
            validation["voltage_v"] *
            validation["power_factor"]
        )
    ).round(3)

    # Recalcula o consumo energético
    validation["energy_kwh_interval"] = (
        validation["power_w"] *
        (INTERVAL_MINUTES / 60) / 1000
    ).round(5)

    validation["power_w"] = validation[
        "power_w"
    ].round(2)

    return validation


# ==========================================
# 4. VALIDAÇÃO DOS DADOS
# ==========================================

def validate_dataset(df):

    expected_records = (
        DAYS * 24 * 60 // INTERVAL_MINUTES
    )

    assert len(df) == expected_records, (
        "Quantidade incorreta de registros!"
    )

    assert not df.isnull().any().any(), (
        "Existem valores ausentes!"
    )

    assert (df["power_w"] > 0).all(), (
        "Existem valores de potência inválidos!"
    )

    assert (df["energy_kwh_interval"] >= 0).all(), (
        "Existem valores de energia inválidos!"
    )

    print("\nValidação concluída com sucesso!")


# ==========================================
# 5. EXECUÇÃO PRINCIPAL
# ==========================================

def main():

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("Gerando dados do Smart Meter...")

    df = generate_dataset()

    validate_dataset(df)

    raw_path = RAW_DIR / "smart_meter_data.csv"

    df.to_csv(
        raw_path,
        index=False
    )

    print("\nCriando base de validação...")

    validation = create_validation_dataset(df)

    validation_path = (
        PROCESSED_DIR /
        "smart_meter_validation.csv"
    )

    validation.to_csv(
        validation_path,
        index=False
    )

    # Resumo dos resultados
    print("\n========== RESUMO ==========")

    print(f"Total de registros: {len(df)}")

    print(
        f"Consumo total: "
        f"{df['energy_kwh_interval'].sum():.2f} kWh"
    )

    print(
        f"Potência média: "
        f"{df['power_w'].mean():.2f} W"
    )

    print(
        f"Anomalias inseridas: "
        f"{validation['is_injected_anomaly'].sum()}"
    )

    print("\nArquivos gerados:")

    print(raw_path)

    print(validation_path)


if __name__ == "__main__":
    main()

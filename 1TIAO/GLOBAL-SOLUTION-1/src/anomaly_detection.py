
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# --------------------------------------------------
# 1. CAMINHOS
# --------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent

TRAIN_FILE = ROOT_DIR / "data" / "raw" / "smart_meter_data.csv"

VALIDATION_FILE = (
    ROOT_DIR / "data" / "processed" / "smart_meter_validation.csv"
)

OUTPUT_DIR = ROOT_DIR / "data" / "processed"

RESULT_FILE = OUTPUT_DIR / "anomaly_detection_results.csv"


# --------------------------------------------------
# 2. VARIÁVEIS UTILIZADAS PELO MODELO
# --------------------------------------------------

FEATURE_COLUMNS = [
    "power_w",
    "current_a",
    "power_factor",
    "hour_sin",
    "hour_cos",
    "is_weekend",
    "rolling_mean_1h",
    "rolling_std_1h",
    "power_deviation_ratio",
]


# --------------------------------------------------
# 3. ENGENHARIA DE ATRIBUTOS
# --------------------------------------------------

def prepare_features(df):
    """Prepara as variáveis utilizadas pelo modelo."""

    df = df.copy()

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df = df.sort_values("timestamp").reset_index(drop=True)

    # Informações temporais
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek

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

    # Comportamento do consumo na última hora
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


def calculate_expected_power(train_df, target_df):
    """
    Calcula a potência esperada por hora e tipo de dia.

    O padrão é aprendido exclusivamente com os dados
    de treinamento.
    """

    train_df = train_df.copy()
    target_df = target_df.copy()

    train_df["hour"] = train_df["timestamp"].dt.hour
    target_df["hour"] = target_df["timestamp"].dt.hour

    train_df["day_of_week"] = (
        train_df["timestamp"].dt.dayofweek
    )

    target_df["day_of_week"] = (
        target_df["timestamp"].dt.dayofweek
    )

    train_df["is_weekend"] = (
        train_df["day_of_week"] >= 5
    ).astype(int)

    target_df["is_weekend"] = (
        target_df["day_of_week"] >= 5
    ).astype(int)

    # Perfil médio de potência por hora e tipo de dia
    expected_profile = (
        train_df
        .groupby(["hour", "is_weekend"])["power_w"]
        .mean()
    )

    keys = pd.MultiIndex.from_frame(
        target_df[["hour", "is_weekend"]]
    )

    target_df["expected_power_w"] = (
        expected_profile.reindex(keys).to_numpy()
    )

    target_df["power_deviation_ratio"] = (
        target_df["power_w"]
        / target_df["expected_power_w"].clip(lower=1)
    )

    return target_df



# --------------------------------------------------
# 4. CARREGAMENTO DOS DADOS
# --------------------------------------------------

def load_datasets():

    if not TRAIN_FILE.exists():
        raise FileNotFoundError(TRAIN_FILE)

    if not VALIDATION_FILE.exists():
        raise FileNotFoundError(VALIDATION_FILE)

    train_df = pd.read_csv(TRAIN_FILE)

    validation_df = pd.read_csv(VALIDATION_FILE)

    # Converter os rótulos de validação para 0 e 1
    validation_df["is_injected_anomaly"] = (
        validation_df["is_injected_anomaly"]
        .astype(str)
        .str.lower()
        .map({
            "true": 1,
            "false": 0,
            "1": 1,
            "0": 0,
        })
    )

    if validation_df["is_injected_anomaly"].isna().any():
        raise ValueError("Existem rótulos de anomalia inválidos.")

    train_df = prepare_features(train_df)

    validation_df = prepare_features(validation_df)

    return train_df, validation_df


# --------------------------------------------------
# 5. TREINAMENTO DO MODELO
# --------------------------------------------------

def train_model(train_df):

    X_train = train_df[FEATURE_COLUMNS]

    # Estimativa da proporção de anomalias no conjunto
    # de validação: 20 anomalias em 2.880 registros.
    contamination = 20 / 2880

    model = Pipeline([
        ("scaler", StandardScaler()),

        ("isolation_forest", IsolationForest(
            n_estimators=200,
            contamination=contamination,
            random_state=42,
        )),
    ])

    model.fit(X_train)

    return model


# --------------------------------------------------
# 6. AVALIAÇÃO
# --------------------------------------------------

def evaluate_model(model, validation_df):

    X_validation = validation_df[FEATURE_COLUMNS]

    y_true = validation_df["is_injected_anomaly"].astype(int)

    # Isolation Forest:
    # -1 = anomalia
    #  1 = comportamento normal

    predictions = model.predict(X_validation)

    # Converter para:
    # 1 = anomalia
    # 0 = normal

    y_pred = np.where(predictions == -1, 1, 0)

    # Pontuação: valores maiores indicam maior suspeita
    anomaly_scores = -model.decision_function(X_validation)

    results = validation_df.copy()

    results["predicted_anomaly"] = y_pred

    results["anomaly_score"] = anomaly_scores

    # Métricas de avaliação
    precision = precision_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    recall = recall_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    f1 = f1_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1],
    )

    return results, precision, recall, f1, matrix


# --------------------------------------------------
# 7. EXECUÇÃO PRINCIPAL
# --------------------------------------------------

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    train_df, validation_df = load_datasets()

    validation_df = calculate_expected_power(
    train_df,
    validation_df
)

    train_df = calculate_expected_power(
       train_df,
       train_df
)

    print("Dados carregados!")
    print(f"Registros de treinamento: {len(train_df)}")
    print(f"Registros de validação: {len(validation_df)}")

    actual_anomalies = int(
        validation_df["is_injected_anomaly"].sum()
    )

    print(f"Anomalias identificadas no conjunto: {actual_anomalies}")

    print("\nTreinando Isolation Forest...")

    model = train_model(train_df)

    print("Treinamento concluído!")

    results, precision, recall, f1, matrix = evaluate_model(
        model,
        validation_df,
    )

    results.to_csv(
        RESULT_FILE,
        index=False,
    )

    print("\n--- RESULTADOS DA AVALIAÇÃO ---")

    print(f"Precisão (Precision): {precision:.4f}")
    print(f"Revocação (Recall): {recall:.4f}")
    print(f"F1-score: {f1:.4f}")

    print("\nMatriz de confusão:")
    print(matrix)

    print("\nPrevisões do modelo:")
    print(f"Anomalias detectadas: {results['predicted_anomaly'].sum()}")

    print(f"\nResultados salvos em: {RESULT_FILE}")


if __name__ == "__main__":
    main()

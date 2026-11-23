
from pathlib import Path
import json

import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
)


# =====================================================
# CONFIGURAÇÕES
# =====================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"

INPUT_FILE = DATA_DIR / "efficiency_diagnosis.csv"

PREDICTIONS_FILE = DATA_DIR / "ml_test_predictions.csv"
METRICS_FILE = DATA_DIR / "ml_metrics.json"
CONFUSION_FILE = DATA_DIR / "ml_confusion_matrix.csv"
IMPORTANCE_FILE = DATA_DIR / "ml_feature_importance.csv"

RANDOM_STATE = 42

CLASSES = [
    "EFICIENTE",
    "ATENÇÃO",
    "INEFICIENTE",
]


# =====================================================
# CARREGAMENTO E PREPARAÇÃO
# =====================================================

def load_data():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "vehicle_id",
        "cost_per_km",
        "cost_km_mean",
        "km_per_liter",
        "km_l_mean",
        "diagnostic_class",
        "efficiency_class",
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Colunas ausentes: {missing}"
        )

    if df.empty:
        raise ValueError("Dataset vazio.")

    return df


def prepare_features(df):

    data = df.copy()

    # Garante que os indicadores sejam numéricos
    numeric_columns = [
        "cost_per_km",
        "cost_km_mean",
        "km_per_liter",
        "km_l_mean",
    ]

    for col in numeric_columns:
        data[col] = pd.to_numeric(
            data[col],
            errors="coerce"
        )

    # Calcula os desvios percentuais
    data["cost_km_gap_pct"] = (
        (
            data["cost_per_km"]
            - data["cost_km_mean"]
        )
        / data["cost_km_mean"].where(
            data["cost_km_mean"] > 0
        )
    ) * 100

    data["km_l_gap_pct"] = (
        (
            data["km_per_liter"]
            - data["km_l_mean"]
        )
        / data["km_l_mean"].where(
            data["km_l_mean"] > 0
        )
    ) * 100

    # Codificação do diagnóstico operacional.
    # -1 = sem telemetria disponível
    #  0 = eficiente
    #  1 = atenção
    #  2 = ineficiente

    telemetry_mapping = {
        "EFICIENTE": 0,
        "ATENÇÃO": 1,
        "INEFICIENTE": 2,
    }

    data["telemetry_diagnostic_level"] = (
        data["diagnostic_class"]
        .map(telemetry_mapping)
        .fillna(-1)
    )

    feature_columns = [
        "cost_km_gap_pct",
        "km_l_gap_pct",
        "telemetry_diagnostic_level",
    ]

    data = data.dropna(
        subset=feature_columns + ["efficiency_class"]
    )

    X = data[feature_columns]
    y = data["efficiency_class"].str.strip().str.upper()

    return data, X, y, feature_columns


# =====================================================
# TREINAMENTO E AVALIAÇÃO
# =====================================================

def train_and_evaluate(data, X, y, feature_columns):

    class_counts = y.value_counts()

    if len(class_counts) != 3:
        raise ValueError(
            "O dataset precisa conter as três classes "
            "para esta avaliação."
        )

    if class_counts.min() < 2:
        raise ValueError(
            "Cada classe precisa ter pelo menos "
            "dois registros para a divisão estratificada."
        )

    # 67% para treinamento e 33% para teste
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.33,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    model = DecisionTreeClassifier(
        max_depth=3,
        min_samples_leaf=1,
        class_weight="balanced",
        random_state=RANDOM_STATE,
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    # Métricas
    accuracy = accuracy_score(
        y_test,
        predictions
    )

    balanced_accuracy = balanced_accuracy_score(
        y_test,
        predictions
    )

    report = classification_report(
        y_test,
        predictions,
        labels=CLASSES,
        output_dict=True,
        zero_division=0,
    )

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=CLASSES,
    )

    # Resultados individuais
    test_results = data.loc[
        X_test.index,
        ["vehicle_id", "efficiency_class"]
    ].copy()

    test_results["predicted_class"] = predictions

    test_results["correct_prediction"] = (
        test_results["efficiency_class"]
        == test_results["predicted_class"]
    )

    test_results.to_csv(
        PREDICTIONS_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    # Matriz de confusão
    matrix_df = pd.DataFrame(
        matrix,
        index=CLASSES,
        columns=CLASSES,
    )

    matrix_df.index.name = "real_class"

    matrix_df.to_csv(
        CONFUSION_FILE,
        encoding="utf-8-sig",
    )

    # Importância das variáveis
    importance = pd.DataFrame({
        "feature": feature_columns,
        "importance": model.feature_importances_,
    }).sort_values(
        "importance",
        ascending=False,
    )

    importance.to_csv(
        IMPORTANCE_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    # Resumo das métricas
    metrics = {
        "model": "DecisionTreeClassifier",
        "random_state": RANDOM_STATE,
        "total_records": len(data),
        "training_records": len(X_train),
        "test_records": len(X_test),
        "accuracy": float(accuracy),
        "balanced_accuracy": float(balanced_accuracy),
        "classification_report": report,
        "class_distribution": {
            str(key): int(value)
            for key, value in class_counts.items()
        },
        "note": (
            "Avaliação exploratória com poucos veículos. "
            "As classes foram originalmente geradas "
            "por regras, portanto o modelo aprende "
            "a reproduzir essas classificações."
        ),
    }

    with open(
        METRICS_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metrics,
            file,
            indent=4,
            ensure_ascii=False,
        )

    return model, test_results, metrics, importance, matrix_df


# =====================================================
# EXECUÇÃO
# =====================================================

def main():

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = load_data()

    data, X, y, feature_columns = prepare_features(df)

    model, predictions, metrics, importance, matrix = (
        train_and_evaluate(
            data,
            X,
            y,
            feature_columns,
        )
    )

    print("\nTreinamento concluído!")

    print("\nDistribuição das classes:")
    print(y.value_counts().to_string())

    print("\nDivisão dos dados:")
    print(f"Treinamento: {metrics['training_records']}")
    print(f"Teste: {metrics['test_records']}")

    print("\nAvaliação do modelo:")
    print(f"Acurácia: {metrics['accuracy']:.2%}")
    print(
        "Acurácia balanceada: "
        f"{metrics['balanced_accuracy']:.2%}"
    )

    print("\nPrevisões no conjunto de teste:")
    print(predictions.to_string(index=False))

    print("\nMatriz de confusão:")
    print(matrix.to_string())

    print("\nImportância das variáveis:")
    print(importance.to_string(index=False))

    print("\nArquivos gerados:")
    print(PREDICTIONS_FILE)
    print(METRICS_FILE)
    print(CONFUSION_FILE)
    print(IMPORTANCE_FILE)


if __name__ == "__main__":
    main()

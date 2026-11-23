
from pathlib import Path
import json
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"

RULES_FILE = DATA_DIR / "efficiency_diagnosis.csv"
ML_FILE = DATA_DIR / "ml_test_predictions.csv"

COMPARISON_FILE = DATA_DIR / "ml_rules_comparison.csv"
REPORT_FILE = DATA_DIR / "ml_rules_comparison.json"
MATRIX_FILE = DATA_DIR / "ml_rules_confusion_matrix.csv"


def main():
    if not RULES_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {RULES_FILE}")

    if not ML_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {ML_FILE}")

    rules = pd.read_csv(RULES_FILE)
    ml = pd.read_csv(ML_FILE)

    required_rules = ["vehicle_id", "efficiency_class"]
    required_ml = ["vehicle_id", "predicted_class"]

    for col in required_rules:
        if col not in rules.columns:
            raise ValueError(f"Coluna ausente no diagnóstico por regras: {col}")

    for col in required_ml:
        if col not in ml.columns:
            raise ValueError(f"Coluna ausente nas previsões do ML: {col}")

    # Mantém somente os veículos presentes no conjunto de teste.
    comparison = ml[["vehicle_id", "predicted_class"]].merge(
        rules[["vehicle_id", "efficiency_class"]],
        on="vehicle_id",
        how="left",
        validate="one_to_one",
    )

    if comparison["efficiency_class"].isna().any():
        raise ValueError("Existem veículos do teste sem diagnóstico por regras.")

    comparison = comparison.rename(
        columns={
            "efficiency_class": "rule_class",
            "predicted_class": "ml_class",
        }
    )

    comparison["agreement"] = (
        comparison["rule_class"].str.strip().str.upper()
        == comparison["ml_class"].str.strip().str.upper()
    )

    comparison["comparison_result"] = comparison["agreement"].map(
        {True: "CONCORDANTE", False: "DIVERGENTE"}
    )

    total = len(comparison)
    agreements = int(comparison["agreement"].sum())
    divergences = total - agreements
    agreement_rate = agreements / total if total else 0

    # Matriz: linhas = diagnóstico por regras; colunas = previsão do ML.
    classes = ["EFICIENTE", "ATENÇÃO", "INEFICIENTE"]

    matrix = pd.crosstab(
        comparison["rule_class"],
        comparison["ml_class"],
    ).reindex(index=classes, columns=classes, fill_value=0)

    comparison.to_csv(
        COMPARISON_FILE, index=False, encoding="utf-8-sig"
    )
    matrix.to_csv(MATRIX_FILE, encoding="utf-8-sig")

    report = {
        "total_test_vehicles": total,
        "agreements": agreements,
        "divergences": divergences,
        "agreement_rate_pct": round(agreement_rate * 100, 2),
        "interpretation": (
            "A comparação mede a concordância do modelo com as regras "
            "de diagnóstico. Não representa uma validação independente "
            "da eficiência real dos veículos."
        ),
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    print("\nComparação entre regras e Machine Learning concluída!")

    print("\nResultados por veículo:")
    print(comparison.to_string(index=False))

    print("\nResumo:")
    print(f"Veículos avaliados: {total}")
    print(f"Concordâncias: {agreements}")
    print(f"Divergências: {divergences}")
    print(f"Taxa de concordância: {agreement_rate:.2%}")

    print("\nMatriz de comparação:")
    print(matrix.to_string())

    print("\nArquivos gerados:")
    print(COMPARISON_FILE)
    print(REPORT_FILE)
    print(MATRIX_FILE)


if __name__ == "__main__":
    main()

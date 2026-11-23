from pathlib import Path
import json
import re
import unicodedata

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
EXPENSES_FILE = BASE_DIR / "fleet_intelligence_dataset.csv"
REGISTRY_FILE = BASE_DIR / "fleet_registry.csv"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REQUIRED_EXPENSE_COLUMNS = {
    "transaction_id", "date_reference", "vehicle_id", "vehicle_type",
    "category", "amount_brl"
}
REQUIRED_REGISTRY_COLUMNS = {
    "vehicle_id", "vehicle_type", "operation_profile", "benchmark_group"
}


def normalize_text(value):
    """Normalize text for comparisons without changing the displayed source value."""
    if pd.isna(value):
        return ""
    value = str(value).strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", value)


def normalize_id(series):
    return series.astype("string").str.strip().str.upper()


def load_csv(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {path.name}. "
            "Coloque os CSVs na mesma pasta deste script."
        )
    return pd.read_csv(path)


def main():
    expenses = load_csv(EXPENSES_FILE)
    registry = load_csv(REGISTRY_FILE)

    missing_expense = REQUIRED_EXPENSE_COLUMNS - set(expenses.columns)
    missing_registry = REQUIRED_REGISTRY_COLUMNS - set(registry.columns)

    if missing_expense:
        raise ValueError(f"Colunas ausentes no dataset de despesas: {sorted(missing_expense)}")
    if missing_registry:
        raise ValueError(f"Colunas ausentes no cadastro da frota: {sorted(missing_registry)}")

    # Preserve original values for audit and normalize key fields for processing.
    expenses = expenses.copy()
    registry = registry.copy()

    expenses["vehicle_id"] = normalize_id(expenses["vehicle_id"])
    registry["vehicle_id"] = normalize_id(registry["vehicle_id"])

    expenses["date_reference"] = pd.to_datetime(
        expenses["date_reference"], errors="coerce"
    )
    expenses["amount_brl"] = pd.to_numeric(expenses["amount_brl"], errors="coerce")

    if "quantity_liters" in expenses.columns:
        expenses["quantity_liters"] = pd.to_numeric(
            expenses["quantity_liters"], errors="coerce"
        )
    if "distance_km" in expenses.columns:
        expenses["distance_km"] = pd.to_numeric(
            expenses["distance_km"], errors="coerce"
        )
    if "odometer_km" in expenses.columns:
        expenses["odometer_km"] = pd.to_numeric(
            expenses["odometer_km"], errors="coerce"
        )
    if "unit_price_brl" in expenses.columns:
        expenses["unit_price_brl"] = pd.to_numeric(
            expenses["unit_price_brl"], errors="coerce"
        )

    # A duplicate in the registry would make the merge ambiguous.
    duplicate_registry_ids = registry[
        registry["vehicle_id"].duplicated(keep=False)
    ]["vehicle_id"].dropna().unique().tolist()
    if duplicate_registry_ids:
        raise ValueError(
            "O cadastro contém vehicle_id duplicado: "
            + ", ".join(map(str, duplicate_registry_ids))
        )

    # Compare vehicle types after accent/case/spacing normalization.
    expenses["_vehicle_type_check"] = expenses["vehicle_type"].map(normalize_text)
    registry["_vehicle_type_check"] = registry["vehicle_type"].map(normalize_text)

    integrated = expenses.merge(
        registry[
            [
                "vehicle_id", "operation_profile", "benchmark_group",
                "profile_description", "data_origin", "_vehicle_type_check"
            ]
        ],
        on="vehicle_id",
        how="left",
        suffixes=("", "_registry"),
        validate="many_to_one",
        indicator=True,
    )

    integrated["validation_status"] = "OK"
    issues = []

    def add_issue(mask, issue_type, description, severity="Alerta"):
        indexes = integrated.index[mask.fillna(False)].tolist()
        for idx in indexes:
            issues.append({
                "row_number": int(idx) + 2,
                "transaction_id": integrated.at[idx, "transaction_id"]
                    if "transaction_id" in integrated.columns else None,
                "vehicle_id": integrated.at[idx, "vehicle_id"],
                "issue_type": issue_type,
                "severity": severity,
                "description": description,
            })
            integrated.at[idx, "validation_status"] = "Revisar"

    add_issue(
        integrated["_merge"].eq("left_only"),
        "VEHICLE_NOT_REGISTERED",
        "vehicle_id não encontrado no cadastro da frota.",
        "Erro",
    )
    add_issue(
        integrated["_merge"].eq("both")
        & integrated["_vehicle_type_check"].ne(integrated["_vehicle_type_check_registry"]),
        "VEHICLE_TYPE_MISMATCH",
        "vehicle_type do lançamento difere do cadastro da frota.",
        "Erro",
    )
    add_issue(
        integrated["date_reference"].isna(),
        "INVALID_DATE",
        "Data ausente ou inválida.",
        "Erro",
    )
    add_issue(
        integrated["amount_brl"].isna(),
        "INVALID_AMOUNT",
        "Valor da despesa ausente ou não numérico.",
        "Erro",
    )
    add_issue(
        integrated["amount_brl"].lt(0),
        "NEGATIVE_AMOUNT",
        "Valor de despesa negativo; verificar a natureza do lançamento.",
        "Alerta",
    )
    if "transaction_id" in integrated.columns:
        duplicate_tx = integrated["transaction_id"].duplicated(keep=False)
        add_issue(
            duplicate_tx,
            "DUPLICATE_TRANSACTION_ID",
            "transaction_id repetido; verificar possível duplicidade.",
            "Erro",
        )
    add_issue(
        integrated["vehicle_id"].isna() | integrated["vehicle_id"].eq(""),
        "MISSING_VEHICLE_ID",
        "Identificador do veículo ausente.",
        "Erro",
    )

    # Export readable date and remove internal validation columns.
    integrated["date_reference"] = integrated["date_reference"].dt.strftime("%Y-%m-%d")
    integrated = integrated.drop(
        columns=["_merge", "_vehicle_type_check", "_vehicle_type_check_registry"],
        errors="ignore",
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    integrated.to_csv(
        OUTPUT_DIR / "fleet_integrated.csv",
        index=False,
        encoding="utf-8-sig",
    )

    issues_df = pd.DataFrame(
        issues,
        columns=[
            "row_number", "transaction_id", "vehicle_id",
            "issue_type", "severity", "description"
        ],
    )
    issues_df.to_csv(
        OUTPUT_DIR / "data_quality_issues.csv",
        index=False,
        encoding="utf-8-sig",
    )

    summary = {
        "source_files": [EXPENSES_FILE.name, REGISTRY_FILE.name],
        "expense_records": int(len(expenses)),
        "registered_vehicles": int(registry["vehicle_id"].nunique()),
        "integrated_records": int(len(integrated)),
        "records_ok": int(integrated["validation_status"].eq("OK").sum()),
        "records_to_review": int(integrated["validation_status"].eq("Revisar").sum()),
        "issues_by_type": (
            issues_df["issue_type"].value_counts().to_dict()
            if not issues_df.empty else {}
        ),
        "notes": [
            "A integração usa vehicle_id como chave.",
            "O relacionamento esperado é muitos lançamentos para um veículo.",
            "Registros com inconsistências são mantidos e sinalizados; não são apagados automaticamente.",
            "A quilometragem não deve ser somada diretamente entre linhas de despesas."
        ],
    }

    with open(OUTPUT_DIR / "data_quality_report.json", "w", encoding="utf-8") as file:
        json.dump(summary, file, ensure_ascii=False, indent=4)

    print("Integração concluída.")
    print(f"Registros de despesas: {summary['expense_records']}")
    print(f"Veículos cadastrados: {summary['registered_vehicles']}")
    print(f"Registros integrados: {summary['integrated_records']}")
    print(f"Registros OK: {summary['records_ok']}")
    print(f"Registros para revisão: {summary['records_to_review']}")
    print(f"Saídas geradas em: {OUTPUT_DIR.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()

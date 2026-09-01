import json
import os
from pathlib import Path

from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import LoanSet
from xrpl.transaction import sign_loan_set_by_counterparty, submit_and_wait
from xrpl.wallet import Wallet


# Parâmetros opcionais. Mantenha None para usar .env e state.json.
JSON_RPC_URL_OVERRIDE = None
STATE_FILE_PATH_OVERRIDE = None
BORROWER_SEED_OVERRIDE = None
PENDING_LOAN_SET_OVERRIDE: dict | None = None
# PENDING_LOAN_SET_OVERRIDE deve seguir o formato de state["pending_loan_set"].


PROJECT_DIR = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_DIR / ".env")

JSON_RPC_URL = JSON_RPC_URL_OVERRIDE or os.getenv("LENDING_DEVNET_JSON_RPC_URL")
STATE_FILE = Path(
    STATE_FILE_PATH_OVERRIDE
    or os.getenv("STATE_FILE_PATH", str(PROJECT_DIR / "state.json"))
)

BORROWER_SEED = BORROWER_SEED_OVERRIDE or os.getenv("BORROWER_SEED")


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def find_created_loan(response) -> dict | None:
    for node in response.result["meta"]["AffectedNodes"]:
        created = node.get("CreatedNode")
        if created and created["LedgerEntryType"] == "Loan":
            return {
                "loan_id": created["LedgerIndex"],
                "fields": created["NewFields"],
            }

    return None


def main() -> None:
    state = load_state()

    if not JSON_RPC_URL:
        raise ValueError("LENDING_DEVNET_JSON_RPC_URL não está definido.")
    if not BORROWER_SEED:
        raise ValueError("BORROWER_SEED não está definido.")

    pending_loan_set = PENDING_LOAN_SET_OVERRIDE or state.get("pending_loan_set")
    if not pending_loan_set:
        raise ValueError("LoanSet pendente ausente no estado.")

    borrower_wallet = Wallet.from_seed(BORROWER_SEED)
    if pending_loan_set["borrower"] != borrower_wallet.address:
        raise ValueError("O LoanSet pendente não pertence ao borrower configurado.")

    print("Borrower:")
    print(borrower_wallet.address)
    print("Loan broker:")
    print(pending_loan_set["loan_broker"])
    print("Principal requested:")
    print(pending_loan_set["principal_requested"])

    loan_broker_signed_transaction = LoanSet.from_dict(
        pending_loan_set["loan_broker_signed_tx"]
    )
    fully_signed = sign_loan_set_by_counterparty(
        borrower_wallet,
        loan_broker_signed_transaction,
    )

    client = JsonRpcClient(JSON_RPC_URL)
    response = submit_and_wait(
        fully_signed.tx_blob,
        client,
        autofill=False,
    )

    transaction_result = response.result["meta"]["TransactionResult"]
    if transaction_result != "tesSUCCESS":
        raise RuntimeError(f"LoanSet falhou com resultado {transaction_result}.")

    loan = find_created_loan(response)
    if loan is None:
        raise RuntimeError("Loan não encontrado nos metadados.")

    state["borrower"] = {"address": borrower_wallet.address}
    state["loan"] = {
        **loan,
        "principal_requested": pending_loan_set["principal_requested"],
        "payment_total": pending_loan_set["payment_total"],
        "payment_interval": pending_loan_set["payment_interval"],
        "grace_period": pending_loan_set["grace_period"],
        "tx_hash": response.result["hash"],
        "result": transaction_result,
    }
    save_state(state)

    print("LoanSet result:")
    print(transaction_result)
    print("Loan criado:")
    print(loan["loan_id"])
    print("Tx hash:")
    print(response.result["hash"])


if __name__ == "__main__":
    main()

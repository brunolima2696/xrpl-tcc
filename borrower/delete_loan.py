import json
import os
from pathlib import Path

from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import LedgerEntry
from xrpl.models.transactions import LoanDelete
from xrpl.transaction import submit_and_wait
from xrpl.wallet import Wallet


# Parâmetros opcionais. Mantenha None para usar .env e state.json.
JSON_RPC_URL_OVERRIDE = None
STATE_FILE_PATH_OVERRIDE = None
BORROWER_SEED_OVERRIDE = None
LOAN_ID_OVERRIDE = None


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


def main() -> None:
    state = load_state()

    if not JSON_RPC_URL:
        raise ValueError("LENDING_DEVNET_JSON_RPC_URL não está definido.")
    if not BORROWER_SEED:
        raise ValueError("BORROWER_SEED não está definido.")

    loan = state.get("loan")
    loan_id = LOAN_ID_OVERRIDE
    if loan_id is None and loan:
        loan_id = loan.get("loan_id")
    if not loan_id:
        raise ValueError("Loan ausente no estado.")

    borrower_wallet = Wallet.from_seed(BORROWER_SEED)

    print("Borrower:")
    print(borrower_wallet.address)
    print("LoanID:")
    print(loan_id)

    client = JsonRpcClient(JSON_RPC_URL)
    transaction = LoanDelete(
        account=borrower_wallet.address,
        loan_id=loan_id,
    )
    response = submit_and_wait(
        transaction=transaction,
        client=client,
        wallet=borrower_wallet,
    )

    transaction_result = response.result["meta"]["TransactionResult"]
    if transaction_result != "tesSUCCESS":
        raise RuntimeError(
            f"LoanDelete falhou com resultado {transaction_result}."
        )

    state["loan_delete"] = {
        "loan_id": loan_id,
        "tx_hash": response.result["hash"],
        "result": transaction_result,
    }
    if "loan" in state:
        state["loan"]["deleted"] = True
    save_state(state)

    print("LoanDelete result:")
    print(transaction_result)
    print("Tx hash:")
    print(response.result["hash"])

    check_response = client.request(
        LedgerEntry(index=loan_id, ledger_index="validated")
    )
    if check_response.result.get("error") == "entryNotFound":
        print("Loan removido do ledger.")
    else:
        print("Loan ainda encontrado no ledger.")


if __name__ == "__main__":
    main()

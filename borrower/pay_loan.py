import json
import os
from pathlib import Path

from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import LoanPay, LoanPayFlag
from xrpl.transaction import submit_and_wait
from xrpl.wallet import Wallet


# Parâmetros opcionais. Mantenha None para usar .env e state.json.
JSON_RPC_URL_OVERRIDE = None
STATE_FILE_PATH_OVERRIDE = None
BORROWER_SEED_OVERRIDE = None
LOAN_ID_OVERRIDE = None
LOAN_PAYMENT_AMOUNT_DROPS_OVERRIDE = None
LOAN_PAY_FLAGS_OVERRIDE: int | None = None


PROJECT_DIR = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_DIR / ".env")

JSON_RPC_URL = JSON_RPC_URL_OVERRIDE or os.getenv("LENDING_DEVNET_JSON_RPC_URL")
STATE_FILE = Path(
    STATE_FILE_PATH_OVERRIDE
    or os.getenv("STATE_FILE_PATH", str(PROJECT_DIR / "state.json"))
)

BORROWER_SEED = BORROWER_SEED_OVERRIDE or os.getenv("BORROWER_SEED")
LOAN_PAYMENT_AMOUNT_DROPS = LOAN_PAYMENT_AMOUNT_DROPS_OVERRIDE or os.getenv(
    "LOAN_PAYMENT_AMOUNT_DROPS", "10000000"
)
LOAN_PAY_FLAGS = (
    LOAN_PAY_FLAGS_OVERRIDE
    if LOAN_PAY_FLAGS_OVERRIDE is not None
    else LoanPayFlag.TF_LOAN_FULL_PAYMENT
)


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def find_modified_loan(response) -> dict | None:
    for node in response.result["meta"]["AffectedNodes"]:
        modified = node.get("ModifiedNode")
        if modified and modified["LedgerEntryType"] == "Loan":
            return {
                "loan_id": modified["LedgerIndex"],
                "fields": modified.get("FinalFields", {}),
            }

    return None


def build_full_payment_transaction(
    borrower_address: str,
    loan_id: str,
    amount: str,
) -> LoanPay:
    return LoanPay(
        account=borrower_address,
        loan_id=loan_id,
        amount=amount,
        flags=LOAN_PAY_FLAGS,
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
    payment_amount = LOAN_PAYMENT_AMOUNT_DROPS

    print("Borrower:")
    print(borrower_wallet.address)
    print("LoanID:")
    print(loan_id)
    print("Full payment amount:")
    print(payment_amount)

    client = JsonRpcClient(JSON_RPC_URL)
    transaction = build_full_payment_transaction(
        borrower_address=borrower_wallet.address,
        loan_id=loan_id,
        amount=payment_amount,
    )
    response = submit_and_wait(
        transaction=transaction,
        client=client,
        wallet=borrower_wallet,
    )

    transaction_result = response.result["meta"]["TransactionResult"]
    if transaction_result != "tesSUCCESS":
        raise RuntimeError(f"LoanPay falhou com resultado {transaction_result}.")

    loan_after_payment = find_modified_loan(response)
    state["loan_payment"] = {
        "amount": payment_amount,
        "full_payment": True,
        "tx_hash": response.result["hash"],
        "result": transaction_result,
    }
    if loan_after_payment:
        state["loan_payment"]["loan_after_payment"] = loan_after_payment["fields"]
    save_state(state)

    print("LoanPay result:")
    print(transaction_result)
    print("Tx hash:")
    print(response.result["hash"])


if __name__ == "__main__":
    main()

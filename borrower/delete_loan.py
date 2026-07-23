import json
import os
from pathlib import Path

from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import LedgerEntry
from xrpl.models.transactions import LoanDelete
from xrpl.transaction import submit_and_wait
from xrpl.wallet import Wallet


load_dotenv()

JSON_RPC_URL = os.getenv("JSON_RPC_URL")
STATE_FILE = Path(os.getenv("STATE_FILE", "state.json"))

BORROWER_SEED = os.getenv("BORROWER_SEED")

client = JsonRpcClient(JSON_RPC_URL)


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def main():
    state = load_state()

    borrower_wallet = Wallet.from_seed(BORROWER_SEED)
    loan_id = state["loan"]["loan_id"]

    print("Borrower / Holder:")
    print(borrower_wallet.address)

    print("LoanID:")
    print(loan_id)

    tx = LoanDelete(
        account=borrower_wallet.address,
        loan_id=loan_id
    )

    response = submit_and_wait(
        tx,
        client,
        borrower_wallet
    )

    result = response.result["meta"]["TransactionResult"]

    state["loan_delete"] = {
        "loan_id": loan_id,
        "tx_hash": response.result["hash"],
        "result": result
    }

    if "loan" in state:
        state["loan"]["deleted"] = result == "tesSUCCESS"

    save_state(state)

    print("LoanDelete result:")
    print(result)

    print("Tx hash:")
    print(response.result["hash"])

    request = LedgerEntry(
        index=loan_id,
        ledger_index="validated"
    )

    check_response = client.request(request)

    if check_response.status == "error" or check_response.result.get("error") == "entryNotFound":
        print("Loan removido do ledger.")
    else:
        print("Loan ainda no ledger.")
        print(json.dumps(check_response.result, indent=2))


if __name__ == "__main__":
    main()
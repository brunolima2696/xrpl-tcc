import json
import os
from pathlib import Path

from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import LoanSet
from xrpl.transaction import sign_loan_set_by_counterparty, submit_and_wait
from xrpl.wallet import Wallet


load_dotenv()

JSON_RPC_URL = os.getenv("LENDING_DEVNET_JSON_RPC_URL")
STATE_FILE = Path(os.getenv("STATE_FILE_PATH"))

BORROWER_SEED = os.getenv("BORROWER_SEED")

client = JsonRpcClient(JSON_RPC_URL)


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def find_created_ledger_entry(response, ledger_entry_type):
    affected_nodes = response.result["meta"]["AffectedNodes"]

    for node in affected_nodes:
        created = node.get("CreatedNode")
        if created and created["LedgerEntryType"] == ledger_entry_type:
            return {
                "id": created["LedgerIndex"],
                "fields": created["NewFields"]
            }

    return None


def main():
    state = load_state()

    borrower_wallet = Wallet.from_seed(BORROWER_SEED)
    pending_loan_set = state["pending_loan_set"]

    print("Borrower / Holder:")
    print(borrower_wallet.address)

    print("Loan broker:")
    print(pending_loan_set["loan_broker"])

    print("Principal requested:")
    print(pending_loan_set["principal_requested"])

    print("Payment total:")
    print(pending_loan_set["payment_total"])

    print("Payment interval:")
    print(pending_loan_set["payment_interval"])

    print("Grace period:")
    print(pending_loan_set["grace_period"])

    loan_broker_signed_tx = LoanSet.from_dict(
        pending_loan_set["loan_broker_signed_tx"]
    )

    fully_signed = sign_loan_set_by_counterparty(
        borrower_wallet,
        loan_broker_signed_tx
    )

    response = submit_and_wait(
        fully_signed.tx_blob,
        client,
        autofill=False
    )

    loan = find_created_ledger_entry(response, "Loan")

    state["borrower"] = {
        "address": borrower_wallet.address
    }

    state["loan"] = {
        "loan_id": loan["id"],
        "fields": loan["fields"],
        "principal_requested": pending_loan_set["principal_requested"],
        "payment_total": pending_loan_set["payment_total"],
        "payment_interval": pending_loan_set["payment_interval"],
        "grace_period": pending_loan_set["grace_period"],
        "tx_hash": response.result["hash"],
        "result": response.result["meta"]["TransactionResult"]
    }

    save_state(state)

    print("LoanSet result:")
    print(response.result["meta"]["TransactionResult"])

    print("Loan criado:")
    print(loan["id"])

    print("Tx hash:")
    print(response.result["hash"])


if __name__ == "__main__":
    main()
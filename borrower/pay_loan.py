import json
import os
from pathlib import Path

from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import LoanPay
from xrpl.transaction import submit_and_wait
from xrpl.wallet import Wallet


load_dotenv()

JSON_RPC_URL = os.getenv("LENDING_DEVNET_JSON_RPC_URL")
STATE_FILE = Path(os.getenv("STATE_FILE_PATH"))

BORROWER_SEED = os.getenv("BORROWER_SEED")
LOAN_PAYMENT_AMOUNT_DROPS = "10000000"

TF_LOAN_LATE_PAYMENT = 262144 # Pagamento após o vencimento
TF_LOAN_FULL_PAYMENT = 131072 # Pagamento total antecipado

TF_LOAN_PAYMENT = TF_LOAN_LATE_PAYMENT

client = JsonRpcClient(JSON_RPC_URL)


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def find_modified_ledger_entry(response, ledger_entry_type):
    affected_nodes = response.result["meta"]["AffectedNodes"]

    for node in affected_nodes:
        modified = node.get("ModifiedNode")
        if modified and modified["LedgerEntryType"] == ledger_entry_type:
            return {
                "id": modified["LedgerIndex"],
                "fields": modified.get("FinalFields", {})
            }

    return None


def main():
    state = load_state()

    borrower_wallet = Wallet.from_seed(BORROWER_SEED)

    loan_id = state["loan"]["loan_id"]
    payment_amount = LOAN_PAYMENT_AMOUNT_DROPS

    print("Borrower / Holder:")
    print(borrower_wallet.address)

    print("LoanID:")
    print(loan_id)

    print("Payment amount:")
    print(payment_amount)

    tx = LoanPay(
        account=borrower_wallet.address,
        loan_id=loan_id,
        amount=payment_amount,
        flags=TF_LOAN_PAYMENT
    )

    response = submit_and_wait(
        tx,
        client,
        borrower_wallet
    )

    loan = find_modified_ledger_entry(response, "Loan")

    state["loan_payment"] = {
        "amount": payment_amount,
        "tx_hash": response.result["hash"],
        "result": response.result["meta"]["TransactionResult"]
    }

    if loan:
        state["loan_payment"]["loan_after_payment"] = loan["fields"]

    save_state(state)

    print("LoanPay result:")
    print(response.result["meta"]["TransactionResult"])

    if loan and "TotalValueOutstanding" in loan["fields"]:
        print("TotalValueOutstanding:")
        print(loan["fields"]["TotalValueOutstanding"])
    else:
        print("Loan totalmente pago ou sem saldo pendente na metadata.")

    print("Tx hash:")
    print(response.result["hash"])


if __name__ == "__main__":
    main()
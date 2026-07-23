import json
import os
from pathlib import Path

from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import LoanSet
from xrpl.transaction import autofill, sign
from xrpl.wallet import Wallet


load_dotenv()

JSON_RPC_URL = os.getenv("LENDING_DEVNET_JSON_RPC_URL")
STATE_FILE = Path(os.getenv("STATE_FILE", "state.json"))

LOAN_BROKER_SEED = os.getenv("LOAN_BROKER_SEED")
BORROWER_ADDRESS = os.getenv("BORROWER_ADDRESS")

LOAN_PRINCIPAL_REQUESTED = "10000000" # Valor do empréstimo em drops. 1 XRP = 1000000 drops
LOAN_PAYMENT_TOTAL = "1" # Número de parcelas
LOAN_PAYMENT_INTERVAL =  "600" # Intervalo entre pagamento das parcelas em segundos. 30 dias = 2592000 
LOAN_GRACE_PERIOD = "300" # Tolerância após o vencimento da parcela

client = JsonRpcClient(JSON_RPC_URL)


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def main():
    state = load_state()

    loan_broker_wallet = Wallet.from_seed(LOAN_BROKER_SEED)
    loan_broker_id = state["loan_broker_object"]["loan_broker_id"]

    if BORROWER_ADDRESS is None:
        borrower_address = state["borrower"]["address"]
    else:
        borrower_address = BORROWER_ADDRESS

    print("Loan broker:")
    print(loan_broker_wallet.address)

    print("Borrower / Holder:")
    print(borrower_address)

    print("LoanBrokerID:")
    print(loan_broker_id)

    tx = LoanSet(
        account=loan_broker_wallet.address,
        counterparty=borrower_address,
        loan_broker_id=loan_broker_id,
        principal_requested=LOAN_PRINCIPAL_REQUESTED,
        payment_total=int(LOAN_PAYMENT_TOTAL),
        payment_interval=int(LOAN_PAYMENT_INTERVAL),
        grace_period=int(LOAN_GRACE_PERIOD),
        loan_origination_fee="0",
        loan_service_fee="0",
        late_payment_fee="0",
        close_payment_fee="0",
        overpayment_fee=0,
        interest_rate=0,
        late_interest_rate=0,
        close_interest_rate=0,
        overpayment_interest_rate=0
    )

    autofilled_tx = autofill(tx, client)
    loan_broker_signed_tx = sign(autofilled_tx, loan_broker_wallet)

    state["pending_loan_set"] = {
        "loan_broker_signed_tx": loan_broker_signed_tx.to_dict(),
        "loan_broker": loan_broker_wallet.address,
        "borrower": borrower_address,
        "loan_broker_id": loan_broker_id,
        "principal_requested": LOAN_PRINCIPAL_REQUESTED,
        "payment_total": LOAN_PAYMENT_TOTAL,
        "payment_interval": LOAN_PAYMENT_INTERVAL,
        "grace_period": LOAN_GRACE_PERIOD
    }

    save_state(state)

    print("LoanSet preparado e assinado pelo loan_broker.")


if __name__ == "__main__":
    main()
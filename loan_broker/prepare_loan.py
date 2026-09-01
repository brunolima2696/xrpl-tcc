import json
import os
from pathlib import Path

from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import LoanSet
from xrpl.transaction import autofill, sign
from xrpl.wallet import Wallet

try:
    from loan_broker.credential_validation import authorize_borrower
except ModuleNotFoundError:
    from credential_validation import authorize_borrower


# Parâmetros opcionais. Mantenha None para usar .env, state.json e rules.json.
JSON_RPC_URL_OVERRIDE = None
STATE_FILE_PATH_OVERRIDE = None
RULES_FILE_PATH_OVERRIDE = None
LOAN_BROKER_SEED_OVERRIDE = None
LOAN_BROKER_ID_OVERRIDE = None
BORROWER_ADDRESS_OVERRIDE = None
LOAN_PRINCIPAL_REQUESTED_OVERRIDE = None
LOAN_PAYMENT_TOTAL_OVERRIDE: int | None = None
LOAN_PAYMENT_INTERVAL_OVERRIDE: int | None = None
LOAN_GRACE_PERIOD_OVERRIDE: int | None = None
LOAN_ORIGINATION_FEE_OVERRIDE = None
LOAN_SERVICE_FEE_OVERRIDE = None
LATE_PAYMENT_FEE_OVERRIDE = None
CLOSE_PAYMENT_FEE_OVERRIDE = None
OVERPAYMENT_FEE_OVERRIDE: int | None = None
INTEREST_RATE_OVERRIDE: int | None = None
LATE_INTEREST_RATE_OVERRIDE: int | None = None
CLOSE_INTEREST_RATE_OVERRIDE: int | None = None
OVERPAYMENT_INTEREST_RATE_OVERRIDE: int | None = None


PROJECT_DIR = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_DIR / ".env")

JSON_RPC_URL = JSON_RPC_URL_OVERRIDE or os.getenv("LENDING_DEVNET_JSON_RPC_URL")
STATE_FILE = Path(
    STATE_FILE_PATH_OVERRIDE
    or os.getenv("STATE_FILE_PATH", str(PROJECT_DIR / "state.json"))
)
RULES_FILE = Path(
    RULES_FILE_PATH_OVERRIDE
    or os.getenv("RULES_FILE_PATH", str(PROJECT_DIR / "loan_broker" / "rules.json"))
)

LOAN_BROKER_SEED = LOAN_BROKER_SEED_OVERRIDE or os.getenv("LOAN_BROKER_SEED")
BORROWER_ADDRESS = BORROWER_ADDRESS_OVERRIDE or os.getenv("BORROWER_ADDRESS")

LOAN_PRINCIPAL_REQUESTED = LOAN_PRINCIPAL_REQUESTED_OVERRIDE or os.getenv(
    "LOAN_PRINCIPAL_REQUESTED", "10000000"
)
LOAN_PAYMENT_TOTAL = (
    LOAN_PAYMENT_TOTAL_OVERRIDE
    if LOAN_PAYMENT_TOTAL_OVERRIDE is not None
    else int(os.getenv("LOAN_PAYMENT_TOTAL", "1"))
)
LOAN_PAYMENT_INTERVAL = (
    LOAN_PAYMENT_INTERVAL_OVERRIDE
    if LOAN_PAYMENT_INTERVAL_OVERRIDE is not None
    else int(os.getenv("LOAN_PAYMENT_INTERVAL", "600"))
)
LOAN_GRACE_PERIOD = (
    LOAN_GRACE_PERIOD_OVERRIDE
    if LOAN_GRACE_PERIOD_OVERRIDE is not None
    else int(os.getenv("LOAN_GRACE_PERIOD", "300"))
)
LOAN_ORIGINATION_FEE = LOAN_ORIGINATION_FEE_OVERRIDE or os.getenv(
    "LOAN_ORIGINATION_FEE", "0"
)
LOAN_SERVICE_FEE = LOAN_SERVICE_FEE_OVERRIDE or os.getenv("LOAN_SERVICE_FEE", "0")
LATE_PAYMENT_FEE = LATE_PAYMENT_FEE_OVERRIDE or os.getenv("LATE_PAYMENT_FEE", "0")
CLOSE_PAYMENT_FEE = CLOSE_PAYMENT_FEE_OVERRIDE or os.getenv(
    "CLOSE_PAYMENT_FEE", "0"
)
OVERPAYMENT_FEE = (
    OVERPAYMENT_FEE_OVERRIDE
    if OVERPAYMENT_FEE_OVERRIDE is not None
    else int(os.getenv("OVERPAYMENT_FEE", "0"))
)
INTEREST_RATE = (
    INTEREST_RATE_OVERRIDE
    if INTEREST_RATE_OVERRIDE is not None
    else int(os.getenv("INTEREST_RATE", "0"))
)
LATE_INTEREST_RATE = (
    LATE_INTEREST_RATE_OVERRIDE
    if LATE_INTEREST_RATE_OVERRIDE is not None
    else int(os.getenv("LATE_INTEREST_RATE", "0"))
)
CLOSE_INTEREST_RATE = (
    CLOSE_INTEREST_RATE_OVERRIDE
    if CLOSE_INTEREST_RATE_OVERRIDE is not None
    else int(os.getenv("CLOSE_INTEREST_RATE", "0"))
)
OVERPAYMENT_INTEREST_RATE = (
    OVERPAYMENT_INTEREST_RATE_OVERRIDE
    if OVERPAYMENT_INTEREST_RATE_OVERRIDE is not None
    else int(os.getenv("OVERPAYMENT_INTEREST_RATE", "0"))
)

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_rules():
    try:
        return json.loads(RULES_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Arquivo não encontrado: {RULES_FILE}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON inválido em {RULES_FILE}: {exc}") from exc


def main():
    state = load_state()

    if not JSON_RPC_URL:
        raise ValueError("LENDING_DEVNET_JSON_RPC_URL não está definido.")
    if not LOAN_BROKER_SEED:
        raise ValueError("LOAN_BROKER_SEED não está definido.")

    loan_broker_wallet = Wallet.from_seed(LOAN_BROKER_SEED)
    permissioned_loan_broker = state.get("permissioned_loan_broker")
    loan_broker_id = LOAN_BROKER_ID_OVERRIDE
    if loan_broker_id is None and permissioned_loan_broker:
        loan_broker_id = permissioned_loan_broker.get("loan_broker_id")
    if not loan_broker_id:
        raise ValueError(
            "Permissioned LoanBroker ausente. Execute "
            "set_permissioned_loan_broker.py primeiro."
        )

    if BORROWER_ADDRESS is None:
        borrower = state.get("borrower")
        if not borrower or not borrower.get("address"):
            raise ValueError("BORROWER_ADDRESS não está definido.")
        borrower_address = borrower["address"]
    else:
        borrower_address = BORROWER_ADDRESS

    client = JsonRpcClient(JSON_RPC_URL)
    borrower_authorization = authorize_borrower(
        client=client,
        borrower_address=borrower_address,
        rules=load_rules(),
    )

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
        payment_total=LOAN_PAYMENT_TOTAL,
        payment_interval=LOAN_PAYMENT_INTERVAL,
        grace_period=LOAN_GRACE_PERIOD,
        loan_origination_fee=LOAN_ORIGINATION_FEE,
        loan_service_fee=LOAN_SERVICE_FEE,
        late_payment_fee=LATE_PAYMENT_FEE,
        close_payment_fee=CLOSE_PAYMENT_FEE,
        overpayment_fee=OVERPAYMENT_FEE,
        interest_rate=INTEREST_RATE,
        late_interest_rate=LATE_INTEREST_RATE,
        close_interest_rate=CLOSE_INTEREST_RATE,
        overpayment_interest_rate=OVERPAYMENT_INTEREST_RATE,
    )

    autofilled_tx = autofill(tx, client)
    loan_broker_signed_tx = sign(autofilled_tx, loan_broker_wallet)

    state["pending_loan_set"] = {
        "loan_broker_signed_tx": loan_broker_signed_tx.to_dict(),
        "loan_broker": loan_broker_wallet.address,
        "borrower": borrower_address,
        "loan_broker_id": loan_broker_id,
        "borrower_authorization": borrower_authorization,
        "principal_requested": LOAN_PRINCIPAL_REQUESTED,
        "payment_total": str(LOAN_PAYMENT_TOTAL),
        "payment_interval": str(LOAN_PAYMENT_INTERVAL),
        "grace_period": str(LOAN_GRACE_PERIOD),
    }

    save_state(state)

    print("LoanSet preparado e assinado pelo loan_broker.")


if __name__ == "__main__":
    main()

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import LoanBrokerSet
from xrpl.transaction import submit_and_wait
from xrpl.wallet import Wallet


# Parâmetros opcionais. Mantenha None para usar .env e state.json.
JSON_RPC_URL_OVERRIDE = None
STATE_FILE_PATH_OVERRIDE = None
LOAN_BROKER_SEED_OVERRIDE = None
VAULT_ID_OVERRIDE = None
MANAGEMENT_FEE_RATE_OVERRIDE: int | None = None
DEBT_MAXIMUM_OVERRIDE = None
COVER_RATE_MINIMUM_OVERRIDE: int | None = None
COVER_RATE_LIQUIDATION_OVERRIDE: int | None = None


PROJECT_DIR = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_DIR / ".env")

STATE_FILE = Path(
    STATE_FILE_PATH_OVERRIDE
    or os.getenv("STATE_FILE_PATH", str(PROJECT_DIR / "state.json"))
)

MANAGEMENT_FEE_RATE = (
    MANAGEMENT_FEE_RATE_OVERRIDE
    if MANAGEMENT_FEE_RATE_OVERRIDE is not None
    else int(os.getenv("LOAN_BROKER_MANAGEMENT_FEE_RATE", "0"))
)
DEBT_MAXIMUM = DEBT_MAXIMUM_OVERRIDE or os.getenv("LOAN_BROKER_DEBT_MAXIMUM")
COVER_RATE_MINIMUM = (
    COVER_RATE_MINIMUM_OVERRIDE
    if COVER_RATE_MINIMUM_OVERRIDE is not None
    else int(os.getenv("LOAN_BROKER_COVER_RATE_MINIMUM", "0"))
)
COVER_RATE_LIQUIDATION = (
    COVER_RATE_LIQUIDATION_OVERRIDE
    if COVER_RATE_LIQUIDATION_OVERRIDE is not None
    else int(os.getenv("LOAN_BROKER_COVER_RATE_LIQUIDATION", "0"))
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


def find_created_loan_broker(response) -> dict | None:
    for node in response.result["meta"]["AffectedNodes"]:
        created = node.get("CreatedNode")
        if created and created["LedgerEntryType"] == "LoanBroker":
            return {
                "loan_broker_id": created["LedgerIndex"],
                "fields": created["NewFields"],
            }

    return None


def build_loan_broker_transaction(account: str, vault_id: str) -> LoanBrokerSet:
    return LoanBrokerSet(
        account=account,
        vault_id=vault_id,
        management_fee_rate=MANAGEMENT_FEE_RATE,
        debt_maximum=DEBT_MAXIMUM,
        cover_rate_minimum=COVER_RATE_MINIMUM,
        cover_rate_liquidation=COVER_RATE_LIQUIDATION,
    )


def main() -> None:
    state = load_state()

    if "permissioned_loan_broker" in state:
        print("Permissioned LoanBroker já existe:")
        print(state["permissioned_loan_broker"]["loan_broker_id"])
        return

    private_vault = state.get("private_vault")
    vault_id = VAULT_ID_OVERRIDE
    if vault_id is None and private_vault:
        vault_id = private_vault.get("vault_id")
    if not vault_id:
        raise ValueError(
            "Private Vault ausente. Execute create_private_vault.py primeiro."
        )

    json_rpc_url = JSON_RPC_URL_OVERRIDE or os.getenv("LENDING_DEVNET_JSON_RPC_URL")
    loan_broker_seed = LOAN_BROKER_SEED_OVERRIDE or os.getenv("LOAN_BROKER_SEED")

    if not json_rpc_url:
        raise ValueError("LENDING_DEVNET_JSON_RPC_URL não está definido.")
    if not loan_broker_seed:
        raise ValueError("LOAN_BROKER_SEED não está definido.")

    loan_broker_wallet = Wallet.from_seed(loan_broker_seed)
    client = JsonRpcClient(json_rpc_url)
    transaction = build_loan_broker_transaction(
        account=loan_broker_wallet.address,
        vault_id=vault_id,
    )

    response = submit_and_wait(
        transaction=transaction,
        client=client,
        wallet=loan_broker_wallet,
    )

    transaction_result = response.result["meta"]["TransactionResult"]
    if transaction_result != "tesSUCCESS":
        raise RuntimeError(
            f"LoanBrokerSet falhou com resultado {transaction_result}."
        )

    loan_broker = find_created_loan_broker(response)
    if loan_broker is None:
        raise RuntimeError("LoanBroker não encontrado nos metadados.")

    state["permissioned_loan_broker"] = {
        **loan_broker,
        "vault_id": vault_id,
        "tx_hash": response.result["hash"],
    }
    save_state(state)

    print("Permissioned LoanBroker criado:")
    print(loan_broker["loan_broker_id"])
    print("Tx hash:")
    print(response.result["hash"])


if __name__ == "__main__":
    main()

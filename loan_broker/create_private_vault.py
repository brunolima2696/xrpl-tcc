import json
import os
from pathlib import Path

from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.models.currencies import XRP
from xrpl.models.transactions import VaultCreate
from xrpl.models.transactions.vault_create import VaultCreateFlag
from xrpl.transaction import submit_and_wait
from xrpl.wallet import Wallet


# Parâmetros opcionais. Mantenha None para usar .env e state.json.
JSON_RPC_URL_OVERRIDE = None
STATE_FILE_PATH_OVERRIDE = None
LOAN_BROKER_SEED_OVERRIDE = None
DOMAIN_ID_OVERRIDE = None
ASSETS_MAXIMUM_OVERRIDE = None
WITHDRAWAL_POLICY_OVERRIDE: int | None = None
VAULT_CREATE_FEE_OVERRIDE = None


PROJECT_DIR = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_DIR / ".env")

STATE_FILE = Path(
    STATE_FILE_PATH_OVERRIDE
    or os.getenv("STATE_FILE_PATH", str(PROJECT_DIR / "state.json"))
)

ASSETS_MAXIMUM = ASSETS_MAXIMUM_OVERRIDE or os.getenv(
    "VAULT_ASSETS_MAXIMUM", "1000000000"
)
WITHDRAWAL_POLICY = (
    WITHDRAWAL_POLICY_OVERRIDE
    if WITHDRAWAL_POLICY_OVERRIDE is not None
    else int(os.getenv("VAULT_WITHDRAWAL_POLICY", "1"))
)
VAULT_CREATE_FEE = VAULT_CREATE_FEE_OVERRIDE or os.getenv(
    "VAULT_CREATE_FEE", "200000"
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


def find_created_vault(response) -> dict | None:
    for node in response.result["meta"]["AffectedNodes"]:
        created = node.get("CreatedNode")
        if created and created["LedgerEntryType"] == "Vault":
            return {
                "vault_id": created["LedgerIndex"],
                "fields": created["NewFields"],
            }

    return None


def build_private_vault_transaction(account: str, domain_id: str) -> VaultCreate:
    return VaultCreate(
        account=account,
        asset=XRP(),
        assets_maximum=ASSETS_MAXIMUM,
        withdrawal_policy=WITHDRAWAL_POLICY,
        domain_id=domain_id,
        flags=VaultCreateFlag.TF_VAULT_PRIVATE,
        fee=VAULT_CREATE_FEE,
    )


def main() -> None:
    state = load_state()

    if "private_vault" in state:
        print("Private Vault já existe:")
        print(state["private_vault"]["vault_id"])
        return

    permissioned_domain = state.get("permissioned_domain")
    domain_id = DOMAIN_ID_OVERRIDE
    if domain_id is None and permissioned_domain:
        domain_id = permissioned_domain.get("domain_id")
    if not domain_id:
        raise ValueError(
            "PermissionedDomain ausente. Execute create_permissioned_domain.py primeiro."
        )

    json_rpc_url = JSON_RPC_URL_OVERRIDE or os.getenv("LENDING_DEVNET_JSON_RPC_URL")
    loan_broker_seed = LOAN_BROKER_SEED_OVERRIDE or os.getenv("LOAN_BROKER_SEED")

    if not json_rpc_url:
        raise ValueError("LENDING_DEVNET_JSON_RPC_URL não está definido.")
    if not loan_broker_seed:
        raise ValueError("LOAN_BROKER_SEED não está definido.")

    loan_broker_wallet = Wallet.from_seed(loan_broker_seed)
    client = JsonRpcClient(json_rpc_url)
    transaction = build_private_vault_transaction(
        account=loan_broker_wallet.address,
        domain_id=domain_id,
    )

    response = submit_and_wait(
        transaction=transaction,
        client=client,
        wallet=loan_broker_wallet,
        check_fee=False,
    )

    transaction_result = response.result["meta"]["TransactionResult"]
    if transaction_result != "tesSUCCESS":
        raise RuntimeError(f"VaultCreate falhou com resultado {transaction_result}.")

    vault = find_created_vault(response)
    if vault is None:
        raise RuntimeError("Private Vault não encontrado nos metadados.")

    state["loan_broker"] = {"address": loan_broker_wallet.address}
    state["private_vault"] = {
        **vault,
        "domain_id": domain_id,
        "tx_hash": response.result["hash"],
    }
    save_state(state)

    print("Private Vault criado:")
    print(vault["vault_id"])
    print("Tx hash:")
    print(response.result["hash"])


if __name__ == "__main__":
    main()

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import VaultDeposit
from xrpl.transaction import submit_and_wait
from xrpl.wallet import Wallet


# Parâmetros opcionais. Mantenha None para usar .env e state.json.
JSON_RPC_URL_OVERRIDE = None
STATE_FILE_PATH_OVERRIDE = None
DEPOSITOR_SEED_OVERRIDE = None
VAULT_ID_OVERRIDE = None
DEPOSIT_AMOUNT_DROPS_OVERRIDE = None
CREDENTIAL_ACCEPTED_OVERRIDE: bool | None = None


PROJECT_DIR = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_DIR / ".env")

STATE_FILE = Path(
    STATE_FILE_PATH_OVERRIDE
    or os.getenv("STATE_FILE_PATH", str(PROJECT_DIR / "state.json"))
)
DEPOSIT_AMOUNT_DROPS = DEPOSIT_AMOUNT_DROPS_OVERRIDE or os.getenv(
    "DEPOSIT_AMOUNT_DROPS", "50000000"
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


def build_deposit_transaction(
    depositor_address: str,
    vault_id: str,
    amount: str,
) -> VaultDeposit:
    return VaultDeposit(
        account=depositor_address,
        vault_id=vault_id,
        amount=amount,
    )


def main() -> None:
    state = load_state()

    if "private_vault_deposit" in state:
        print("Depósito no Private Vault já existe:")
        print(state["private_vault_deposit"]["tx_hash"])
        return

    private_vault = state.get("private_vault")
    vault_id = VAULT_ID_OVERRIDE
    if vault_id is None and private_vault:
        vault_id = private_vault.get("vault_id")
    if not vault_id:
        raise ValueError("Private Vault ausente.")

    credential = state.get("credentials", {}).get("depositor")
    credential_accepted = (
        CREDENTIAL_ACCEPTED_OVERRIDE
        if CREDENTIAL_ACCEPTED_OVERRIDE is not None
        else bool(credential and credential.get("accepted"))
    )
    if not credential_accepted:
        raise ValueError("A Credential do depositor ainda não foi aceita.")

    json_rpc_url = JSON_RPC_URL_OVERRIDE or os.getenv("LENDING_DEVNET_JSON_RPC_URL")
    depositor_seed = DEPOSITOR_SEED_OVERRIDE or os.getenv("DEPOSITOR_SEED")

    if not json_rpc_url:
        raise ValueError("LENDING_DEVNET_JSON_RPC_URL não está definido.")
    if not depositor_seed:
        raise ValueError("DEPOSITOR_SEED não está definido.")

    depositor_wallet = Wallet.from_seed(depositor_seed)
    if (
        CREDENTIAL_ACCEPTED_OVERRIDE is None
        and credential
        and credential.get("subject") != depositor_wallet.address
    ):
        raise ValueError("A Credential aceita não pertence ao depositor configurado.")

    client = JsonRpcClient(json_rpc_url)
    transaction = build_deposit_transaction(
        depositor_address=depositor_wallet.address,
        vault_id=vault_id,
        amount=DEPOSIT_AMOUNT_DROPS,
    )
    response = submit_and_wait(
        transaction=transaction,
        client=client,
        wallet=depositor_wallet,
    )

    transaction_result = response.result["meta"]["TransactionResult"]
    if transaction_result != "tesSUCCESS":
        raise RuntimeError(
            f"VaultDeposit falhou com resultado {transaction_result}."
        )

    state["depositor"] = {"address": depositor_wallet.address}
    state["private_vault_deposit"] = {
        "vault_id": vault_id,
        "amount": DEPOSIT_AMOUNT_DROPS,
        "tx_hash": response.result["hash"],
        "result": transaction_result,
    }
    save_state(state)

    print("VaultDeposit no Private Vault concluído.")
    print("Tx hash:")
    print(response.result["hash"])


if __name__ == "__main__":
    main()

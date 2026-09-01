import json
import os
from pathlib import Path

from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import CredentialAccept
from xrpl.transaction import submit_and_wait
from xrpl.utils import str_to_hex
from xrpl.wallet import Wallet


# Parâmetros opcionais. Mantenha None para usar .env e state.json.
JSON_RPC_URL_OVERRIDE = None
STATE_FILE_PATH_OVERRIDE = None
BORROWER_SEED_OVERRIDE = None
ISSUER_ADDRESS_OVERRIDE = None
CREDENTIAL_TYPE_OVERRIDE = None


PROJECT_DIR = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_DIR / ".env")

STATE_FILE = Path(
    STATE_FILE_PATH_OVERRIDE
    or os.getenv("STATE_FILE_PATH", str(PROJECT_DIR / "state.json"))
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


def build_accept_transaction(
    subject_address: str,
    issuer_address: str,
    credential_type_hex: str,
) -> CredentialAccept:
    return CredentialAccept(
        account=subject_address,
        issuer=issuer_address,
        credential_type=credential_type_hex,
    )


def main() -> None:
    state = load_state()
    credential = state.get("credentials", {}).get("borrower")
    using_credential_override = (
        ISSUER_ADDRESS_OVERRIDE is not None or CREDENTIAL_TYPE_OVERRIDE is not None
    )

    if credential and credential.get("accepted") and not using_credential_override:
        print("Credential do borrower já foi aceita:")
        print(credential.get("credential_id", "parâmetros hardcoded"))
        return

    issuer_address = ISSUER_ADDRESS_OVERRIDE or (
        credential.get("issuer") if credential else None
    )
    credential_type_hex = (
        str_to_hex(CREDENTIAL_TYPE_OVERRIDE)
        if CREDENTIAL_TYPE_OVERRIDE is not None
        else credential.get("credential_type_hex") if credential else None
    )
    if not issuer_address or not credential_type_hex:
        raise ValueError(
            "Informe ISSUER_ADDRESS_OVERRIDE e CREDENTIAL_TYPE_OVERRIDE ou "
            "emita a Credential antes do aceite."
        )

    json_rpc_url = JSON_RPC_URL_OVERRIDE or os.getenv("LENDING_DEVNET_JSON_RPC_URL")
    borrower_seed = BORROWER_SEED_OVERRIDE or os.getenv("BORROWER_SEED")

    if not json_rpc_url:
        raise ValueError("LENDING_DEVNET_JSON_RPC_URL não está definido.")
    if not borrower_seed:
        raise ValueError("BORROWER_SEED não está definido.")

    borrower_wallet = Wallet.from_seed(borrower_seed)
    if credential and credential.get("subject") != borrower_wallet.address:
        raise ValueError("A Credential armazenada não pertence ao borrower configurado.")

    client = JsonRpcClient(json_rpc_url)
    transaction = build_accept_transaction(
        subject_address=borrower_wallet.address,
        issuer_address=issuer_address,
        credential_type_hex=credential_type_hex,
    )
    response = submit_and_wait(
        transaction=transaction,
        client=client,
        wallet=borrower_wallet,
    )

    transaction_result = response.result["meta"]["TransactionResult"]
    if transaction_result != "tesSUCCESS":
        raise RuntimeError(
            f"CredentialAccept falhou com resultado {transaction_result}."
        )

    if credential is None:
        credential = {
            "issuer": issuer_address,
            "subject": borrower_wallet.address,
            "credential_type": CREDENTIAL_TYPE_OVERRIDE,
            "credential_type_hex": credential_type_hex,
        }
        state.setdefault("credentials", {})["borrower"] = credential
    credential["accepted"] = True
    credential["accept_tx_hash"] = response.result["hash"]
    save_state(state)

    print("Credential do borrower aceita.")
    print("Tx hash:")
    print(response.result["hash"])


if __name__ == "__main__":
    main()

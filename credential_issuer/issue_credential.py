import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.core.addresscodec import is_valid_classic_address
from xrpl.models.transactions import CredentialCreate
from xrpl.transaction import submit_and_wait
from xrpl.utils import str_to_hex
from xrpl.wallet import Wallet


# Parâmetros opcionais. Mantenha None para usar CLI, .env, state.json e rules.json.
ROLE_OVERRIDE = None  # "depositor" ou "borrower"
JSON_RPC_URL_OVERRIDE = None
STATE_FILE_PATH_OVERRIDE = None
RULES_FILE_PATH_OVERRIDE = None
ISSUER_SEED_OVERRIDE = None
SUBJECT_ADDRESS_OVERRIDE = None
SUBJECT_SEED_OVERRIDE = None
CREDENTIAL_TYPE_OVERRIDE = None


PROJECT_DIR = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_DIR / ".env")

RULES_FILE = Path(
    RULES_FILE_PATH_OVERRIDE
    or os.getenv("RULES_FILE_PATH", str(PROJECT_DIR / "loan_broker" / "rules.json"))
)
STATE_FILE = Path(
    STATE_FILE_PATH_OVERRIDE
    or os.getenv("STATE_FILE_PATH", str(PROJECT_DIR / "state.json"))
)

ROLE_CONFIG = {
    "depositor": {
        "subject_seed_env": "DEPOSITOR_SEED",
        "credential_type_env": "DEPOSITOR_CREDENTIAL_TYPE",
    },
    "borrower": {
        "subject_seed_env": "BORROWER_SEED",
        "credential_type_env": "BORROWER_CREDENTIAL_TYPE",
    },
}


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Arquivo não encontrado: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON inválido em {path}: {exc}") from exc


def save_state(state: dict) -> None:
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def select_credential_type(
    rules: dict,
    role: str,
    issuer_address: str,
    requested_type: str | None,
) -> str:
    role_rules = rules.get(role)
    if not isinstance(role_rules, dict):
        raise ValueError(f"rules.json deve conter o objeto '{role}'.")

    issuers = role_rules.get("issuers")
    if not isinstance(issuers, list):
        raise ValueError(f"{role}.issuers deve ser uma lista.")

    for issuer_rule in issuers:
        if issuer_rule.get("address") != issuer_address:
            continue

        credential_types = issuer_rule.get("credentialTypes")
        if not isinstance(credential_types, list) or not credential_types:
            raise ValueError(
                f"O issuer {issuer_address} não possui CredentialTypes para {role}."
            )

        if requested_type is not None:
            if requested_type not in credential_types:
                raise ValueError(
                    f"CredentialType '{requested_type}' não é permitido para o "
                    f"issuer {issuer_address} em {role}."
                )
            selected_type = requested_type
        else:
            selected_type = credential_types[0]

        type_size = len(selected_type.encode("utf-8"))
        if not 1 <= type_size <= 64:
            raise ValueError("CredentialType deve possuir entre 1 e 64 bytes.")

        return selected_type

    raise ValueError(
        f"O issuer {issuer_address} não está autorizado pelas regras de {role}."
    )


def find_created_credential(response) -> dict | None:
    for node in response.result["meta"]["AffectedNodes"]:
        created = node.get("CreatedNode")
        if created and created["LedgerEntryType"] == "Credential":
            return {
                "credential_id": created["LedgerIndex"],
                "fields": created["NewFields"],
            }

    return None


def build_credential_transaction(
    issuer_address: str,
    subject_address: str,
    credential_type: str,
) -> CredentialCreate:
    return CredentialCreate(
        account=issuer_address,
        subject=subject_address,
        credential_type=str_to_hex(credential_type),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Emite uma Credential para Depositor ou Borrower."
    )
    parser.add_argument("role", nargs="?", choices=ROLE_CONFIG)
    parser.add_argument(
        "--credential-type",
        help="Tipo configurado em rules.json; usa o primeiro permitido se omitido.",
    )
    args = parser.parse_args()

    role = ROLE_OVERRIDE or args.role
    if role not in ROLE_CONFIG:
        parser.error("Informe a role 'depositor' ou 'borrower'.")

    state = load_json(STATE_FILE) if STATE_FILE.exists() else {}
    existing_credential = state.get("credentials", {}).get(role)
    if existing_credential:
        print(f"Credential de {role} já existe:")
        print(existing_credential["credential_id"])
        return

    json_rpc_url = JSON_RPC_URL_OVERRIDE or os.getenv("LENDING_DEVNET_JSON_RPC_URL")
    issuer_seed = (
        ISSUER_SEED_OVERRIDE
        or os.getenv("CREDENTIAL_ISSUER_SEED")
        or os.getenv("ISSUER_SEED")
    )
    subject_seed_env = ROLE_CONFIG[role]["subject_seed_env"]

    if not json_rpc_url:
        raise ValueError("LENDING_DEVNET_JSON_RPC_URL não está definido.")
    if not issuer_seed:
        raise ValueError("CREDENTIAL_ISSUER_SEED não está definido.")

    issuer_wallet = Wallet.from_seed(issuer_seed)
    subject_address = SUBJECT_ADDRESS_OVERRIDE
    if subject_address is None:
        subject_seed = SUBJECT_SEED_OVERRIDE or os.getenv(subject_seed_env)
        if not subject_seed:
            raise ValueError(
                f"Defina SUBJECT_ADDRESS_OVERRIDE ou {subject_seed_env}."
            )
        subject_address = Wallet.from_seed(subject_seed).address
    elif not is_valid_classic_address(subject_address):
        raise ValueError("SUBJECT_ADDRESS_OVERRIDE não é um endereço XRPL válido.")

    requested_type = (
        CREDENTIAL_TYPE_OVERRIDE
        or args.credential_type
        or os.getenv(ROLE_CONFIG[role]["credential_type_env"])
    )
    rules = load_json(RULES_FILE)
    credential_type = select_credential_type(
        rules=rules,
        role=role,
        issuer_address=issuer_wallet.address,
        requested_type=requested_type,
    )

    client = JsonRpcClient(json_rpc_url)
    transaction = build_credential_transaction(
        issuer_address=issuer_wallet.address,
        subject_address=subject_address,
        credential_type=credential_type,
    )
    response = submit_and_wait(
        transaction=transaction,
        client=client,
        wallet=issuer_wallet,
    )

    transaction_result = response.result["meta"]["TransactionResult"]
    if transaction_result != "tesSUCCESS":
        raise RuntimeError(
            f"CredentialCreate falhou com resultado {transaction_result}."
        )

    credential = find_created_credential(response)
    if credential is None:
        raise RuntimeError("Credential não encontrada nos metadados.")

    state.setdefault("credentials", {})[role] = {
        **credential,
        "issuer": issuer_wallet.address,
        "subject": subject_address,
        "credential_type": credential_type,
        "credential_type_hex": str_to_hex(credential_type),
        "accepted": False,
        "tx_hash": response.result["hash"],
    }
    save_state(state)

    print(f"Credential de {role} emitida:")
    print(credential["credential_id"])
    print("CredentialType:")
    print(credential_type)
    print("Tx hash:")
    print(response.result["hash"])


if __name__ == "__main__":
    main()

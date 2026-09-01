import json
import os
from pathlib import Path

from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.core.addresscodec import is_valid_classic_address
from xrpl.models.transactions import PermissionedDomainSet
from xrpl.models.transactions.deposit_preauth import Credential
from xrpl.transaction import submit_and_wait
from xrpl.utils import str_to_hex
from xrpl.wallet import Wallet


# Parâmetros opcionais. Mantenha None para usar .env, state.json e rules.json.
JSON_RPC_URL_OVERRIDE = None
STATE_FILE_PATH_OVERRIDE = None
RULES_FILE_PATH_OVERRIDE = None
LOAN_BROKER_SEED_OVERRIDE = None
ACCEPTED_CREDENTIALS_OVERRIDE: list[dict[str, str]] | None = None
# Exemplo: [{"issuer": "r...", "credential_type": "DepositorTypeA"}]


PROJECT_DIR = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_DIR / ".env")

RULES_FILE = Path(
    RULES_FILE_PATH_OVERRIDE
    or os.getenv("RULES_FILE_PATH", str(PROJECT_DIR / "loan_broker" / "rules.json"))
)
STATE_FILE = Path(
    STATE_FILE_PATH_OVERRIDE
    or os.getenv("STATE_FILE_PATH", str(PROJECT_DIR / "loan_broker" / "state.json"))
)


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


def build_depositor_credentials(rules: dict) -> list[Credential]:
    depositor_rules = rules.get("depositor")
    if not isinstance(depositor_rules, dict):
        raise ValueError("rules.json deve conter o objeto 'depositor'.")

    issuers = depositor_rules.get("issuers")
    if not isinstance(issuers, list) or not issuers:
        raise ValueError("depositor.issuers deve ser uma lista não vazia.")

    credentials: list[Credential] = []
    seen: set[tuple[str, str]] = set()

    for issuer_index, issuer_rule in enumerate(issuers):
        if not isinstance(issuer_rule, dict):
            raise ValueError(f"depositor.issuers[{issuer_index}] deve ser um objeto.")

        address = issuer_rule.get("address")
        if not isinstance(address, str) or not is_valid_classic_address(address):
            raise ValueError(
                f"Endereço XRPL inválido em depositor.issuers[{issuer_index}].address."
            )

        credential_types = issuer_rule.get("credentialTypes")
        if not isinstance(credential_types, list) or not credential_types:
            raise ValueError(
                f"depositor.issuers[{issuer_index}].credentialTypes deve ser "
                "uma lista não vazia."
            )

        for type_index, credential_type in enumerate(credential_types):
            if not isinstance(credential_type, str):
                raise ValueError(
                    "CredentialType inválido em "
                    f"depositor.issuers[{issuer_index}].credentialTypes[{type_index}]."
                )

            credential_type_size = len(credential_type.encode("utf-8"))
            if not 1 <= credential_type_size <= 64:
                raise ValueError(
                    "CredentialType deve possuir entre 1 e 64 bytes em "
                    f"depositor.issuers[{issuer_index}].credentialTypes[{type_index}]."
                )

            credential_type_hex = str_to_hex(credential_type)
            key = (address, credential_type_hex)

            if key in seen:
                continue

            seen.add(key)
            credentials.append(
                Credential(
                    issuer=address,
                    credential_type=credential_type_hex,
                )
            )

    if len(credentials) > 10:
        raise ValueError(
            "O PermissionedDomain aceita no máximo 10 combinações de issuer e "
            "CredentialType."
        )

    return credentials


def build_overridden_credentials(
    configured_credentials: list[dict[str, str]],
) -> list[Credential]:
    rules = {"depositor": {"issuers": []}}
    issuers: dict[str, list[str]] = {}

    for item in configured_credentials:
        if not isinstance(item, dict):
            raise ValueError("Cada Credential hardcoded deve ser um objeto.")
        issuer = item.get("issuer")
        credential_type = item.get("credential_type")
        if not isinstance(issuer, str) or not isinstance(credential_type, str):
            raise ValueError(
                "Credentials hardcoded exigem 'issuer' e 'credential_type'."
            )
        issuers.setdefault(issuer, []).append(credential_type)

    for issuer, credential_types in issuers.items():
        rules["depositor"]["issuers"].append(
            {"address": issuer, "credentialTypes": credential_types}
        )

    return build_depositor_credentials(rules)


def find_created_domain(response) -> dict | None:
    for node in response.result["meta"]["AffectedNodes"]:
        created = node.get("CreatedNode")
        if created and created["LedgerEntryType"] == "PermissionedDomain":
            return {
                "domain_id": created["LedgerIndex"],
                "fields": created["NewFields"],
            }

    return None


def main() -> None:
    state = load_json(STATE_FILE) if STATE_FILE.exists() else {}

    if "permissioned_domain" in state:
        print("PermissionedDomain já existe:")
        print(state["permissioned_domain"]["domain_id"])
        return

    if ACCEPTED_CREDENTIALS_OVERRIDE is not None:
        accepted_credentials = build_overridden_credentials(
            ACCEPTED_CREDENTIALS_OVERRIDE
        )
    else:
        accepted_credentials = build_depositor_credentials(load_json(RULES_FILE))

    json_rpc_url = JSON_RPC_URL_OVERRIDE or os.getenv("LENDING_DEVNET_JSON_RPC_URL")
    loan_broker_seed = LOAN_BROKER_SEED_OVERRIDE or os.getenv("LOAN_BROKER_SEED")

    if not json_rpc_url:
        raise ValueError("LENDING_DEVNET_JSON_RPC_URL não está definido.")
    if not loan_broker_seed:
        raise ValueError("LOAN_BROKER_SEED não está definido.")

    loan_broker_wallet = Wallet.from_seed(loan_broker_seed)
    client = JsonRpcClient(json_rpc_url)

    transaction = PermissionedDomainSet(
        account=loan_broker_wallet.address,
        accepted_credentials=accepted_credentials,
    )

    response = submit_and_wait(
        transaction=transaction,
        client=client,
        wallet=loan_broker_wallet,
    )

    transaction_result = response.result["meta"]["TransactionResult"]
    if transaction_result != "tesSUCCESS":
        raise RuntimeError(
            f"PermissionedDomainSet falhou com resultado {transaction_result}."
        )

    domain = find_created_domain(response)
    if domain is None:
        raise RuntimeError("PermissionedDomain não encontrado nos metadados.")

    state["permissioned_domain"] = {
        **domain,
        "tx_hash": response.result["hash"],
    }
    save_state(state)

    print("PermissionedDomain criado:")
    print(domain["domain_id"])
    print("Tx hash:")
    print(response.result["hash"])


if __name__ == "__main__":
    main()

import json
import os
from pathlib import Path

from xrpl.clients import JsonRpcClient
from xrpl.models.currencies import XRP
from xrpl.models.transactions import VaultCreate
from xrpl.transaction import submit_and_wait
from xrpl.wallet import Wallet
from dotenv import load_dotenv
load_dotenv()

JSON_RPC_URL = os.getenv("LENDING_DEVNET_JSON_RPC_URL")
LOAN_BROKER_SEED = "sEdS82yBLdFhZSUNiiDHFZoWTNdcShA"

STATE_FILE = Path(os.getenv("STATE_FILE_PATH"))

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

    if "vault" in state:
        print("Vault já existe:")
        print(state["vault"]["vault_id"])
        return

    loan_broker_wallet = Wallet.from_seed(LOAN_BROKER_SEED)

    state["loan_broker"] = {
        "address": loan_broker_wallet.address,
        "seed": LOAN_BROKER_SEED
    }

    save_state(state)

    print("Loan broker:")
    print(loan_broker_wallet.address)

    tx = VaultCreate(
        account=loan_broker_wallet.address,
        asset=XRP(),
        assets_maximum="1000000000",
        withdrawal_policy=1,
        fee="200000"
    )

    response = submit_and_wait(
        tx,
        client,
        loan_broker_wallet,
        check_fee=False
    )

    vault = find_created_ledger_entry(response, "Vault")

    state = load_state()
    state["vault"] = {
        "vault_id": vault["id"],
        "fields": vault["fields"],
        "tx_hash": response.result["hash"]
    }

    save_state(state)

    print("Vault criado:")
    print(vault["id"])
    print("Tx hash:")
    print(response.result["hash"])


if __name__ == "__main__":
    main()
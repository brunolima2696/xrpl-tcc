import json
import os
from pathlib import Path

from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import LoanBrokerSet
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

    if "loan_broker_object" in state:
        print("LoanBroker já existe:")
        print(state["loan_broker_object"]["loan_broker_id"])
        return

    loan_broker_wallet = Wallet.from_seed(LOAN_BROKER_SEED)

    state["loan_broker"] = {
        "address": loan_broker_wallet.address,
        "seed": LOAN_BROKER_SEED
    }

    save_state(state)

    vault_id = state["vault"]["vault_id"]

    print("Loan broker:")
    print(loan_broker_wallet.address)

    print("VaultID:")
    print(vault_id)

    tx = LoanBrokerSet(
        account=loan_broker_wallet.address,
        vault_id=vault_id,
        management_fee_rate=0,
        cover_rate_minimum=0,
        cover_rate_liquidation=0
    )

    response = submit_and_wait(
        tx,
        client,
        loan_broker_wallet
    )

    loan_broker = find_created_ledger_entry(response, "LoanBroker")

    state["loan_broker_object"] = {
        "loan_broker_id": loan_broker["id"],
        "fields": loan_broker["fields"],
        "tx_hash": response.result["hash"]
    }

    save_state(state)

    print("LoanBroker criado:")
    print(loan_broker["id"])
    print("Tx hash:")
    print(response.result["hash"])


if __name__ == "__main__":
    main()
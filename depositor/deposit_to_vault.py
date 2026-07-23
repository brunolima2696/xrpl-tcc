import json
import os
from pathlib import Path

from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import VaultDeposit
from xrpl.transaction import submit_and_wait
from xrpl.wallet import Wallet


load_dotenv()

JSON_RPC_URL = os.getenv("LENDING_DEVNET_JSON_RPC_URL")
STATE_FILE = Path(os.getenv("STATE_FILE_PATH"))

DEPOSITOR_SEED = os.getenv("DEPOSITOR_SEED")
DEPOSIT_AMOUNT_DROPS = "50000000"

client = JsonRpcClient(JSON_RPC_URL)


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def main():
    state = load_state()

    depositor_wallet = Wallet.from_seed(DEPOSITOR_SEED)

    vault_id = state["vault"]["vault_id"]

    print("Depositor:")
    print(depositor_wallet.address)

    print("VaultID:")
    print(vault_id)

    print("Deposit amount:")
    print(DEPOSIT_AMOUNT_DROPS)

    tx = VaultDeposit(
        account=depositor_wallet.address,
        vault_id=vault_id,
        amount=DEPOSIT_AMOUNT_DROPS
    )

    response = submit_and_wait(
        tx,
        client,
        depositor_wallet
    )

    state["depositor"] = {
        "address": depositor_wallet.address,
        "seed": DEPOSITOR_SEED
    }

    state["vault_deposit"] = {
        "amount": DEPOSIT_AMOUNT_DROPS,
        "tx_hash": response.result["hash"],
        "result": response.result["meta"]["TransactionResult"]
    }

    save_state(state)

    print("VaultDeposit result:")
    print(response.result["meta"]["TransactionResult"])

    print("Tx hash:")
    print(response.result["hash"])


if __name__ == "__main__":
    main()
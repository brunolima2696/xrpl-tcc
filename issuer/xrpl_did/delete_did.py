# neccasary imports
from xrpl.models import DIDDelete
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait
from dotenv import load_dotenv
import os
load_dotenv()

# connect to the xrpl via a client
print("Connecting to client")
JSON_RPC_URL = os.getenv("JSON_RPC_URL")
client = JsonRpcClient(JSON_RPC_URL)
print("connected!")

# Issuer
ISSUER_SEED = os.getenv("ISSUER_SEED")
ISSUER_ADDRESS = os.getenv("ISSUER_ADDRESS")
ISSUER_WALLET = Wallet.from_seed(ISSUER_SEED)

did_delete_txn = DIDDelete(account=ISSUER_ADDRESS)

# sign, submit the did delete transaction and wait for result
print("signed and submitting did delete transaction. awaiting response...")
did_delete_response = submit_and_wait(
    transaction=did_delete_txn,
    wallet=ISSUER_WALLET,
    client=client,
)

# Parse response for result
did_delete_result = did_delete_response.result

# Print result and transaction hash
print(did_delete_result["meta"]["TransactionResult"])
print(did_delete_result["hash"])
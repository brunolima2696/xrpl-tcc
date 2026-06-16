# neccasary imports
from xrpl.models import DIDDelete
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait


# connect to the xrpl via a client
print("Connecting to client")
JSON_RPC_URL = "https://s.altnet.rippletest.net:51234/"
client = JsonRpcClient(JSON_RPC_URL)
print("connected!")


# input the seed that was generated from running the did_set.py
seed = "sEdTZHgVTQrHJJNRiytkst15mXH6jQM"

# restore an account that has an existing DID
wallet = Wallet.from_seed(seed=seed)

# define the account DIDDelete transaction
did_delete_txn = DIDDelete(account=wallet.address)

# sign, submit the did delete transaction and wait for result
print("signed and submitting did delete transaction. awaiting response...")
did_delete_response = submit_and_wait(
    transaction=did_delete_txn,
    wallet=wallet,
    client=client,
)

# Parse response for result
did_delete_result = did_delete_response.result

# Print result and transaction hash
print(did_delete_result["meta"]["TransactionResult"])
print(did_delete_result["hash"])

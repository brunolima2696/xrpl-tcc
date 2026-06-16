# This allows you to create or update a DID
from xrpl.models import CredentialAccept
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait
from xrpl.utils import str_to_hex
from dotenv import load_dotenv
import os
load_dotenv()

# connect to the xrpl via a client
print("Connecting to client")
JSON_RPC_URL = os.getenv("JSON_RPC_URL")
client = JsonRpcClient(JSON_RPC_URL)
print("connected!")

# HOLDER
HOLDER_SEED = os.getenv("HOLDER_SEED")
HOLDER_WALLET = Wallet.from_seed(seed=HOLDER_SEED)
HOLDER_ADRESS = HOLDER_WALLET.address

# Issuer
ISSUER_ADDRESS = os.getenv("ISSUER_ADDRESS")

# XRPL Credential Type
credential_type = "XRPLDegree"

# Credential Accept transaction
credential_accept_tx = CredentialAccept(
    account=HOLDER_ADRESS, # holder da credencial
    issuer=ISSUER_ADDRESS, # issuer da credencial
    credential_type=str_to_hex(credential_type) # tipo da credencial
)

# Sign, submit and wait for response
credential_accept_tx_response = submit_and_wait(
    transaction=credential_accept_tx,
    client=client,
    wallet=HOLDER_WALLET
)

credential_accept_tx_result = credential_accept_tx_response.result

print(f"Transaction result: {credential_accept_tx_result["meta"]["TransactionResult"]}")
print(f"Hash: {credential_accept_tx_result["hash"]}")
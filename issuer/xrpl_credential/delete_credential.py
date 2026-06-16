from xrpl.models import CredentialDelete
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

# Issuer
ISSUER_SEED = os.getenv("ISSUER_SEED")
ISSUER_WALLET = Wallet.from_seed(seed=ISSUER_SEED)
ISSUER_ADDRESS = ISSUER_WALLET.address

# Holder
HOLDER_ADDRESS = os.getenv("HOLDER_ADDRESS")

# Credential type for deletion
credential_type = "XRPLDegree"

# Credential Delete transaction | Holder ou Issuer podem deletar
credential_delete_tx = CredentialDelete(
    account=HOLDER_ADDRESS, # Conta que envia a transaction
    issuer=ISSUER_ADDRESS, # issuer da credencial
    credential_type=str_to_hex(credential_type) # tipo da credencial
)

# Sign, submit and wait for response
credential_delete_tx_response = submit_and_wait(
    transaction=credential_delete_tx,
    client=client,
    wallet=ISSUER_WALLET
)

credential_delete_tx_result = credential_delete_tx_response.result

print(credential_delete_tx_result["meta"]["TransactionResult"])
print(credential_delete_tx_result["hash"])
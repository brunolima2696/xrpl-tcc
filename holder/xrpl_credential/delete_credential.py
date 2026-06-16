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

# Holder Wallet
HOLDER_SEED = os.getenv("HOLDER_SEED")
HOLDER_WALLET = Wallet.from_seed(seed=HOLDER_SEED)
HOLDER_ADDRESS = HOLDER_WALLET.address

# Issuer Address
ISSUER_ADDRESS = os.getenv("ISSUER_ADDRESS")

# Credential type for deletion
credential_type = "XRPLDegree"

# Credential Delete transaction | Holder ou Issuer podem deletar
credential_delete_tx = CredentialDelete(
    account=ISSUER_ADDRESS, # Conta que envia a transaction
    issuer=ISSUER_ADDRESS, # Issuer da credencial
    credential_type=str_to_hex(credential_type) # tipo da credencial
)

# Sign, submit and wait for response
credential_delete_tx_response = submit_and_wait(
    transaction=credential_delete_tx,
    client=client,
    wallet=HOLDER_WALLET
)

credential_delete_tx_result = credential_delete_tx_response.result

print(credential_delete_tx_result["meta"]["TransactionResult"])
print(credential_delete_tx_result["hash"])
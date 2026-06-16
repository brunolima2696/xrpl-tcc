# This allows you to create or update a DID
import json
from xrpl.models import CredentialCreate
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait
from xrpl.utils import str_to_hex
from utils.get_cid_from_logfile import get_cid_from_logfile
import os
from dotenv import load_dotenv
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

# Holder
HOLDER_ADDRESS = os.getenv("HOLDER_ADDRESS")

# Credential JSON Document Fields
file_name = "diploma_verifiable_credential.json"
cid = get_cid_from_logfile(file_name=file_name)

# Credential XPRL Fields
credential_type = "XRPLDegree"
uri = "ipfs://" + cid + "/" + file_name

# Credential Create transaction
credential_create_tx = CredentialCreate(
    account=ISSUER_ADDRESS, # issuer da credencial
    subject=HOLDER_ADDRESS, # holder da credencial
    credential_type=str_to_hex(credential_type), # tipo da credencial
    uri=str_to_hex(json.dumps(uri, ensure_ascii=False, separators=(",", ":")))   
)

# Sign, submit and wait for response
credential_create_tx_response = submit_and_wait(
    transaction=credential_create_tx,
    client=client,
    wallet=ISSUER_WALLET
)

credential_create_tx_result = credential_create_tx_response.result

print(f"Transaction result: {credential_create_tx_result["meta"]["TransactionResult"]}")
print(f"Hash: {credential_create_tx_result["hash"]}")
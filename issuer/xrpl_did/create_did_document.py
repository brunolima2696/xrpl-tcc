# This allows you to create or update a DID
import json
from utils.get_cid_from_logfile import get_cid_from_logfile
from xrpl.models import DIDSet
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
ISSUER_WALLET = Wallet.from_seed(ISSUER_SEED)
ISSUER_ADDRESS = ISSUER_WALLET.address

# DID JSON Document
file_name = "issuer_did.json"
cid = get_cid_from_logfile(file_name)

# DID XRPL Object Fields 
document = {    
    }

data = {    
    }

# uri = "ipfs://" + cid + "/" + file_name
uri = "string generica 123"

# DID SET transaction
did_set_txn = DIDSet(
    account=ISSUER_ADDRESS,
    did_document=str_to_hex(json.dumps(document, ensure_ascii=False, separators=(",", ":"))),
    data=str_to_hex(json.dumps(data, ensure_ascii=False, separators=(",", ":"))),
    uri=str_to_hex(uri),
)

# sign, submit the transaction and wait for the response
print("signing and submitting the transaction, awaiting a response \n")
did_set_txn_response = submit_and_wait(
    transaction=did_set_txn,
    client=client, 
    wallet=ISSUER_WALLET
)

# Parse response for result
did_set_txn_result = did_set_txn_response.result

# Print result and transaction hash
print(f"Transaction result: {did_set_txn_result["meta"]["TransactionResult"]}")
print(f"Hash: {did_set_txn_result["hash"]}")
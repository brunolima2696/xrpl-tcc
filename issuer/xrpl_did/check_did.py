from xrpl.models import LedgerEntry
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from dotenv import load_dotenv
import json
import os
load_dotenv()

# connect to the xrpl via a client
print("Connecting to client")
JSON_RPC_URL = os.getenv("JSON_RPC_URL")
client = JsonRpcClient(JSON_RPC_URL)
print("connected!")

# Issuer Address
issuer_address = os.getenv("ISSUER_ADDRESS")

# build the request for the account's DID
req = LedgerEntry(ledger_index="validated", did=issuer_address)

# submit request and awaiting result
print("submitting request \n")
response = client.request(req)
result = response.result

# parse result
if "index" in result and "Account" in result["node"]:
    print(f'DID index: {result["node"]["index"]}')
    # print(f'DID Document HEX: {result["node"]["DIDDocument"]}')
    did_document = bytes.fromhex(result["node"]["DIDDocument"]).decode("utf-8")
    print(f'DID Document: {json.dumps(json.loads(did_document), indent=2, ensure_ascii=False, sort_keys=True)}')
    # print(f'Data: {result["node"]["Data"]}')
    did_data = bytes.fromhex(result["node"]["Data"]).decode("utf-8")
    print(f'DID Data: {json.dumps(json.loads(did_data), indent=2, ensure_ascii=False, sort_keys=True)}')
    # print(f'URI: {result["node"]["URI"]}')
    did_uri = bytes.fromhex(result["node"]["URI"]).decode("utf-8")
    print(f'Did URI: {did_uri}')

else:
    print("No DID found for this account")

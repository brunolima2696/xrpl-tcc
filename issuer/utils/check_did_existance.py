from xrpl.clients import JsonRpcClient
from xrpl.models import LedgerEntry
import re

def is_valid_ipfs_format(uri=str):
    pattern = r"^ipfs://[^/]+/[^/]+$"
    return re.match(pattern,uri) is not None

def check_did_existance(client=JsonRpcClient, address= str):
    req = LedgerEntry(ledger_index="validated", did= address)
    response = client.request(req)
    result = response.result
    if not ("index" in result and "Account" in result["node"]):
        print(f"No DID Object set for account: {address}")
        return False
    if not ("URI" in result["node"] and is_valid_ipfs_format(bytes.fromhex(result["node"]["URI"]).decode("utf-8"))):
        print("No URI or does not contain valid IPFS format: ")
        return False
    
    return True

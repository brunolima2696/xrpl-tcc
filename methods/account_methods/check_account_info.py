import os
from xrpl.clients import JsonRpcClient
from xrpl.wallet import generate_faucet_wallet
from xrpl.core import addresscodec
from xrpl.models.requests.account_info import AccountInfo
import json


JSON_RPC_URL = "https://s.altnet.rippletest.net:51234/"
client = JsonRpcClient(JSON_RPC_URL)

test_account = ''

# Look up info about your account
print("\nGetting account info...")
acct_info = AccountInfo(
    account=test_account,
    ledger_index="validated",
    strict=True,
)

response = client.request(acct_info)
result = response.result
print("Response Status: ", response.status)
print(json.dumps(response.result, indent=4, sort_keys=True))
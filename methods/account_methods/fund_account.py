import os
from xrpl.clients import JsonRpcClient
from xrpl.wallet import generate_faucet_wallet
import xrpl.wallet
from xrpl.core import addresscodec
from xrpl.models.requests.account_info import AccountInfo
import json

JSON_RPC_URL = "https://s.altnet.rippletest.net:51234/"
client = JsonRpcClient(JSON_RPC_URL)

seed = ""

# Create or Fund wallet using the Testnet faucet:
# https://xrpl.org/xrp-testnet-faucet.html
print("\nFunding with Testnet XRP...")
wallet = xrpl.wallet.Wallet.from_seed(seed=seed)
test_wallet = xrpl.wallet.generate_faucet_wallet(client=client, wallet=wallet, debug=True)
test_account = test_wallet.classic_address

print(f"Wallet: {test_account}")
print(f"Account Testnet Explorer URL: ")
print(f" https://testnet.xrpl.org/accounts/{test_account}")
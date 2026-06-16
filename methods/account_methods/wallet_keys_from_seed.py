import xrpl 

seed = ""

# Wallet from seed
wallet = xrpl.wallet.Wallet.from_seed(seed=seed)

# Keys from wallet
print("private key:", wallet.private_key)
print("public key:", wallet.public_key)
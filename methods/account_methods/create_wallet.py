import xrpl

keypair = xrpl.wallet.Wallet.create()

print("seed:", keypair.seed)
print("classic address:", keypair.address)
print("private key:", keypair.private_key)
print("public key:", keypair.public_key)
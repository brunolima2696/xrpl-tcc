from xrpl.clients import JsonRpcClient
from xrpl.models.requests import LedgerEntry

credential_index = "A86D024DEC8C22CC42FCB32DC504B2166CDE014E67035C3E9E8E0F3B16C3498A"

client = JsonRpcClient("https://s.altnet.rippletest.net:51234")
req = LedgerEntry(index=credential_index)
resp = client.request(req)

credential = resp.result["node"]  

print("Issuer :", credential["Issuer"])
print("Subject :", credential["Subject"])
print("Flags :", credential["Flags"])
print("Index :", credential["index"])
print("Type:", bytes.fromhex(credential["CredentialType"]).decode('utf-8'))
print("URI :", bytes.fromhex(credential["URI"]).decode('utf-8'))
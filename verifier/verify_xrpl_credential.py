import os
from dotenv import load_dotenv
from utils.load_document import load_document
from utils.verify_xrpl_credential import verify_xrpl_credential
from xrpl.clients import JsonRpcClient
load_dotenv()

JSON_RPC_URL = os.getenv("JSON_RPC_URL")
client = JsonRpcClient(JSON_RPC_URL)

vp_path = "holder/documents/diploma_verifiable_presentation.json"

vp = load_document(vp_path)

try:
    credential = verify_xrpl_credential(vp=vp, client=client)

    # Print credential
    print("\nIssuer :", credential["Issuer"])
    print("Subject :", credential["Subject"])
    print("Flags :", credential["Flags"])
    print("Index :", credential["index"])
    print("Type:", bytes.fromhex(credential["CredentialType"]).decode('utf-8'))
    print("URI :", bytes.fromhex(credential["URI"]).decode('utf-8'))
    
except Exception as e:
    print(f"{e}")
import os
from dotenv import load_dotenv
from utils.load_document import load_document
from utils.verify_signature import verify_signature
from xrpl.clients import JsonRpcClient
load_dotenv()

JSON_RPC_URL = os.getenv("JSON_RPC_URL")
client = JsonRpcClient(JSON_RPC_URL)

vc_path = "issuer/documents/diploma_verifiable_credential.json"

vc = load_document(vc_path)

try:
    verify_signature(document=vc, client=client)
except Exception as e:
    print(f"{e}")
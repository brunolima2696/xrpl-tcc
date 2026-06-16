import os
from dotenv import load_dotenv
from utils.load_document import load_document
from utils.verify_signature import verify_signature
from xrpl.clients import JsonRpcClient
load_dotenv()

JSON_RPC_URL = os.getenv("JSON_RPC_URL")
client = JsonRpcClient(JSON_RPC_URL)

vp_path = "holder/documents/diploma_verifiable_presentation.json"

vp = load_document(vp_path)

try:
    verify_signature(document=vp, client=client)
except Exception as e:
    print(f"{e}")
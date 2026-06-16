import json
import os
from utils.multibase import base58
from dotenv import load_dotenv
from utils.ipfs_upload import upload_to_ipfs
from schemas.did_schema import *
load_dotenv()

## CRIA DOCUMENTO JSON DID DO HOLDER
## E FAZ UPLOAD PARA O IPFS

# HOLDER
HOLDER_ADDRESS = os.getenv("HOLDER_ADDRESS")
HOLDER_PUBLIC_KEY = os.getenv("HOLDER_PUBLIC_KEY")

# DID Document
did_document = DIDDocumentSchema()

did_document.context = "https://www.w3.org/TR/did-1.1/#did-documents"
did_document.id = f"did:xrpl:2:{HOLDER_ADDRESS}"

did_document.verificationMethod.append(
    VerificationMethodSchema(
        id="#key-1",
        type="Ed25519VerificationKey",
        publicKey=base58(HOLDER_PUBLIC_KEY)
    )
)


# Document JSON Creation
document_path = "holder/documents/"
document_name = "holder_did.json"

print("Creating JSON file")
with open(document_path + document_name,"w",encoding="utf-8") as f:
    json.dump(did_document.model_dump(by_alias=True), f, indent=4, ensure_ascii=False)

# Document IPFS Upload
upload_to_ipfs(document_path, document_name)
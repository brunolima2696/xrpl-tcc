import os
import json
from utils.multibase import base58
from utils.ipfs_upload import upload_to_ipfs
from schemas.did_schema import *
from dotenv import load_dotenv
load_dotenv()

## CRIA DOCUMENTO JSON DID DO ISSUER
## E FAZ UPLOAD PARA O IPFS

# Issuer
ISSUER_ADDRESS = os.getenv("ISSUER_ADDRESS")
ISSUER_PUBLIC_KEY = os.getenv("ISSUER_PUBLIC_KEY")

# DID Document
did_document = DIDDocumentSchema()

did_document.context = "https://www.w3.org/TR/did-1.1/#did-documents"
did_document.id = f"did:xrpl:2:{ISSUER_ADDRESS}"

did_document.verificationMethod.append(
    VerificationMethodSchema(
        id="#key-1",
        type="Ed25519VerificationKey",
        publicKey=base58(ISSUER_PUBLIC_KEY)
    )
)

did_document.service.append(
    ServiceSchema(
        id="#issuer",
        type="CredentialIssuer",
        serviceEndpoint="https://issuer.universidade.br/credentials"
    )
)

# Document JSON Creation
document_path = "issuer/documents/"
document_name = "issuer_did.json"

print("Creating JSON file")
with open(document_path + document_name,"w",encoding="utf-8") as f:
    json.dump(did_document.model_dump(by_alias=True), f, indent=4, ensure_ascii=False)

# Document IPFS Upload
upload_to_ipfs(document_path, document_name)
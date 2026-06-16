import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from xrpl.clients import JsonRpcClient
from schemas.verifiable_credential_schema import *
from utils.jws import jws
from utils.ipfs_upload import upload_to_ipfs
from utils.check_did_existance import check_did_existance
from dotenv import load_dotenv
load_dotenv()

## CRIA DOCUMENTO JSON DA VC
## E FAZ UPLOAD PARA O IPFS

#  Issuer
ISSUER_ADDRESS = os.getenv("ISSUER_ADDRESS")
ISSUER_PRIVATE_KEY = os.getenv("ISSUER_PRIVATE_KEY")

# Holder
HOLDER_ADDRESS = os.getenv("HOLDER_ADDRESS")

# Check Holder and Issuer DID existance in XRPL Ledger
print("Connecting to client")
JSON_RPC_URL = os.getenv("JSON_RPC_URL")
client = JsonRpcClient(JSON_RPC_URL)
print("connected!")

if not (check_did_existance(client=client, address=ISSUER_ADDRESS) and check_did_existance(client=client,address=HOLDER_ADDRESS)):
    print("Cannot create Verifiable Credential")
else:

    # Verifiable Credential
    verifiable_credential = VerifiableCredentialSchema()

    verifiable_credential.context = "https://www.w3.org/TR/vc-data-model-2.0/#verifiable-credentials"
    verifiable_credential.type = ["VerifiableCredential", "UniversityDegreeVC"]
    verifiable_credential.issuer = f"did:xrpl:2:{ISSUER_ADDRESS}"

    verifiable_credential.credentialSubject = CredentialSubjectSchema(
        id=f"did:xrpl:2:{HOLDER_ADDRESS}",
        name='Nome Aluno',
        degree={
            "type": "Example Degree",
            "name": "Bachelor of Engineering"
        },
        alumniOf = {
            "name": "University Name"
        },
        studendId="123456789"
    )

    verifiable_credential.evidence.append(
        EvidenceSchema(
            id="ipfs://CID_DO_PDF_DO_DIPLOMA/diploma.pdf",
            type=["Evidence"],
            name="Diploma (PDF)",
            description="Arquivo PDF do diploma emitido pela universidade."
        )
    )

    verifiable_credential = verifiable_credential.model_dump(by_alias=True, exclude={"proof"})

    proof = ProofSchema(
        type="Ed25519Signature",
        created=datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(),
        proofPurpose="authentication",
        verificationMethod=f"did:xrpl:2:{ISSUER_ADDRESS}#key-1",
        jws = jws(verifiable_credential, ISSUER_PRIVATE_KEY)
    )

    proof = proof.model_dump()

    verifiable_credential["proof"] = proof

    # Document JSON Creation
    document_path = "issuer/documents/"
    document_name = "diploma_verifiable_credential.json"

    print("Creating Verifiable Credential...")

    try:
        with open(document_path + document_name,"w",encoding="utf-8") as f:
            json.dump(verifiable_credential, f, indent=4, ensure_ascii=False)
        print("Verifiable Credential created")
    except OSError as e:
        print(f"Failed to create file: {e}")

    # Document IPFS Upload
    upload_to_ipfs(document_path, document_name)
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from schemas.verifiable_presentation_schema import *
from utils.credential_index_calculator import calculate_credential_index
from utils.jws import jws
from dotenv import load_dotenv
load_dotenv()

## CRIA DOCUMENTO JSON DA VP

# HOLDER
HOLDER_ADDRESS = os.getenv("HOLDER_ADDRESS")
HOLDER_PRIVATE_KEY = os.getenv("HOLDER_PRIVATE_KEY")

# ISSUER
ISSUER_ADDRESS = os.getenv("ISSUER_ADDRESS")

# Verifiable Presentation

verifiable_presentation = VerifiablePresentationSchema()

verifiable_presentation.context = "https://www.w3.org/TR/vc-data-model-2.0/#verifiable-presentations"
verifiable_presentation.type = ["VerifiablePresentation", "UniversityDegreeVP"]
verifiable_presentation.holder = f"did:xrpl:2:{HOLDER_ADDRESS}"

xrpl_credential_type = "XRPLDegree"
xrpl_credential_index = calculate_credential_index(HOLDER_ADDRESS, ISSUER_ADDRESS, xrpl_credential_type)

xrplCredentialRef = XrplCredentialRefSchema(
    network_id= '2',
    issuer= ISSUER_ADDRESS,            
    subject= HOLDER_ADDRESS,         
    credential_type= xrpl_credential_type,
    index= xrpl_credential_index
)

verifiable_presentation.verifiableCredential = VerifiableCredentialSchema(
    context="https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/credential",
    type=["XRPLCredential","XRPLDegreeCredential"],
    issuer=f"did:xrpl:2:{ISSUER_ADDRESS}"
)

verifiable_presentation.verifiableCredential.credentialRef.append(xrplCredentialRef)

verifiable_presentation = verifiable_presentation.model_dump(by_alias=True, exclude={"proof"})

proof = ProofSchema(
        type="Ed25519Signature",
        created=datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(),
        proofPurpose="authentication",
        verificationMethod=f"did:xrpl:2:{HOLDER_ADDRESS}#key-1",
        jws=jws(verifiable_presentation, HOLDER_PRIVATE_KEY)
    )

proof = proof.model_dump()

verifiable_presentation["proof"] = proof

# DOCUMENT JSON CREATION
document_path = "holder/documents/"
document_name = "diploma_verifiable_presentation.json"

print("Creating Verifiable Presentation...")
try:
    with open(document_path + document_name,"w",encoding="utf-8") as f:
        json.dump(verifiable_presentation, f, indent=4, ensure_ascii=False)
    print("Verifiable Presentation created.")
except OSError as e:
    print(f"Failed to create file: {e}")
from typing import List
from pydantic import BaseModel, Field, ConfigDict

class ProofSchema(BaseModel):
    type: str = ""
    created: str = ""
    proofPurpose: str = ""
    verificationMethod: str = ""
    jws: str = ""

class XrplCredentialRefSchema (BaseModel):
    credential_ref_type: str = 'XRPLCredential'
    network_id: str = ''
    issuer: str = ''
    subject: str = ''
    credential_type: str = ''
    index: str = ''

class VerifiableCredentialSchema (BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        validate_by_alias=True
    )
    context: str = Field(default='', alias='@context')
    type: List[str] = Field(default_factory=list)
    issuer: str = ''
    credentialRef: List = Field(default_factory=list)

class VerifiablePresentationSchema (BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        validate_by_alias=True
    )
    context: str = Field(default='', alias='@context')
    type: List[str] = Field(default_factory=list)
    holder: str = ''
    verifiableCredential: VerifiableCredentialSchema = Field(default_factory=VerifiableCredentialSchema)
    proof: ProofSchema = Field(default_factory=ProofSchema)
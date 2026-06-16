from typing import List
from pydantic import BaseModel, Field, ConfigDict


class CredentialSubjectSchema(BaseModel):
    id: str = ""
    name: str = ""
    degree: dict = Field(default_factory=dict)
    alumniOf: dict = Field(default_factory=dict)
    studendId: str = ""


class EvidenceSchema(BaseModel):
    id: str = ""
    type: List[str] = Field(default_factory=list)
    name: str = ""
    description: str = ""


class ProofSchema(BaseModel):
    type: str = ""
    created: str = ""
    proofPurpose: str = ""
    verificationMethod: str = ""
    jws: str = ""


class VerifiableCredentialSchema(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        validate_by_alias=True
    )

    context: str = Field(default="", alias='@context')
    type: List[str] = Field(default_factory=list)
    issuer: str = ""
    credentialSubject: CredentialSubjectSchema = Field(default_factory=CredentialSubjectSchema)
    evidence: List[EvidenceSchema] = Field(default_factory=list)
    proof: ProofSchema = Field(default_factory=ProofSchema)
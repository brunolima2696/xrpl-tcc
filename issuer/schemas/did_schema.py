from typing import List
from pydantic import BaseModel, Field, ConfigDict

class VerificationMethodSchema(BaseModel):
    id: str = ""
    type: str = ""
    publicKey: str = ""

class ServiceSchema(BaseModel):
    id: str = ""
    type: str = ""
    serviceEndpoint: str = ""

class DIDDocumentSchema(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        validate_by_alias=True
    )

    context: str = Field(default="", alias='@context')
    id: str = ""
    verificationMethod: List[VerificationMethodSchema] = Field(default_factory=list)
    service: List[ServiceSchema] = Field(default_factory=list)
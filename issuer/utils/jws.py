import json
import base64
from nacl.signing import SigningKey  # Ed25519
from nacl.encoding import RawEncoder

def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def jws(vp:dict,pkey:str):

    vp_payload = json.dumps(
        vp,
        separators=(",",":"),
        sort_keys=True
    ).encode("utf-8")

    jws_header={
        "alg": "EdDSA",
        "typ": "JWT"
    }

    header_bytes = json.dumps(
        jws_header,
        separators=(",", ":"),
        sort_keys=True
    ).encode("utf-8")

    header_b64 = b64url(header_bytes)
    payload_b64 = b64url(vp_payload)

    pkey = bytes.fromhex(pkey)[1:]

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signing_key = SigningKey(pkey, encoder=RawEncoder)
    signature = signing_key.sign(signing_input).signature
    signature_b64 = b64url(signature)

    jws = f"{header_b64}.{payload_b64}.{signature_b64}"

    return jws
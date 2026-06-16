import hashlib
from xrpl.core.addresscodec import decode_classic_address

def sha512half(data: bytes) -> str:
    return hashlib.sha512(data).digest()[:32].hex().upper()

def calculate_credential_index(
    subject_address: str,
    issuer_address: str,
    credential_type: str,
) -> str:
    credential_space_key = bytes.fromhex("0044")
    subject_bytes = decode_classic_address(subject_address)
    issuer_bytes = decode_classic_address(issuer_address)
    credential_type_bytes = credential_type.encode("utf-8")

    payload = (
        credential_space_key
        + subject_bytes
        + issuer_bytes
        + credential_type_bytes
    )

    return sha512half(payload)
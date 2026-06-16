import base64
import json
from .resolve_did import get_public_key_from_did
from nacl.signing import VerifyKey
from nacl.encoding import RawEncoder
from xrpl.clients import JsonRpcClient


def b64url_decode(s: str) -> bytes:
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)


def verify_signature(document: dict, client: JsonRpcClient) -> None:
    
    proof = document.get("proof")
    if not proof:
        raise ValueError("document não possui campo 'proof'")

    jws = proof.get("jws")
    vm_id = proof.get("verificationMethod")

    if not jws or not vm_id:
        raise ValueError("Proof sem jws ou verificationMethod")

    # Decompor JWS
    try:
        header_b64, payload_b64, sig_b64 = jws.split(".")
    except ValueError:
        raise ValueError("JWS incorreto")

    # validar header.alg == "EdDSA"
    header_bytes = b64url_decode(header_b64)
    header = json.loads(header_bytes.decode("utf-8"))
    if header.get("alg") != "EdDSA":
        raise ValueError(f"Algoritmo JWS inesperado: {header.get('alg')}")

    # Recriar document sem proof e serializar
    document_no_proof = dict(document)
    document_no_proof.pop("proof", None)

    document_payload = json.dumps(
        document_no_proof,
        separators=(",", ":"),
        sort_keys=True
    ).encode("utf-8")

    expected_payload_b64 = base64.urlsafe_b64encode(document_payload).rstrip(b"=").decode("ascii")
    if payload_b64 != expected_payload_b64:
        raise ValueError("Payload do JWS não corresponde a document")

    # Resolver DID e obter public key
    if "VerifiableCredential" in document.get("type"):
        did = document.get("issuer")
    elif "VerifiablePresentation" in document.get("type"):    
        did = document.get("holder")
    else:
        raise ValueError("document não possui tipo válido")

    pubkey_bytes = get_public_key_from_did(did, vm_id, client)

    #  Verificar assinatura Ed25519
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = b64url_decode(sig_b64)

    vk = VerifyKey(pubkey_bytes, encoder=RawEncoder)
    try:
        vk.verify(signing_input, signature)
    except Exception as e:
        raise ValueError(f"Assinatura inválida: {e}")
    
    print("Assinatura confirmada.")
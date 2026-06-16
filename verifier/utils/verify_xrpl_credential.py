from xrpl.clients import JsonRpcClient
from xrpl.models.requests import LedgerEntry

LSF_ACCEPTED = 0x00010000

def verify_xrpl_credential(vp: dict, client: JsonRpcClient, require_accepted: bool = True) -> dict:
    
    cred_ref = vp["verifiableCredential"].get("credentialRef")
    if not cred_ref:
        raise ValueError("VP não possui campo credentialRef")

    xrpl_cred = next((cred for cred in cred_ref if cred.get("credential_ref_type") == "XRPLCredential"), None)

    if not xrpl_cred:
        raise ValueError("credentialRef não possui XRPLCredential")

    network_id = xrpl_cred.get("network_id")
    issuer_account = xrpl_cred.get("issuer")
    subject_account = xrpl_cred.get("subject")
    credential_type = xrpl_cred.get("credential_type")
    index = xrpl_cred.get("index")

    if not isinstance(network_id, str):
        raise ValueError(f"network_id inesperado ({network_id})")
    if not issuer_account or not subject_account or not credential_type or not index:
        raise ValueError("xrplCredentialRef incompleto")

    # CredentialType para hex
    credential_type_hex = credential_type.encode("utf-8").hex().upper()

    # Buscar a Credential pelo index
    resp = client.request(LedgerEntry(index=index))
    if resp.status != "success":
        raise RuntimeError(f"Erro ao buscar Credential pelo index: {resp.result}")
    
    node = resp.result.get("node")
    if not node:
        raise RuntimeError("LedgerEntry não retornou campo 'node'")

    if node.get("LedgerEntryType") != "Credential":
        raise ValueError("LedgerEntryType não é 'Credential'")

    # Checar Issuer, Subject, CredentialType
    if node.get("Issuer") != issuer_account:
        raise ValueError("Issuer da Credential no ledger não bate com xrplCredentialRef")
    if node.get("Subject") != subject_account:
        raise ValueError("Subject da Credential no ledger não bate com xrplCredentialRef")
    if node.get("CredentialType") != credential_type_hex:
        raise ValueError("CredentialType da Credential no ledger não bate com credential_type da VP")

    # Checar Flag accepted
    flags = node.get("Flags", 0)
    if require_accepted and not (flags & LSF_ACCEPTED):
        raise ValueError("Credential encontrada, mas não aceita (lsfAccepted)")
    
    print("XRPL Credential confirmada.")

    return node
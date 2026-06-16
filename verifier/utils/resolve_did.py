import base58
import os
import json
import requests
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountObjects
from dotenv import load_dotenv
load_dotenv()

IPFS_API = os.getenv("IPFS_API")
verifier_documents_path = "verifier/documents/"

def resolve_did_object_for_account(account: str, client: JsonRpcClient) -> dict:
    
    resp = client.request(AccountObjects(account=account))
    if resp.status != "success":
        raise RuntimeError(f"Erro ao buscar conta: {resp.result}")
    
    for obj in resp.result.get("account_objects", []):
        if obj.get("LedgerEntryType") == "DID":
            return obj
    raise RuntimeError("Nenhum objeto DID encontrado")


def resolve_did_document_from_ipfs(
    cid: str,
    file_name: str,
    ipfs_api_url = IPFS_API,
) -> dict:
    try:
        response = requests.post(f"{ipfs_api_url}/api/v0/cat", params={"arg": cid})
        response.raise_for_status()

        # salva o JSON do DID
        with open(verifier_documents_path + file_name, "wb") as file:
            file.write(response.content)

        # retorna para leitura
        with open(verifier_documents_path + file_name, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data

    except requests.RequestException as e:
        print(f"Failed to download file from IPFS: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"Downloaded file is not valid JSON: {e}")
        raise
    except OSError as e:
        print(f"File error: {e}")

def get_public_key_from_did(did: str, vm_id: str, client: JsonRpcClient) -> bytes:
    
    # Address a partir de did:xrpl:2:<address>
    parts = did.split(":")
    if len(parts) != 4 or parts[0] != "did" or parts[1] != "xrpl":
        raise ValueError(f"DID inválido: {did}")
    account = parts[-1]
    
    # Buscar ledger object DID da conta
    did_obj = resolve_did_object_for_account(account, client)

    # Campo URI
    did_obj_uri = bytes.fromhex(did_obj["URI"]).decode('utf-8')
    cid = did_obj_uri.split("/")[-2]
    file_name = did_obj_uri.split("/")[-1]

    did_document = resolve_did_document_from_ipfs(cid, file_name)

    vm_list = did_document.get("verificationMethod", [])
    if not vm_list:
        raise ValueError("Nenhum verificationMethod encontrado")

    # vm_id = "did:xrpl:2:<addr>#key-1"
    if "#" in vm_id:
        suffix = "#" + vm_id.split("#", 1)[1]  # "#key-1"
    else:
        suffix = vm_id

    for vm in vm_list:
        if vm.get("id") == suffix:
            pkey_b58 = vm.get("publicKey")[1:]
            if not pkey_b58:
                raise ValueError("verificationMethod encontrado, mas sem pKey")
            pubkey_bytes = base58.b58decode(pkey_b58)
            if len(pubkey_bytes) != 32:
                raise ValueError(f"Public key Ed25519 deve ter 32 bytes, recebi {len(pubkey_bytes)}")
            return pubkey_bytes
    
    raise ValueError(f"verificationMethod {vm_id} não encontrado no Data do DID")
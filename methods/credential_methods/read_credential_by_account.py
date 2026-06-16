from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountObjects, AccountObjectType

lsfAccepted = 0x00010000

account = "rL7oLd4KDXcCfjPcCWpLF7WGATxPG7gcVp"

# connect to the xrpl via a client
print("Connecting to client")
JSON_RPC_URL = "https://s.altnet.rippletest.net:51234/"
client = JsonRpcClient(JSON_RPC_URL)
print("connected!")

class XRPLLookupError(Exception):
    def __init__(self, xrpl_response):
        self.body = xrpl_response.result

def look_up_credentials(client:JsonRpcClient, 
                        issuer:str="", 
                        subject:str="", 
                        accepted:str="both"):
    """
    Looks up Credentials issued by/to a specified XRPL account, optionally
    filtering by accepted status. Handles pagination.
    """
    account = issuer or subject # Use whichever is specified, issuer if both
    if not account:
        raise ValueError("Must specify issuer or subject")
    
    accepted = accepted.lower()
    if accepted not in ("yes","no","both"):
        raise ValueError("accepted must be str 'yes', 'no', or 'both'")

    credentials = []
    has_more_pages = True
    marker = None
    while has_more_pages:
        xrpl_response = client.request(AccountObjects(
            account=account,
            type=AccountObjectType.CREDENTIAL,
            marker=marker
        ))
        if xrpl_response.status != "success":
            raise XRPLLookupError(xrpl_response)

        for obj in xrpl_response.result["account_objects"]:
            # Skip credentials that aren't issued to/by the requested address.
            if issuer and obj["Issuer"] != issuer:
                continue
            if subject and obj["Subject"] != subject:
                continue
            # Skip credentials that don't match the specified accepted status
            cred_accepted = obj["Flags"] & lsfAccepted
            
            if accepted == "yes" and not cred_accepted:
                continue
            if accepted == "no" and cred_accepted:
                continue
            credentials.append(obj)
        
        marker = xrpl_response.result.get("marker")
        if not marker:
            has_more_pages = False
    return credentials

credentials = look_up_credentials(client=client, issuer=account)

for i, credentials in enumerate(credentials, start=1):
    print(f"--- Credential #{i} ---")
    print("Issuer :", credentials["Issuer"])
    print("Subject :", credentials["Subject"])
    print("Flags :", credentials["Flags"])
    print("Index :", credentials["index"])
    print("Type:", bytes.fromhex(credentials["CredentialType"]).decode('utf-8'))
    print("URI :", bytes.fromhex(credentials["URI"]).decode('utf-8'))
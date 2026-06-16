import json
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import os
load_dotenv()

IPFS_API = os.getenv("IPFS_API")

# File to be uploaded
file_path = ""
file_name = ""

# File to record upload logs/CIDs
log_path = "ipfs/logs/"
log_file = "logfile.jsonl"

# Upload (add) com pin=true 
with open(file_path + file_name, "rb") as f:
    r = requests.post(
        f"{IPFS_API}/api/v0/add",
        params={"pin": "true", "preserve-mtime": "true"},
        files={"file": f}
    )

r.raise_for_status()

# IPFS response data
data = r.json()

data_name = data["Name"]
data_CID = data["Hash"]
data_size = data["Size"]
data_added_at = datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat()

# Saving data content to logfile
log_file_content = {
    "name": data_name,
    "CID": data_CID,
    "size": data_size,
    "added_at": data_added_at
}

with open(log_path + log_file, "a", encoding="utf-8") as out:
    out.write(json.dumps(log_file_content, ensure_ascii=False) + "\n")


print("Name:", data_name)
print("CID:", data_CID)
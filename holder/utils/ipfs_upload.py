import json
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import os
load_dotenv()

def upload_to_ipfs(file_path: str, file_name: str):
    """
    Uploads file to IPFS and prints the corresponding CID and File Name.
    Also updates local and IPFS logfiles with both values, file size and timestamp.

    :param str file_path: path to the file to be uploaded
    :param str file_name: name of the file to be uploaded

    :return: none

    """
    IPFS_API = os.getenv("IPFS_API")

    # File to be uploaded
    file_path = file_path
    file_name = file_name

    # IPFS logfile location
    ipfs_logfile_path = "ipfs/logs/"
    ipfs_logfile_name = "logfile.jsonl"

    # Local logfile location
    local_logfile_path = "holder/logs/"
    local_logfile_name = "logfile.jsonl"

    print("Uploading to IPFS...")
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

    print("Updating IPFS logfile...")
    with open(ipfs_logfile_path + ipfs_logfile_name, "a", encoding="utf-8") as out:
        out.write(json.dumps(log_file_content, ensure_ascii=False) + "\n")

    print("Updating local logfile...")
    with open(local_logfile_path + local_logfile_name, "a", encoding="utf-8") as out:
        out.write(json.dumps(log_file_content, ensure_ascii=False) + "\n")

    print("Name:", data_name)
    print("CID:", data_CID)
import json
import os
from dotenv import load_dotenv
from pathlib import Path
import requests
load_dotenv()

IPFS_API = os.getenv("IPFS_API")

CID_TO_DOWNLOAD = "QmeTL2AkGopZhzqy3qQYzJVSTtNTy7PXWs8UJtvVMeKpWV"  

CURRENT_DIR = Path(__file__).resolve().parent
LOG_FILE = CURRENT_DIR / "logs/logfile.jsonl"
DOWNLOADS_DIR = CURRENT_DIR / "downloads"

if not LOG_FILE.exists():
    raise RuntimeError(f"Log não encontrado: {LOG_FILE}")
if not DOWNLOADS_DIR.exists():
    raise RuntimeError(f"Pasta downloads não encontrada: {DOWNLOADS_DIR}")

record = None

with LOG_FILE.open("r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if obj.get("CID") == CID_TO_DOWNLOAD:
            record = obj  # fica com o último cid

if not record:
    raise RuntimeError(f"CID não encontrado no log: {CID_TO_DOWNLOAD}")

name = Path(record.get("name", "downloaded_file")).name
out_path = DOWNLOADS_DIR / name  # sobrescreve se existir

with requests.post(
    f"{IPFS_API}/api/v0/cat",
    params={"arg": CID_TO_DOWNLOAD},
    stream=True,
    timeout=120,
) as r:
    r.raise_for_status()
    with out_path.open("wb") as out:
        for chunk in r.iter_content(chunk_size=1024 * 256):
            if chunk:
                out.write(chunk)

print("OK:", out_path)
import json

def get_cid_from_logfile(file_name: str):
    """
    Searches, by file name, for IPFS upload CID from local logfile.

    :param str file_name: Name of the file to be search

    :return CID: CID for corresponding file 
    """


    FILE_NAME = file_name
    LOG_FILE =  "issuer/logs/logfile.jsonl"

    record = None

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if obj.get("name") == FILE_NAME:
                record = obj  

    if not record:
        raise RuntimeError(f"Arquivo não encontrado no log: {FILE_NAME}")

    return record.get("CID")
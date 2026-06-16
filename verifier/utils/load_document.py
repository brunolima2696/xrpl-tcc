import json
from pathlib import Path

def load_document(path: str) -> dict:

    doc_str = Path(path).read_text(encoding="utf-8")
    doc = json.loads(doc_str)

    return doc
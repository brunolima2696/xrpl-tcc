from nacl.signing import SigningKey
from nacl.encoding import RawEncoder
import base58 as b58

def base58(key: str):

    key_bytes = bytes.fromhex(key)[1:]

    key_b58 = b58.b58encode(key_bytes).decode("ascii")  

    return "z" + key_b58
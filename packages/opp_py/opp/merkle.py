from __future__ import annotations
import hashlib
from typing import List

def _h(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()

def merkle_root(chunks: List[bytes]) -> str:
    if not chunks:
        return "sha256:" + hashlib.sha256(b"").hexdigest()
    layer = [ _h(c) for c in chunks ]
    while len(layer) > 1:
        nxt = []
        for i in range(0, len(layer), 2):
            a = layer[i]
            b = layer[i+1] if i+1 < len(layer) else a
            nxt.append(_h(a + b))
        layer = nxt
    return "sha256:" + layer[0].hex()

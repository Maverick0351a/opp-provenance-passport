from __future__ import annotations
import base64, hashlib, json, datetime
from typing import Any

def b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")

def canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def cid_of(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(obj)).hexdigest()

def utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

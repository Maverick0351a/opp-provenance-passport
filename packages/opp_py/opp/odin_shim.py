from __future__ import annotations
import os, base64, json, hashlib, datetime
from typing import Any, Dict, Optional
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
import httpx

__all__ = ["OPEClient"]

def _b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")

def _canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def _cid(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(obj)).hexdigest()

def _utcnow_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

class OPEClient:
    """Fallback OPEClient providing create_envelope() / send_envelope().

    Environment variables (mirrors odin-sdk expectations):
      - OPP_GATEWAY_URL / ODIN_GATEWAY_URL (default http://127.0.0.1:8080)
      - OPP_SENDER_PRIV_B64 / ODIN_SENDER_PRIV_B64 : base64url 32-byte Ed25519 seed (no padding)
      - OPP_SENDER_KID / ODIN_SENDER_KID : key id (default 'opp-sender')
    send_envelope() will POST JSON to {gateway_url}/api/v1/envelopes if network reachable; otherwise it silently ignores errors.
    """
    def __init__(self, gateway_url: Optional[str] = None, sender_priv_b64: Optional[str] = None, sender_kid: Optional[str] = None):
        self.gateway_url = gateway_url or os.getenv("OPP_GATEWAY_URL") or os.getenv("ODIN_GATEWAY_URL") or "http://127.0.0.1:8080"
        self.sender_priv_b64 = sender_priv_b64 or os.getenv("ODIN_SENDER_PRIV_B64") or os.getenv("OPP_SENDER_PRIV_B64")
        if not self.sender_priv_b64:
            raise RuntimeError("Missing ODIN_SENDER_PRIV_B64 / OPP_SENDER_PRIV_B64 (base64url 32-byte Ed25519 seed)")
        self.sender_kid = sender_kid or os.getenv("ODIN_SENDER_KID") or os.getenv("OPP_SENDER_KID") or "opp-sender"
        seed_bytes = base64.urlsafe_b64decode(self.sender_priv_b64 + "=" * (-len(self.sender_priv_b64) % 4))
        if len(seed_bytes) != 32:
            raise ValueError("Ed25519 seed must be 32 bytes")
        self._priv = Ed25519PrivateKey.from_private_bytes(seed_bytes)
        self._pub = self._priv.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
        self._pub_b64u = _b64u(self._pub)

    def create_envelope(self, payload: Dict[str, Any], payload_type: str, target_type: str, trace_id: Optional[str] = None, ts: Optional[str] = None) -> Dict[str, Any]:
        trace_id = trace_id or os.getenv("OPP_TRACE_ID") or os.getenv("ODIN_TRACE_ID") or "opp-trace"
        ts = ts or _utcnow_iso()
        cid = _cid(payload)
        msg = f"{cid}|{trace_id}|{ts}".encode("utf-8")
        sig = self._priv.sign(msg)
        return {
            "trace_id": trace_id,
            "ts": ts,
            "sender": {"kid": self.sender_kid, "jwk": {"kty": "OKP", "crv": "Ed25519", "x": self._pub_b64u}},
            "payload": payload,
            "payload_type": payload_type,
            "target_type": target_type,
            "cid": cid,
            "signature": _b64u(sig),
        }

    def send_envelope(self, env: Dict[str, Any]):  # best-effort POST
        url = self.gateway_url.rstrip("/") + "/api/v1/envelopes"
        try:
            with httpx.Client(timeout=2.0) as c:
                resp = c.post(url, json=env)
                return {"status_code": resp.status_code}
        except Exception:
            return {"status_code": None}

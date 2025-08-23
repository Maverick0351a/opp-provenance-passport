from __future__ import annotations
import base64, json, hashlib
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
import httpx
from opp.graph import build_graph_from_bundle, to_passport  # type: ignore

app = FastAPI(title="OPP Exporter API", version="0.1.0")

def canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def sha256_hex(b: bytes) -> str:
    import hashlib
    return hashlib.sha256(b).hexdigest()

def b64u_decode(s: str) -> bytes:
    s = s.strip()
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

def verify_signature(jwk: Dict[str, Any], message: bytes, sig_b64u: str) -> bool:
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        pub = Ed25519PublicKey.from_public_bytes(b64u_decode(jwk["x"]))
        pub.verify(b64u_decode(sig_b64u), message)
        return True
    except Exception:
        return False

async def fetch_json(url: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.json()

@app.get("/graph/{trace_id}")
async def graph(trace_id: str, gateway: Optional[str] = None):
    gw = gateway or "http://127.0.0.1:8080"
    bundle = await fetch_json(f"{gw}/v1/receipts/export/{trace_id}")
    # build minimal graph
    chain = bundle.get("chain") or bundle.get("hops", [])
    nodes = [{"id": r.get("receipt_hash"), "ts": r.get("ts")} for r in chain]
    edges = [{"from": chain[i-1].get("receipt_hash"), "to": chain[i].get("receipt_hash")} for i in range(1, len(chain))]
    return {"trace_id": trace_id, "nodes": nodes, "edges": edges, "count": len(nodes)}

@app.get("/validate/{trace_id}")
async def validate(trace_id: str, gateway: Optional[str] = None, kid: Optional[str] = None):
    gw = gateway or "http://127.0.0.1:8080"
    # fetch bundle + headers via httpx to get signature headers
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"{gw}/v1/receipts/export/{trace_id}")
        r.raise_for_status()
        bundle = r.json()
        hdrs = {k.lower(): v for k, v in r.headers.items()}
    # local CID
    local_cid = "sha256:" + sha256_hex(canonical(bundle))
    hdr_cid = hdrs.get("x-odin-response-cid") or hdrs.get("x-odin-bundle-cid")
    cid_match = hdr_cid == local_cid if hdr_cid else False
    # chain check
    chain = bundle.get("chain") or bundle.get("hops", [])
    chain_ok = all(i == 0 or chain[i]["prev_receipt_hash"] == chain[i-1]["receipt_hash"] for i in range(len(chain)))
    # signature verify
    sig = hdrs.get("x-odin-signature")
    kid_hdr = hdrs.get("x-odin-kid") or kid
    jwks = await fetch_json(f"{gw}/.well-known/jwks.json")
    jwk = None
    for k in jwks.get("keys", []):
        if not kid_hdr or k.get("kid") == kid_hdr:
            jwk = k; break
    sig_ok = False
    variant = None
    if sig and jwk:
        # try cid|trace|ts then cid only
        for v in ["cid|trace|ts", "cid"]:
            if v == "cid|trace|ts":
                ts = bundle.get("ts") or (chain[-1].get("ts") if chain else None)
                msg = f"{local_cid}|{trace_id}|{ts}".encode("utf-8") if ts else None
            else:
                msg = local_cid.encode("utf-8")
            if msg and verify_signature(jwk, msg, sig):
                sig_ok = True; variant = v; break
    return {"ok": bool(cid_match and chain_ok and sig_ok), "chain_ok": chain_ok, "cid_match": cid_match, "sig_ok": sig_ok, "sig_variant": variant, "bundle_cid": local_cid, "kid": kid_hdr}

@app.get("/healthz")
async def healthz():
    return {"ok": True, "service": "opp-exporter", "version": "0.1.0"}

@app.get("/passport/{trace_id}")
async def passport(trace_id: str, gateway: Optional[str] = None):
    gw = gateway or "http://127.0.0.1:8080"
    bundle = await fetch_json(f"{gw}/v1/receipts/export/{trace_id}")
    graph = build_graph_from_bundle(bundle)
    return to_passport(graph, bundle)

@app.get("/policy/{trace_id}")
async def policy(trace_id: str, gateway: Optional[str] = None):
    gw = gateway or "http://127.0.0.1:8080"
    bundle = await fetch_json(f"{gw}/v1/receipts/export/{trace_id}")
    chain = bundle.get("chain") or bundle.get("hops") or []
    decisions = []
    breaches = []
    engines = []
    for r in chain:
        norm = r.get("normalized", {})
        policy = norm.get("policy") or {}
        if isinstance(policy, dict):
            eng = policy.get("engine") or policy.get("policy_engine")
            if eng and eng not in engines:
                engines.append(eng)
            decs = policy.get("decisions") or norm.get("policy_decisions")
            if isinstance(decs, list):
                for d in decs:
                    if isinstance(d, dict):
                        decisions.append(d)
                        outcome = (d.get("outcome") or d.get("result") or d.get("decision") or "").lower()
                        if outcome and outcome not in ("allow", "pass", "ok"):
                            breaches.append(d)
    return {"trace_id": trace_id, "engines": engines, "decisions": decisions, "breaches": breaches, "breach_count": len(breaches)}

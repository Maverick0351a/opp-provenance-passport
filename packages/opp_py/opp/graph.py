from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
from .merkle import merkle_root

def _collect_dataset_roots(bundle: Dict[str, Any]) -> List[str]:
    datasets = []
    chain = bundle.get("chain") or bundle.get("hops") or []
    for r in chain:
        norm = r.get("normalized", {})
        ds = norm.get("dataset") or norm.get("datasets")
        if isinstance(ds, list):
            for d in ds:
                if isinstance(d, dict) and "chunks" in d:
                    roots = [c.get("cid", "") for c in d.get("chunks", []) if c.get("cid")]
                    if roots:
                        datasets.append(merkle_root([cid.encode() for cid in roots]))
        elif isinstance(ds, dict) and "chunks" in ds:
            roots = [c.get("cid", "") for c in ds.get("chunks", []) if c.get("cid")]
            if roots:
                datasets.append(merkle_root([cid.encode() for cid in roots]))
    return datasets

def to_passport(graph: Dict[str, Any], bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Produce an auditor‑friendly passport summary.

    Extracts:
      - trace_id
      - counts (receipts, distinct steps)
      - first/last timestamps
      - model identifier (if present)
      - dataset Merkle roots (derived)
      - evaluation metrics (accuracy, loss, etc if present in normalized payloads)
      - safety flags (aggregate OR of boolean flags)
    """
    chain = bundle.get("chain") or bundle.get("hops") or []
    steps = [r.get("normalized", {}).get("step") for r in chain if r.get("normalized", {}).get("step")]
    distinct_steps = sorted(set(steps))
    timestamps = [r.get("ts") for r in chain if r.get("ts")]
    model_id: Optional[str] = None
    metrics: Dict[str, Any] = {}
    safety: Dict[str, bool] = {}
    policy_engines: List[str] = []
    policy_breaches: List[Dict[str, Any]] = []
    policy_decisions: List[Dict[str, Any]] = []
    for r in chain:
        norm = r.get("normalized", {})
        if not model_id:
            model_id = norm.get("model_id") or norm.get("model")
        m = norm.get("metrics")
        if isinstance(m, dict):
            for k, v in m.items():
                # prefer final metric (later overwrites earlier)
                metrics[k] = v
        sf = norm.get("safety") or {}
        if isinstance(sf, dict):
            for k, v in sf.items():
                if isinstance(v, bool):
                    safety[k] = safety.get(k, False) or v
        # policy extraction
        policy = norm.get("policy") or {}
        if isinstance(policy, dict):
            eng = policy.get("engine") or policy.get("policy_engine")
            if eng and eng not in policy_engines:
                policy_engines.append(eng)
            decs = policy.get("decisions") or norm.get("policy_decisions")
            if isinstance(decs, list):
                for d in decs:
                    if isinstance(d, dict):
                        policy_decisions.append(d)
                        outcome = (d.get("outcome") or d.get("result") or d.get("decision") or "").lower()
                        if outcome and outcome not in ("allow", "pass", "ok"):
                            policy_breaches.append(d)
    dataset_roots = _collect_dataset_roots(bundle)
    return {
        "trace_id": bundle.get("trace_id") or (chain[0].get("trace_id") if chain else None),
        "receipts": graph.get("count"),
        "steps": distinct_steps,
        "first_ts": timestamps[0] if timestamps else None,
        "last_ts": timestamps[-1] if timestamps else None,
        "model_id": model_id,
        "dataset_roots": dataset_roots,
        "metrics": metrics,
        "safety_flags": safety,
    "policy_engines": policy_engines,
    "policy_decisions": policy_decisions,
    "policy_breaches": policy_breaches,
        "bundle_cid": bundle.get("bundle_cid") or bundle.get("cid"),
        "integrity": {
            "graph_nodes": len(graph.get("nodes", [])),
            "graph_edges": len(graph.get("edges", [])),
        },
        "summary": f"Model {model_id or 'N/A'} with {len(distinct_steps)} steps and {len(dataset_roots)} dataset roots"
    }

def build_graph_from_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Create a minimal provenance graph from an ODIN export bundle.

    Nodes: receipts (id = receipt_hash), Edges: prev->curr linkage.
    """
    chain = bundle.get("chain") or bundle.get("hops") or []
    nodes = []
    edges = []
    last = None
    for hop in chain:
        rid = hop.get("receipt_hash")
        nodes.append({"id": rid, "ts": hop.get("ts"), "step": hop.get("normalized", {}).get("step")})
        if last is not None:
            edges.append({"from": last, "to": rid, "type": "link"})
        last = rid
    return {"nodes": nodes, "edges": edges, "count": len(nodes)}

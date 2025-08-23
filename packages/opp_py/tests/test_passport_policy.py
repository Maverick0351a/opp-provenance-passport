from __future__ import annotations
from opp.graph import build_graph_from_bundle, to_passport

def make_receipt(receipt_hash, prev, step, policy=None, metrics=None, ts="2024-01-01T00:00:00Z"):
    norm = {"step": step}
    if policy: norm["policy"] = policy
    if metrics: norm["metrics"] = metrics
    return {"receipt_hash": receipt_hash, "prev_receipt_hash": prev, "normalized": norm, "ts": ts}

def test_passport_policy_breaches():
    chain = [
        make_receipt("h1", None, "ingest.v1", policy={"engine":"opa","decisions":[{"rule":"ok_rule","outcome":"allow"}]}),
        make_receipt("h2", "h1", "train.v1", metrics={"accuracy":0.9}, policy={"engine":"opa","decisions":[{"rule":"deny_rule","outcome":"deny"}]}),
    ]
    bundle = {"trace_id":"t1","chain": chain}
    graph = build_graph_from_bundle(bundle)
    passport = to_passport(graph, bundle)
    assert passport["policy_engines"] == ["opa"]
    assert len(passport["policy_decisions"]) == 2
    assert len(passport["policy_breaches"]) == 1
    assert passport["policy_breaches"][0]["rule"] == "deny_rule"
    assert passport["metrics"]["accuracy"] == 0.9

from __future__ import annotations

import os
import pytest

from opp.graph import build_graph_from_bundle, to_passport
from opp import decorators as dec


def _dataset_chunk(cid: str):
    return {"cid": cid, "size": 10}


def test_graph_dataset_roots_and_safety():
    # Two receipts with dataset chunks and safety flags merging
    chain = [
        {
            "trace_id": "tD",
            "receipt_hash": "r1",
            "ts": "2024-01-01T00:00:00Z",
            "normalized": {
                "step": "ingest.v1",
                "dataset": {"chunks": [_dataset_chunk("c1"), _dataset_chunk("c2")]},
                "safety": {"nsfw": False, "malware": False},
            },
        },
        {
            "trace_id": "tD",
            "receipt_hash": "r2",
            "prev_receipt_hash": "r1",
            "ts": "2024-01-01T00:00:05Z",
            "normalized": {
                "step": "train.v1",
                "datasets": [{"chunks": [_dataset_chunk("c3"), _dataset_chunk("c4")]}],
                "safety": {"nsfw": True, "malware": False},
                "metrics": {"loss": 0.12},
            },
        },
    ]
    bundle = {"trace_id": "tD", "chain": chain}
    graph = build_graph_from_bundle(bundle)
    passport = to_passport(graph, bundle)
    # Expect two dataset roots derived
    assert len(passport["dataset_roots"]) == 2
    # Safety flag nsfw should OR to True
    assert passport["safety_flags"]["nsfw"] is True
    assert passport["metrics"]["loss"] == 0.12


def test_decorator_missing_seed_env():
    # Ensure env vars absent
    for k in ["ODIN_SENDER_PRIV_B64", "OPP_SENDER_PRIV_B64"]:
        os.environ.pop(k, None)
    with pytest.raises(RuntimeError):
        dec._get_client(None)  # access helper directly

from __future__ import annotations

import base64
import json
import os
import tempfile
import types
from typing import Any

import pytest
import typer

from opp import cli as opp_cli
from opp import odin_shim


# ---------------- CLI TESTS -----------------


@pytest.fixture()
def fake_get():
    calls: list[str] = []

    def _fake(url: str) -> dict[str, Any]:
        calls.append(url)
        # Branch on path parts to return shape expected by command
        if "/receipts/export/" in url:
            # Provide a minimal bundle with two receipts
            trace = url.rsplit("/", 1)[-1]
            chain = [
                {"trace_id": trace, "receipt_hash": "r1", "ts": "2024-01-01T00:00:00Z", "normalized": {"step": "ingest.v1"}},
                {"trace_id": trace, "receipt_hash": "r2", "prev_receipt_hash": "r1", "ts": "2024-01-01T00:00:10Z", "normalized": {"step": "train.v1", "policy": {"engine": "opa", "decisions": [{"rule": "deny", "outcome": "deny"}]}}},
            ]
            return {"trace_id": trace, "chain": chain}
        if "/graph/" in url:
            return {"hello": "world"}
        if "/validate/" in url:
            ok = "bad" not in url
            return {"ok": ok, "details": "test"}
        return {}

    return calls, _fake


def test_cli_graph_api(monkeypatch, capsys, fake_get):
    calls, getter = fake_get
    monkeypatch.setattr(opp_cli, "_get", getter)
    opp_cli.graph(trace="t1", api="http://api")
    out = capsys.readouterr().out
    assert '"hello": "world"' in out
    assert any("/graph/" in c for c in calls)


def test_cli_graph_gateway(monkeypatch, capsys, fake_get):
    calls, getter = fake_get
    monkeypatch.setattr(opp_cli, "_get", getter)
    opp_cli.graph(trace="t2", gateway="http://gw", api=None)
    out = capsys.readouterr().out
    # Should include graph with count
    assert '"graph"' in out and '"count": 2' in out, out
    assert any("/receipts/export/" in c for c in calls)


def test_cli_graph_missing_params():
    with pytest.raises(typer.BadParameter):
        opp_cli.graph(trace="t", api=None, gateway=None)  # type: ignore[arg-type]


def test_cli_validate_api_ok(monkeypatch, capsys, fake_get):
    calls, getter = fake_get
    monkeypatch.setattr(opp_cli, "_get", getter)
    with pytest.raises(SystemExit) as exc:  # capture exit code
        opp_cli.validate(trace="t3", api="http://api", gateway="http://ignored")
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert '"ok": true' in out
    assert any("/validate/" in c for c in calls)


def test_cli_validate_gateway_bad_chain(monkeypatch, capsys, fake_get):
    calls, getter = fake_get

    def getter_bad(url: str) -> dict[str, Any]:
        d = getter(url)
        if "/receipts/export/" in url:
            # Break continuity
            d["chain"][1]["prev_receipt_hash"] = "WRONG"
        return d

    monkeypatch.setattr(opp_cli, "_get", getter_bad)
    with pytest.raises(SystemExit) as exc:
        opp_cli.validate(trace="t4", gateway="http://gw", api=None)
    assert exc.value.code == 2, capsys.readouterr().out
    out = capsys.readouterr().out
    assert '"ok": false' in out


def test_cli_passport_and_policy(monkeypatch, capsys, fake_get):
    calls, getter = fake_get
    monkeypatch.setattr(opp_cli, "_get", getter)
    # passport with file output
    with tempfile.TemporaryDirectory() as td:
        out_file = os.path.join(td, "passport.json")
        opp_cli.passport(trace="t5", gateway="http://gw", out=out_file)
        content = open(out_file, "r", encoding="utf-8").read()
        assert '"trace_id": "t5"' in content
    # clear any prior stdout (e.g., 'Wrote ...')
    capsys.readouterr()
    # policy prints summary
    opp_cli.policy(trace="t5", gateway="http://gw")
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["trace_id"] == "t5"
    assert data["breach_count"] == 1
    assert any("/receipts/export/" in c for c in calls)


# ---------------- ODIN SHIM TESTS -----------------


def _seed_b64u() -> str:
    seed = b"\x01" * 32
    return base64.urlsafe_b64encode(seed).decode().rstrip("=")


def test_odin_shim_create_and_send_success(monkeypatch):
    os.environ["OPP_SENDER_PRIV_B64"] = _seed_b64u()
    # Dummy httpx client
    class DummyResp:
        status_code = 202

    class DummyClient(types.SimpleNamespace):
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def post(self, url, json):  # noqa: A003 - shadow ok
            self.last = (url, json)
            return DummyResp()

    monkeypatch.setattr(odin_shim, "httpx", types.SimpleNamespace(Client=DummyClient))
    client = odin_shim.OPEClient(gateway_url="http://gw")
    env = client.create_envelope({"foo": "bar"}, "evt", "target")
    assert env["payload"]["foo"] == "bar"
    res = client.send_envelope(env)
    assert res["status_code"] == 202


def test_odin_shim_send_failure(monkeypatch):
    os.environ["OPP_SENDER_PRIV_B64"] = _seed_b64u()

    class BadClient:
        def __enter__(self):
            raise RuntimeError("network down")
        def __exit__(self, *a):
            return False

    monkeypatch.setattr(odin_shim, "httpx", types.SimpleNamespace(Client=BadClient))
    client = odin_shim.OPEClient(gateway_url="http://gw")
    env = client.create_envelope({"x": 1}, "evt", "tgt")
    res = client.send_envelope(env)
    assert res["status_code"] is None


def test_odin_shim_missing_seed(monkeypatch):
    # Clear related env vars
    for k in [
        "OPP_SENDER_PRIV_B64",
        "ODIN_SENDER_PRIV_B64",
    ]:
        os.environ.pop(k, None)
    with pytest.raises(RuntimeError):
        odin_shim.OPEClient()

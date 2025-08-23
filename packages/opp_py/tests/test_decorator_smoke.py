from opp.decorators import stamp
import types

class DummyClient(types.SimpleNamespace):
    def create_envelope(self, payload, payload_type, target_type, trace_id=None, ts=None):
        return {"payload": payload, "payload_type": payload_type, "target_type": target_type}
    def send_envelope(self, env):
        # simulate delivery
        return {"ok": True}

def test_stamp_decorator_monkeypatch(monkeypatch):
    # monkeypatch the client getter to avoid env requirements
    from opp import decorators as dec
    def fake_get(_):
        return DummyClient()
    monkeypatch.setattr(dec, "_get_client", fake_get)

    events = []
    @stamp("ingest.v1", attrs={"source":"files"})
    def run():
        events.append("ran")
        return 42

    assert run() == 42
    assert events == ["ran"]

from opp.decorators import stamp
import types

events = []

class CaptureClient(types.SimpleNamespace):
    def __init__(self):
        super().__init__(sent=[])
    def create_envelope(self, payload, payload_type, target_type, trace_id=None, ts=None):
        return {"payload": payload, "payload_type": payload_type, "target_type": target_type}
    def send_envelope(self, env):
        self.sent.append(env)
        return {"ok": True}

def test_stamp_inputs_outputs(monkeypatch):
    from opp import decorators as dec
    cap = CaptureClient()
    monkeypatch.setattr(dec, "_get_client", lambda _: cap)

    def inputs(args, kwargs):
        # represent inputs as tuple for deterministic CID
        return {"args": list(args), "kwargs": kwargs}
    def outputs(ret):
        return {"ret": ret}

    @stamp("compute.v1", inputs=inputs, outputs=outputs)
    def compute(a, b):
        return a + b

    assert compute(2, 5) == 7
    # Should have two envelopes
    assert len(cap.sent) == 2
    start, end = cap.sent
    assert start["payload"]["phase"] == "start"
    assert "inputs_cid" in start["payload"]
    assert end["payload"]["phase"] == "end"
    assert "outputs_cid" in end["payload"]
    assert "status" in end["payload"] and end["payload"]["status"] == "ok"

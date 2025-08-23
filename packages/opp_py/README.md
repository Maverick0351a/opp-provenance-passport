# OPP Python SDK (`opp_py`)

Instrumentation + CLI for ODIN Provenance Passport (OPP).

## Features
- `@stamp(step_type, attrs=..., inputs=..., outputs=...)` decorator emits start/end signed receipts.
- Automatic input/output content IDs (CIDs) via optional callables.
- Fallback lightweight OPE client (no external `odin-sdk` required) using env Ed25519 seed.
- Graph + Passport generation (`opp graph`, `opp passport`).
- Policy evidence aggregation & breach summary (`opp policy`).
- Optional C2PA bridge (`opp.c2pa.embed_bundle_cid`) to embed bundle CID into images (extra deps).

## Install (editable dev)
```bash
pip install -e packages/opp_py
```

Required env for stamping (generate a random 32‑byte seed once):
```bash
export OPP_GATEWAY_URL=http://127.0.0.1:8080
export OPP_SENDER_PRIV_B64=<base64url_32byte_seed>
export OPP_SENDER_KID=opp-sender
```

Generate a seed (PowerShell):
```powershell
$bytes = New-Object byte[] 32; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes); \
$seed = [Convert]::ToBase64String($bytes).TrimEnd('=') -replace '\+','-' -replace '/','_'; $seed
```

## Decorator Usage
```python
from opp.decorators import stamp

@stamp(
		"train.v1",
		attrs={"model":"resnet"},
		inputs=lambda args, kwargs: {"hyperparams": kwargs.get("hp")},
		outputs=lambda ret: {"metrics": ret.get("metrics")}
)
def train(data, *, hp):
		# ... training ...
		return {"metrics": {"accuracy": 0.93}}

train([], hp={"lr":1e-3})
```

Emitted start receipt includes `inputs_cid`; end receipt includes `outputs_cid` and `status`.

## CLI
```bash
opp graph --trace TRACE --gateway $OPP_GATEWAY_URL         # build minimal graph
opp validate --trace TRACE --gateway $OPP_GATEWAY_URL      # continuity + basic validation
opp passport --trace TRACE --gateway $OPP_GATEWAY_URL      # rich model/data passport JSON
opp policy --trace TRACE --gateway $OPP_GATEWAY_URL        # summarized policy evidence + breaches
```

## Passport Fields (excerpt)
```jsonc
{
	"trace_id": "...",
	"receipts": 12,
	"steps": ["ingest.v1","train.v1"],
	"dataset_roots": ["sha256:..."],
	"model_id": "model-123",
	"metrics": {"accuracy": 0.93},
	"safety_flags": {"pii_redacted": true},
	"policy_engines": ["opa"],
	"policy_breaches": [{"rule":"no_public_data","outcome":"deny"}]
}
```

## Policy Evidence
If receipts carry a normalized `policy` object with `engine` + `decisions[]`, breaches are auto‑derived when an outcome is not in `{allow, pass, ok}`.

## Optional C2PA Bridge
```bash
pip install c2pa Pillow
python examples/c2pa_embed.py image.png
```
Adds a custom assertion with the `bundle_cid` to the image manifest.

## Airflow & Dagster Examples
See `examples/airflow_dag.py` and `examples/dagster_job.py` for task/op instrumentation and trace continuity.

## Testing
```bash
pytest -q packages/opp_py/tests
```

## Backward Compatibility
New fields are additive; existing receipt payload fields preserved. Hashing uses canonical JSON (stable order, no whitespace).

## License
Apache 2.0

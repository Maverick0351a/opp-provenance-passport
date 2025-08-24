# OPP Python SDK (`opp_py`)

Provenance instrumentation + CLI for the **ODIN Provenance Passport (OPP)**. Decorate code, stamp signed chained receipts, then materialize a verifiable graph, model/data passport, and policy breach summary.

> Part of the monorepo: root README covers the exporter API + Next.js explorer UI.

## Key Features
* `@stamp(step_type, attrs=..., inputs=..., outputs=...)` decorator emits start & end receipts (with continuity, status, CIDs).
* Automatic input/output canonicalization + CID generation (content addressable provenance).
* Lightweight embedded OPE client (no external odin SDK) using an Ed25519 seed from env vars.
* CLI commands: `graph`, `validate`, `passport`, `policy` (work with gateway or exporter API).
* Policy decision aggregation & breach derivation (deny / non-allow outcomes surfaced).
* Dataset & model summarization: dataset chunk Merkle roots, safety flag OR-ing, metrics merge.
* Optional C2PA bridge (`opp.c2pa.embed_bundle_cid`) to embed bundle CID in image manifests (extra deps).
* Typed package (`py.typed`) + ruff + mypy clean in CI with >=90% coverage gate.

## Install
PyPI (latest released):
```bash
pip install opp-py
```

Editable (from repo root) for local hacking:
```bash
pip install -e packages/opp_py
```

Optional extras (C2PA embedding):
```bash
pip install 'opp-py[c2pa]'
```

## Environment Variables
| Var | Purpose | Required | Example |
| --- | --- | --- | --- |
| `OPP_GATEWAY_URL` | Base URL of ODIN gateway | For CLI against gateway | `http://127.0.0.1:8080` |
| `OPP_SENDER_PRIV_B64` (or `ODIN_SENDER_PRIV_B64`) | Base64url (no padding) 32‑byte Ed25519 seed used to derive keypair | For stamping | `Base64URLSeed` |
| `OPP_SENDER_KID` | Key ID to place in receipts | Optional (default `opp-sender`) | `my-signer` |

Generate a seed (Linux/macOS bash):
```bash
python - <<'PY'
import os,base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip('='))
PY
```

Generate a seed (PowerShell):
```powershell
$bytes = New-Object byte[] 32; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes);
$seed = [Convert]::ToBase64String($bytes).TrimEnd('=') -replace '\+','-' -replace '/','_'; $seed
```

Export (bash):
```bash
export OPP_GATEWAY_URL=http://127.0.0.1:8080
export OPP_SENDER_PRIV_B64=<seed>
export OPP_SENDER_KID=opp-sender
```

## Decorator Quick Start
```python
from opp.decorators import stamp

@stamp(
		"train.v1",
		attrs={"model": "resnet"},
		inputs=lambda args, kwargs: {"hyperparams": kwargs.get("hp")},
		outputs=lambda ret: {"metrics": ret.get("metrics")},
)
def train(data, *, hp):
		# ... train ...
		return {"metrics": {"accuracy": 0.93}}

train([], hp={"lr": 1e-3})
```
Start receipt: `inputs_cid` + status=started. End receipt: `outputs_cid`, status=finished (or error info if exception raised before re‑raising).

### Advanced Patterns
* Access original function arguments inside `inputs` factory to compute derived fingerprints (e.g., dataset digests).
* Raise inside decorated function: end receipt still emitted with `status=error` + `error_type`/`error_message` before exception propagates.
* Provide `attrs` for static metadata (model arch, dataset id, region) – included in both receipts for convenience.

## CLI Usage
```bash
# Build graph JSON (gateway)
opp graph --trace TRACE_ID --gateway $OPP_GATEWAY_URL

# Same, but via exporter API (which pre-validates and may enrich)
opp graph --trace TRACE_ID --api http://127.0.0.1:8099

# Validate continuity & signatures
opp validate --trace TRACE_ID --gateway $OPP_GATEWAY_URL

# Emit model/data passport (save to file)
opp passport --trace TRACE_ID --gateway $OPP_GATEWAY_URL --out passport.json

# Summarize policy decisions & breaches
opp policy --trace TRACE_ID --gateway $OPP_GATEWAY_URL
```

Exit codes: `validate` returns 0 on success, 2 on validation failures.

## Passport (Representative Fields)
```jsonc
{
	"trace_id": "...",
	"receipts": 12,
	"steps": ["ingest.v1", "train.v1"],
	"dataset_roots": ["sha256:..."],
	"model_id": "model-123",
	"metrics": {"accuracy": 0.93},
	"safety_flags": {"nsfw": false, "malware": false},
	"policy_engines": ["opa"],
	"breach_count": 1,
	"policy_breaches": [{"rule": "no_public_data", "outcome": "deny"}]
}
```

### Policy Derivation
Receipts containing a normalized `policy` object with `engine` + `decisions[]` are parsed. Any decision whose `outcome` not in `{allow, pass, ok}` is counted as a breach.

## Optional C2PA Bridge
Install extras: `pip install 'opp-py[c2pa]'` (on Windows you may need WSL + `exiv2` system libs). Then:
```python
from opp.c2pa import embed_bundle_cid
embed_bundle_cid("image.png", "sha256:bundlecid...")
```
Adds a custom assertion referencing the bundle CID. Raises a clear error if deps missing.

## Testing
```bash
pytest -q packages/opp_py/tests
```
CI enforces ruff, mypy, and >=90% coverage.

## Backward Compatibility Notes
* New receipt fields are additive.
* Canonical JSON (sorted keys, no extraneous whitespace) is used before hashing.
* Content IDs include the `sha256:` prefix for clarity and interop.

## Troubleshooting
| Issue | Cause | Fix |
| ----- | ----- | --- |
| `RuntimeError: missing signer seed` | Env seed not set | Export `OPP_SENDER_PRIV_B64` (or `ODIN_SENDER_PRIV_B64`). |
| Signature validation fails | Gateway mismatch or altered receipt | Re-fetch bundle; confirm gateway URL & no mutation. |
| C2PA install fails on Windows | Native `py3exiv2` dependency missing | Use WSL or skip C2PA optional path. |

## License
Apache 2.0

# ODIN Provenance Passport (OPP) — Starter

[![opp-ci](https://github.com/Maverick0351a/opp-provenance-passport/actions/workflows/ci.yml/badge.svg)](https://github.com/Maverick0351a/opp-provenance-passport/actions)
[![google-partner](https://img.shields.io/badge/Google%20Cloud-Partner-blue?logo=googlecloud&logoColor=white)](https://cloud.google.com/partners)
[![release](https://img.shields.io/github/v/release/Maverick0351a/opp-provenance-passport)](https://github.com/Maverick0351a/opp-provenance-passport/releases)
[![PyPI version](https://img.shields.io/pypi/v/opp-py)](https://pypi.org/project/opp-py/)
[![codecov](https://codecov.io/gh/Maverick0351a/opp-provenance-passport/branch/master/graph/badge.svg)](https://codecov.io/gh/Maverick0351a/opp-provenance-passport)
[![codeql](https://github.com/Maverick0351a/opp-provenance-passport/actions/workflows/codeql.yml/badge.svg)](https://github.com/Maverick0351a/opp-provenance-passport/actions/workflows/codeql.yml)

**One‑liner:** Turnkey provenance + policy layer that stamps & validates **datasets, prompts, model builds, and agent/tool runs** with chained, signed ODIN OPE receipts, then elevates them into a human + machine readable Model Passport & Policy view.

This starter includes:
- **opp_py** (Python SDK): decorators (inputs/outputs CIDs) + CLI (graph, validate, passport, policy).
- **exporter_api** (FastAPI): fetches & verifies receipt bundles; endpoints `/graph/{trace}`, `/validate/{trace}`, `/passport/{trace}`, `/policy/{trace}`.
- **explorer** (Next.js): visual graph + verification banner + passport & policy breach panel.
- **opp_js** (early preview): TypeScript scaffolding to add similar decorators in Node runtimes.
- **spec**: JSON‑LD context & JSON Schemas for common steps.
- **examples**: RAG ingest, Airflow DAG, Dagster job, C2PA embedding.
- **AGENT.md**: ready‑to‑use Copilot prompts and tasking playbook.
- **Quality Gates**: CI enforces ruff, mypy (clean), and >=70% coverage (currently ~90%).
- **Security**: Automated Bandit static analysis + pip-audit vulnerability scan on PRs, pushes, and weekly schedule.

> The Python SDK section below mirrors its internal `packages/opp_py/README.md` for convenience.

> You’ll need an **ODIN Gateway** running (local or Cloud Run) that exposes `/v1/receipts/export/{trace_id}` and `/.well-known/jwks.json`.
> See: https://github.com/Maverick0351a/odin-gateway-starter

---

## Quick Start (Python)

```bash
# 0) Create & activate a venv (recommended)
python -m venv .venv && source .venv/bin/activate  # (Windows: .\.venv\Scripts\Activate.ps1)

# 1) Install opp_py in editable mode + exporter_api deps
pip install -e packages/opp_py
pip install -r services/exporter_api/requirements.txt

# 2) Set your ODIN Gateway URL
export OPP_GATEWAY_URL="http://127.0.0.1:8080"   # or your Cloud Run URL

# 3) Run the exporter API (verifies bundles and builds a provenance graph)
uvicorn services.exporter_api.main:app --reload --port 8099

# 4) Explore in a browser (separate terminal): Next.js explorer (optional)
cd apps/explorer
npm install
npm run dev
# open http://localhost:3000
```

## CLI (opp_py)

After `pip install -e packages/opp_py` the `opp` command is available:

```bash
# Graph from a trace id (hits exporter_api by default; can use gateway directly with --gateway)
opp graph --trace TRACE_ID --api http://127.0.0.1:8099

# Validate a bundle fetched from the gateway
opp validate --trace TRACE_ID --gateway "$OPP_GATEWAY_URL"

# Create a simple Model Passport (JSON) from the verified bundle
opp passport --trace TRACE_ID --gateway "$OPP_GATEWAY_URL" --out model_passport.json
opp policy --trace TRACE_ID --gateway "$OPP_GATEWAY_URL"
```

### Exit Codes
| Command | Success | Validation Failure |
| ------- | ------- | ------------------ |
| `opp validate` | 0 | 2 |

---

## Python SDK (opp_py) Deep Dive

### Key Features
* `@stamp(step_type, attrs=..., inputs=..., outputs=...)` decorator emits start & end receipts with continuity + status.
* Automatic input/output canonicalization & CID generation (content-addressed provenance graph edges).
* Lightweight built-in OPE client (Ed25519 seed from env) — no external odin SDK required.
* CLI: `graph`, `validate`, `passport`, `policy` — operate directly on gateway or via exporter API.
* Policy decision aggregation & breach derivation (any outcome not in `{allow, pass, ok}` counted as breach).
* Dataset chunk Merkle roots & safety flag OR-ing; metrics merged across steps.
* Optional C2PA bridge: embed bundle CID in image manifest (`opp.c2pa.embed_bundle_cid`).
* Typed package + ruff + mypy; test coverage gate >=90% (see badge).

### Install
PyPI:
```bash
pip install opp-py
```
Editable (monorepo):
```bash
pip install -e packages/opp_py
```
Extras:
```bash
pip install 'opp-py[c2pa]'
```

### Environment Variables
| Var | Purpose | Required | Example |
| --- | --- | --- | --- |
| `OPP_GATEWAY_URL` | ODIN gateway base URL | For gateway CLI ops | `http://127.0.0.1:8080` |
| `OPP_SENDER_PRIV_B64` (or `ODIN_SENDER_PRIV_B64`) | Base64url (no padding) 32‑byte Ed25519 seed | For stamping | `Base64URLSeed` |
| `OPP_SENDER_KID` | Key ID placed in receipts | Optional (default `opp-sender`) | `my-signer` |

Generate seed (bash):
```bash
python - <<'PY'
import os,base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip('='))
PY
```
PowerShell:
```powershell
$bytes = New-Object byte[] 32; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes);
$seed = [Convert]::ToBase64String($bytes).TrimEnd('=') -replace '\+','-' -replace '/','_'; $seed
```

### Decorator Usage
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
Start receipt supplies `inputs_cid`; end receipt adds `outputs_cid` + status (and error info if exception).

#### Advanced Tips
* Inputs factory can derive hashed summaries (e.g., dataset digests) from raw arguments.
* Exceptions still trigger an end receipt with `status=error` before being re-raised.
* Use `attrs` for static metadata repeated across receipts (model architecture, region, dataset id).

### Passport (Representative Fields)
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

### Optional C2PA Bridge
```bash
pip install 'opp-py[c2pa]'
```
On Windows, if native deps fail, use WSL with `exiv2` libs or skip (the rest still functions). Usage:
```python
from opp.c2pa import embed_bundle_cid
embed_bundle_cid("image.png", "sha256:bundlecid...")
```

### Troubleshooting
| Issue | Cause | Fix |
| ----- | ----- | --- |
| `RuntimeError: missing signer seed` | Seed env absent | Export `OPP_SENDER_PRIV_B64`. |
| Validation failure | Continuity/signature mismatch | Re-fetch; ensure gateway integrity & receipt order. |
| C2PA install fails | Missing native `py3exiv2` dep | Use WSL or omit `[c2pa]` extra. |

---

### Optional: C2PA Embedding

To enable image manifest embedding (adds the bundle CID into a C2PA assertion):

```bash
pip install 'opp-py[c2pa]'
```

If installation fails on Windows due to `py3exiv2` (missing `exiv2` native library), you can:

1. Use WSL (Ubuntu) and install system deps: `sudo apt-get update && sudo apt-get install -y exiv2 libexiv2-dev` then re-run the pip install.
2. Or skip C2PA locally; the core SDK works without it. The test suite will gracefully skip C2PA happy‑path tests if deps are absent.

Usage:

```python
from opp.c2pa import embed_bundle_cid
out_path = embed_bundle_cid("image.png", "sha256:...bundlecid...")
print("Wrote", out_path)
```

The helper raises a clear `RuntimeError` if optional deps are missing.

## VS Code / Copilot

- Open this folder in VS Code.
- Read **AGENT.md** first — it contains **copy‑paste prompts** for Copilot Chat to extend this repo (schemas, UI, integrations).
- Use the **built‑in tasks** in AGENT.md to iteratively implement features (Airflow/LangChain integrations, C2PA bridge, etc.).

## License

Apache 2.0 — see [LICENSE](LICENSE).


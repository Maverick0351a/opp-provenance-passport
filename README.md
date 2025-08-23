# ODIN Provenance Passport (OPP) — Starter

**One‑line:** a turnkey provenance layer that stamps **datasets, prompts, models, and agent runs** with cryptographically verifiable receipts — built on the ODIN OPE protocol.

This starter includes:
- **opp_py** (Python SDK): decorators (inputs/outputs CIDs) + CLI (graph, validate, passport, policy).
- **exporter_api** (FastAPI): fetches & verifies receipt bundles; endpoints `/graph/{trace}`, `/validate/{trace}`, `/passport/{trace}`, `/policy/{trace}`.
- **explorer** (Next.js): visual graph + verification banner + passport & policy breach panel.
- **opp_js** (early preview): TypeScript scaffolding to add similar decorators in Node runtimes.
- **spec**: JSON‑LD context & JSON Schemas for common steps.
- **examples**: RAG ingest, Airflow DAG, Dagster job, C2PA embedding.
- **AGENT.md**: ready‑to‑use Copilot prompts and tasking playbook.

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

## VS Code / Copilot

- Open this folder in VS Code.
- Read **AGENT.md** first — it contains **copy‑paste prompts** for Copilot Chat to extend this repo (schemas, UI, integrations).
- Use the **built‑in tasks** in AGENT.md to iteratively implement features (Airflow/LangChain integrations, C2PA bridge, etc.).

## License

Apache 2.0 — see [LICENSE](LICENSE).


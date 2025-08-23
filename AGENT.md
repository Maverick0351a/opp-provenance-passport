# AGENT.md — Copilot Playbook for OPP

You are **Copilot for ODIN Provenance Passport (OPP)**. Your mission is to help instrument AI pipelines with cryptographically verifiable provenance receipts and render human‑readable passports.

## Context & Principles
- **Substrate:** ODIN Gateway signs & verifies; OPP instruments and visualizes.
- **Receipts:** Content‑addressed (CID) + Ed25519 signed; hash‑linked chains per `trace_id`.
- **Bundles:** `/v1/receipts/export/{trace_id}` returns signed sets for offline verification.

## Codebase Map
- `packages/opp_py/opp/*` — decorators, graph builder, CLI
- `services/exporter_api/*` — FastAPI to verify bundles and emit graphs/passports
- `apps/explorer/*` — Next.js graph viewer
- `spec/*` — JSON‑LD context & JSON Schemas

## Golden Prompts (paste into Copilot Chat)

### 1) Extend Python decorator to capture inputs/outputs
> Open `packages/opp_py/opp/decorators.py`. Add optional `inputs` and `outputs` callables to `@stamp(...)` that compute CIDs from arguments and return values. Include them in the emitted receipt payload. Update tests in `packages/opp_py/opp/tests`.

### 2) Add Airflow/Dagster integration examples
> Create `examples/airflow_dag.py` and `examples/dagster_job.py` that wrap tasks/ops with `@stamp` and demonstrate trace continuity across steps. Use environment variable `OPP_TRACE_ID` as a default if present.

### 3) Build a richer model passport
> In `packages/opp_py/opp/graph.py`, add a `to_passport(graph, bundle)` that summarizes datasets (Merkle roots), model id, eval metrics, and safety flags. Return JSON designed for auditors. Expose via CLI and exporter_api.

### 4) Explorer: add D3 graph + verify banner
> In `apps/explorer/app/components/Graph.tsx`, render nodes/edges from `/api/graph?trace=...`. Add a green banner when `sig_ok && chain_ok` is true. Include copy‑to‑clipboard for the `bundle_cid`.

### 5) C2PA bridge
> Add `packages/opp_py/opp/c2pa.py` with helper to embed `bundle_cid` into C2PA assertions on generated images. Provide an example script in `examples/c2pa_embed.py`. Do not include heavy deps by default; guard imports.

### 6) Policy evidence
> Ensure exporter_api includes `policy_engine` and decision metadata (if present in receipts). Add a filter to show policy breaches in the explorer UI.

## House Rules
- Maintain backward compatibility of receipt fields; extend additively.
- Keep all crypto ops side‑effect free and deterministic; never reformat JSON before hashing.
- Prefer small, well‑named modules and strong typing hints.

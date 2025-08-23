from __future__ import annotations
import json, sys
import httpx
import typer
from typing import Optional
from .graph import build_graph_from_bundle, to_passport

app = typer.Typer(help="OPP CLI — provenance graphs, passports, validation")

def _get(url: str) -> dict:
    with httpx.Client(timeout=15.0) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.json()

@app.command()
def graph(trace: str = typer.Option(..., "--trace", help="Trace ID"),
          api: Optional[str] = typer.Option(None, "--api", help="Exporter API base (if set uses /graph)"),
          gateway: Optional[str] = typer.Option(None, "--gateway", help="Gateway base (if set fetches /v1/receipts/export)")):
    if api:
        data = _get(f"{api}/graph/{trace}")
        print(json.dumps(data, indent=2))
        return
    if not gateway:
        raise typer.BadParameter("Provide --api or --gateway")
    bundle = _get(f"{gateway}/v1/receipts/export/{trace}")
    g = build_graph_from_bundle(bundle)
    print(json.dumps({"graph": g}, indent=2))

@app.command()
def validate(trace: str = typer.Option(..., "--trace"),
             gateway: str = typer.Option(..., "--gateway", help="Gateway base URL"),
             api: Optional[str] = typer.Option(None, "--api", help="Exporter API (uses /validate)")):
    if api:
        data = _get(f"{api}/validate/{trace}")
        print(json.dumps(data, indent=2))
        sys.exit(0 if data.get("ok") else 2)
    bundle = _get(f"{gateway}/v1/receipts/export/{trace}")
    # Local minimal validation: just presence and chain continuity
    chain = bundle.get("chain") or bundle.get("hops") or []
    ok = True
    for i in range(1, len(chain)):
        if chain[i].get("prev_receipt_hash") != chain[i-1].get("receipt_hash"):
            ok = False
            break
    print(json.dumps({"ok": ok, "count": len(chain)}, indent=2))
    sys.exit(0 if ok else 2)

@app.command()
def passport(trace: str = typer.Option(..., "--trace"),
             gateway: str = typer.Option(..., "--gateway"),
             out: Optional[str] = typer.Option(None, "--out", help="Write to file")):
    bundle = _get(f"{gateway}/v1/receipts/export/{trace}")
    graph = build_graph_from_bundle(bundle)
    passport_obj = to_passport(graph, bundle)
    s = json.dumps(passport_obj, indent=2)
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(s)
        print(f"Wrote {out}")
    else:
        print(s)

@app.command()
def policy(trace: str = typer.Option(..., "--trace"), gateway: str = typer.Option(..., "--gateway")):
    bundle = _get(f"{gateway}/v1/receipts/export/{trace}")
    graph = build_graph_from_bundle(bundle)
    passport_obj = to_passport(graph, bundle)
    out = {
        "trace_id": passport_obj.get("trace_id"),
        "policy_engines": passport_obj.get("policy_engines"),
        "breaches": passport_obj.get("policy_breaches"),
        "breach_count": len(passport_obj.get("policy_breaches", [])),
    }
    print(json.dumps(out, indent=2))

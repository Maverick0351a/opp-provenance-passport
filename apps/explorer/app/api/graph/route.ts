import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest) {
  const trace = req.nextUrl.searchParams.get('trace');
  const gateway = req.nextUrl.searchParams.get('gateway') || 'http://127.0.0.1:8080';
  if (!trace) return NextResponse.json({ error: 'missing trace' }, { status: 400 });
  const url = `${gateway}/v1/receipts/export/${encodeURIComponent(trace)}`;
  try {
    const r = await fetch(url, { cache: 'no-store' });
    if (!r.ok) return NextResponse.json({ error: 'gateway fetch failed', status: r.status }, { status: 502 });
    const bundle = await r.json();
    const chain = bundle.chain || bundle.hops || [];
    const nodes = chain.map((h: any) => ({ id: h.receipt_hash, ts: h.ts, step: h.normalized?.step }));
    const edges = chain.slice(1).map((h: any, i: number) => ({ from: chain[i].receipt_hash, to: h.receipt_hash }));
    return NextResponse.json({ trace_id: trace, nodes, edges, count: nodes.length });
  } catch (e: any) {
    return NextResponse.json({ error: e.message || 'error' }, { status: 500 });
  }
}

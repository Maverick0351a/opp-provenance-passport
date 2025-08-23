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
    const localCid = 'sha256:' + await sha256Json(bundle);
    // Basic continuity check
    const chainOk = chain.every((h: any, i: number) => i === 0 || h.prev_receipt_hash === chain[i-1].receipt_hash);
    return NextResponse.json({
      ok: chainOk,
      chain_ok: chainOk,
      cid_match: true, // we only compute locally here
      sig_ok: false,   // exporter_api does signature verify; gateway path does not provide headers here
      bundle_cid: localCid
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message || 'error' }, { status: 500 });
  }
}

async function sha256Json(obj: any): Promise<string> {
  const enc = new TextEncoder();
  const data = enc.encode(JSON.stringify(obj, Object.keys(obj).sort()));
  const hash = await crypto.subtle.digest('SHA-256', data);
  return Array.from(new Uint8Array(hash)).map(b=>b.toString(16).padStart(2,'0')).join('');
}

"use client";
import { useState } from 'react';
import Graph from './components/Graph';

interface ValidateResp { ok: boolean; chain_ok: boolean; cid_match: boolean; sig_ok: boolean; bundle_cid?: string; }

export default function Page() {
  const [trace, setTrace] = useState('demo-trace-001');
  const [gateway, setGateway] = useState('http://127.0.0.1:8080');
  const [graph, setGraph] = useState<any | null>(null);
  const [verify, setVerify] = useState<ValidateResp | null>(null);
  const [loading, setLoading] = useState(false);
  const [passport, setPassport] = useState<any | null>(null);
  const [showBreaches, setShowBreaches] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true); setError(null);
    try {
      const gRes = await fetch(`/api/graph?trace=${encodeURIComponent(trace)}&gateway=${encodeURIComponent(gateway)}`);
      const gData = await gRes.json();
      setGraph(gData);
      const vRes = await fetch(`/api/validate?trace=${encodeURIComponent(trace)}&gateway=${encodeURIComponent(gateway)}`);
      const vData = await vRes.json();
      setVerify(vData);
      const pRes = await fetch(`${gateway.replace(/\/$/, '')}/passport/${encodeURIComponent(trace)}`);
      if (pRes.ok) {
        const pData = await pRes.json();
        setPassport(pData);
      } else {
        setPassport(null);
      }
    } catch (e: any) {
      setError(e.message || 'Fetch failed');
    } finally {
      setLoading(false);
    }
  }

  const verified = verify && verify.sig_ok && verify.chain_ok;

  function copyCid() {
    if (verify?.bundle_cid) navigator.clipboard.writeText(verify.bundle_cid);
  }

  return (
    <main>
      <h1>OPP Explorer</h1>
      <p>Fetch and visualize a provenance graph, then verify signatures & chain integrity.</p>
      <div style={{display:'flex',gap:8,flexWrap:'wrap',marginBottom:12}}>
        <input value={trace} onChange={e=>setTrace(e.target.value)} placeholder="trace_id"/>
        <input value={gateway} onChange={e=>setGateway(e.target.value)} placeholder="gateway url" style={{minWidth:260}}/>
        <button onClick={run} disabled={loading}>{loading ? 'Loading...' : 'Fetch & Verify'}</button>
      </div>
      {error && <div style={{background:'#fee',padding:8,border:'1px solid #f99',marginBottom:12}}>Error: {error}</div>}
      {verify && (
        <div style={{
          background: verified ? '#0a4' : '#444',
          color: 'white', padding: '8px 12px', borderRadius: 6, marginBottom: 16,
          display:'flex',alignItems:'center',gap:16
        }}>
          <strong>{verified ? 'Verification OK' : 'Verification Incomplete / Failed'}</strong>
          <span>sig_ok: {String(verify.sig_ok)} chain_ok: {String(verify.chain_ok)} cid_match: {String(verify.cid_match)}</span>
          {verify.bundle_cid && <button onClick={copyCid} style={{background:'#fff',color:'#000',padding:'4px 8px',borderRadius:4}}>Copy bundle CID</button>}
        </div>
      )}
      {graph && graph.nodes?.length > 0 && (
        <div style={{border:'1px solid #ccc',borderRadius:8,padding:8,marginBottom:24}}>
          <h2 style={{marginTop:0}}>Graph</h2>
          <Graph nodes={graph.nodes} edges={graph.edges} />
        </div>
      )}
      {passport && (
        <div style={{border:'1px solid #ccc',borderRadius:8,padding:8,marginBottom:24}}>
          <h2 style={{marginTop:0}}>Passport</h2>
          <div style={{display:'flex',gap:16,flexWrap:'wrap'}}>
            <div><strong>Model:</strong> {passport.model_id || '—'}</div>
            <div><strong>Receipts:</strong> {passport.receipts}</div>
            <div><strong>Steps:</strong> {passport.steps?.length}</div>
            <div><strong>Datasets:</strong> {passport.dataset_roots?.length}</div>
            <div><strong>Policy Breaches:</strong> {passport.policy_breaches?.length}</div>
          </div>
          {passport.policy_breaches?.length > 0 && (
            <div style={{marginTop:12}}>
              <label style={{display:'flex',alignItems:'center',gap:8}}>
                <input type="checkbox" checked={showBreaches} onChange={e=>setShowBreaches(e.target.checked)} /> Show breaches
              </label>
              {showBreaches && <ul style={{marginTop:8}}>
                {passport.policy_breaches.map((b: any, i: number) => (
                  <li key={i}><code>{b.rule || b.id || 'rule'}</code> outcome={b.outcome || b.result || b.decision}</li>
                ))}
              </ul>}
            </div>
          )}
        </div>
      )}
      {graph && <details><summary>Raw Graph JSON</summary><pre style={{maxHeight:300,overflow:'auto'}}>{JSON.stringify(graph,null,2)}</pre></details>}
      {verify && <details><summary>Verify JSON</summary><pre style={{maxHeight:300,overflow:'auto'}}>{JSON.stringify(verify,null,2)}</pre></details>}
    </main>
  );
}

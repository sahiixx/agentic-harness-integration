'use client';

import { useState } from 'react';
import { runEndpoint } from '@/lib/api';

type Spec = { kind: 'pattern' | 'bridge'; path: string; label: string; sample: unknown };

const SPECS: Spec[] = [
  { kind: 'pattern', path: 'chain', label: 'Chain', sample: { prompts: ['Hello', 'World'], temperature: 0.7 } },
  { kind: 'pattern', path: 'route', label: 'Route', sample: { input_text: 'I want to buy', routes: { sales: 'You are sales', support: 'You are support' } } },
  { kind: 'pattern', path: 'parallel', label: 'Parallel', sample: { tasks: ['Task A', 'Task B'], temperature: 0.7 } },
  { kind: 'pattern', path: 'orchestrate', label: 'Orchestrate', sample: { objective: 'Write a blog post about AI', pre_analyze: false } },
  { kind: 'pattern', path: 'evaluate_optimize', label: 'Eval-Optimize', sample: { prompt: 'Write a headline', rubric: { clarity: 1 }, max_iterations: 3 } },
  { kind: 'pattern', path: 'react', label: 'ReAct', sample: { query: 'AI companies in Dubai', max_model_calls: 8 } },
  { kind: 'pattern', path: 'reflect', label: 'Reflect', sample: { draft: 'Original draft text', criteria: ['concise', 'clear'] } },
  { kind: 'bridge', path: 'nexus/enrich', label: 'NEXUS Enrich', sample: { name: 'John Doe', email: 'john@acme.com', company: 'Acme Corp', title: 'CEO' } },
  { kind: 'bridge', path: 'gapclaw/hunt', label: 'GapClaw Hunt', sample: { query: 'property developers needing CRM', max_model_calls: 8 } },
  { kind: 'bridge', path: 'sara/generate', label: 'SARA Generate', sample: { topic: 'Dubai Marina investment guide', rubric: {}, max_iterations: 3 } },
  { kind: 'bridge', path: 'gapsolver/discover', label: 'GapSolver Discover', sample: { industry: 'real_estate', location: 'Dubai', top_n: 5 } },
];

export default function Console() {
  const [selected, setSelected] = useState(SPECS[0]);
  const [payload, setPayload] = useState(JSON.stringify(SPECS[0].sample, null, 2));
  const [token, setToken] = useState('');
  const [result, setResult] = useState('');
  const [error, setError] = useState('');
  const [latency, setLatency] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSelect = (i: number) => {
    const spec = SPECS[i];
    setSelected(spec);
    setPayload(JSON.stringify(spec.sample, null, 2));
    setResult(''); setError(''); setLatency(null);
  };

  const handleSubmit = async () => {
    setLoading(true); setError(''); setResult(''); setLatency(null);
    const started = performance.now();
    try {
      const data = await runEndpoint(selected.kind, selected.path, JSON.parse(payload), token);
      setResult(JSON.stringify(data, null, 2));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
    setLatency(Math.round(performance.now() - started));
    setLoading(false);
  };

  return (
    <div className="card">
      <h2>Harness Console</h2>
      <p className="card-sub">POST {selected.kind === 'bridge' ? selected.path : `pattern/${selected.path}`}</p>

      <label className="lbl">Endpoint</label>
      <select className="inp" value={SPECS.indexOf(selected)} onChange={(e) => handleSelect(Number(e.target.value))}>
        {SPECS.map((s, i) => (
          <option key={s.path} value={i}>
            {s.kind === 'bridge' ? '★ ' : ''}{s.label} — {s.path}
          </option>
        ))}
      </select>

      <label className="lbl">Bearer token (optional — JWT-secured endpoints)</label>
      <input className="inp mono" value={token} onChange={(e) => setToken(e.target.value)} placeholder="paste JWT or leave empty" />

      <label className="lbl">Payload</label>
      <textarea className="inp mono" value={payload} onChange={(e) => setPayload(e.target.value)} rows={8} />

      <div className="row">
        <button className="btn btn-primary" onClick={handleSubmit} disabled={loading}>
          {loading ? 'Running…' : 'Run'}
        </button>
        {latency !== null && !error && (
          <span className="badge status-live">{(latency / 1000).toFixed(2)}s</span>
        )}
      </div>

      {error && <pre className="err">{error}</pre>}
      {result && !error && <pre className="out">{result}</pre>}
    </div>
  );
}
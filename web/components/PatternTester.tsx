'use client';

import { useState } from 'react';
import { postPattern } from '@/lib/api';

const PATTERNS = [
  { label: 'Chain', value: 'chain', default: { prompts: ['Hello', 'World'], temperature: 0.7 } },
  { label: 'Route', value: 'route', default: { input_text: 'I want to buy', routes: { sales: 'You are sales', support: 'You are support' } } },
  { label: 'Parallel', value: 'parallel', default: { tasks: ['Task A', 'Task B'], temperature: 0.7 } },
  { label: 'Orchestrate', value: 'orchestrate', default: { objective: 'Write a blog post about AI', pre_analyze: false } },
  { label: 'Evaluate Optimize', value: 'evaluate_optimize', default: { prompt: 'Write a headline', rubric: { clarity: 1 }, max_iterations: 3 } },
  { label: 'ReAct', value: 'react', default: { query: 'AI companies in Dubai', max_model_calls: 8 } },
  { label: 'Reflect', value: 'reflect', default: { draft: 'Original draft text', criteria: ['concise', 'clear'] } },
];

export default function PatternTester() {
  const [selected, setSelected] = useState(PATTERNS[0].value);
  const [payload, setPayload] = useState(JSON.stringify(PATTERNS[0].default, null, 2));
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const handlePatternChange = (value: string) => {
    setSelected(value);
    const pattern = PATTERNS.find((p) => p.value === value);
    if (pattern) setPayload(JSON.stringify(pattern.default, null, 2));
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const data = await postPattern(selected, JSON.parse(payload));
      setResult(JSON.stringify(data, null, 2));
    } catch (e) {
      setResult(String(e));
    }
    setLoading(false);
  };

  return (
    <div className="card">
      <h2>Pattern Tester</h2>
      <select
        value={selected}
        onChange={(e) => handlePatternChange(e.target.value)}
        style={{ padding: 8, borderRadius: 6, marginRight: 8 }}
      >
        {PATTERNS.map((p) => (
          <option key={p.value} value={p.value}>{p.label}</option>
        ))}
      </select>
      <button className="btn" onClick={handleSubmit} disabled={loading}>
        {loading ? 'Running...' : 'Run'}
      </button>
      <textarea
        value={payload}
        onChange={(e) => setPayload(e.target.value)}
        rows={6}
        style={{ width: '100%', marginTop: 12, padding: 10, borderRadius: 6, fontFamily: 'monospace', background: '#0f172a', color: '#e2e8f0', border: '1px solid #334155' }}
      />
      {result && (
        <pre style={{ marginTop: 12, padding: 12, background: '#0f172a', borderRadius: 6, overflow: 'auto', maxHeight: 300, fontSize: 12 }}>
          {result}
        </pre>
      )}
    </div>
  );
}

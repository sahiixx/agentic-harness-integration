'use client';

import { useEffect, useState } from 'react';
import { fetchHealth, fetchEscalated, createToken } from '@/lib/api';

export default function SidePanel() {
  const [status, setStatus] = useState<'loading' | 'ok' | 'error'>('loading');
  const [version, setVersion] = useState('');
  const [token, setToken] = useState('');
  const [escalated, setEscalated] = useState<unknown[] | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetchHealth()
      .then((d) => {
        setStatus(d.status === 'ok' ? 'ok' : 'error');
        setVersion(d.version || '');
      })
      .catch(() => setStatus('error'));
  }, []);

  const issueToken = async () => {
    setBusy(true);
    try {
      const r = await createToken('dashboard');
      setToken(r.token);
      const esc = await fetchEscalated(r.token);
      setEscalated((esc as { escalated: unknown[] }).escalated);
    } catch {
      setEscalated([]);
    }
    setBusy(false);
  };

  return (
    <div className="stack">
      <div className="card">
        <h2>API Health</h2>
        <p className="card-sub">Service status</p>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="dot" style={{ background: status === 'ok' ? 'var(--ok)' : 'var(--err)' }} />
          <span className="mono">
            {status === 'loading' ? 'CHECKING' : status === 'ok' ? 'ONLINE' : 'OFFLINE'}
          </span>
          {version && <span className="meta mono">v{version}</span>}
        </div>
        <div style={{ marginTop: 18 }}>
          <button className="btn btn-ghost" onClick={issueToken} disabled={busy}>
            {busy ? 'Issuing…' : token ? 'JWT issued ✓' : 'Issue JWT + load escalations'}
          </button>
        </div>
        {token && (
          <p className="meta mono" style={{ wordBreak: 'break-all', fontSize: 10, marginTop: 10 }}>
            {token.slice(0, 56)}…
          </p>
        )}
      </div>

      <div className="card">
        <h2>Escalated Traces</h2>
        <p className="card-sub">Human review queue</p>
        {escalated === null && <p className="meta">Not loaded yet.</p>}
        {escalated !== null && escalated.length === 0 && (
          <span className="badge status-live">NONE — ALL CLEAN</span>
        )}
        {escalated !== null && escalated.length > 0 && (
          <div style={{ marginTop: 12 }}>
            {escalated.map((t, i) => (
              <div key={i} className="trace-row">
                <code>{String((t as { trace_id?: string }).trace_id ?? `trace_${i}`)}</code>
                <span className="badge status-err">{String((t as { status?: string }).status ?? '')}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
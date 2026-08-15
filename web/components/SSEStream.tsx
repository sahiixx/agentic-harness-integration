'use client';

import { useEffect, useState } from 'react';
import { createEventSource } from '@/lib/api';

export default function SSEStream() {
  const [events, setEvents] = useState<string[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const traceId = `t_${Date.now()}`;
    const es = createEventSource(traceId);

    es.onopen = () => setConnected(true);
    es.onmessage = (e) => {
      setEvents((prev) => [...prev, e.data]);
    };
    es.onerror = () => {
      setConnected(false);
      es.close();
    };

    return () => es.close();
  }, []);

  return (
    <div className="card">
      <h2>SSE Stream Demo</h2>
      <p>
        Connection:{' '}
        <span className={connected ? 'status-ok' : 'status-error'}>
          {connected ? 'CONNECTED' : 'DISCONNECTED'}
        </span>
      </p>
      <div style={{ maxHeight: 200, overflow: 'auto', background: '#0f172a', padding: 12, borderRadius: 6, fontSize: 12 }}>
        {events.length === 0 && <em>No events yet...</em>}
        {events.map((e, i) => (
          <div key={i} style={{ marginBottom: 4 }}>→ {e}</div>
        ))}
      </div>
    </div>
  );
}

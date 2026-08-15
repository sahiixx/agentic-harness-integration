'use client';

import { useEffect, useState } from 'react';
import { fetchHealth } from '@/lib/api';

export default function HealthCard() {
  const [status, setStatus] = useState<'loading' | 'ok' | 'error'>('loading');
  const [version, setVersion] = useState('');

  useEffect(() => {
    fetchHealth()
      .then((d) => {
        setStatus(d.status === 'ok' ? 'ok' : 'error');
        setVersion(d.version || '');
      })
      .catch(() => setStatus('error'));
  }, []);

  return (
    <div className="card">
      <h2>API Health</h2>
      <p>
        Status:{' '}
        <span className={`status-${status}`}>
          {status === 'loading' ? 'Checking...' : status.toUpperCase()}
        </span>
      </p>
      {version && <p>Version: {version}</p>}
    </div>
  );
}

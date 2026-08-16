'use client';

import { useEffect, useState } from 'react';

type HealthStatus = Record<string, { status: string; last_check: number; meta: any }>;
type RepoSummary = { total: number; tiers: number; counts: Record<string, number>; integrated: string[] };

export default function Dashboard() {
  const [data, setData] = useState<{
    health: HealthStatus;
    grok_session_log: string;
    repos: RepoSummary;
    free_providers: Record<string, any>;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchDashboard() {
      try {
        const res = await fetch('/api/harness/dashboard');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        setData(json);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load dashboard');
      }
    }
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 30000); // refresh every 30s
    return () => clearInterval(interval);
  }, []);

  if (error) return <div className="dash-error">Error: {error}</div>;
  if (!data) return <div className="dash-loading">Loading dashboard…</div>;

  const { health, grok_session_log, repos, free_providers } = data;

  const healthy = Object.values(health).filter(h => h.status === 'healthy').length;
  const total = Object.keys(health).length;

  return (
    <div className="dash-wrap">
      <div className="dash-grid">
        <div className="dash-card dash-health">
          <h3>Subsystems</h3>
          <div className="dash-metric">
            <span className="dash-value">{healthy}/{total}</span>
            <span className="dash-label">healthy</span>
          </div>
          <div className="dash-list">
            {Object.entries(health).map(([name, info]) => (
              <div key={name} className={`dash-item ${info.status.startsWith('healthy') ? 'ok' : 'down'}`}>
                <span className="dash-name">{name}</span>
                <span className="dash-status">{info.status}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="dash-card dash-grok">
          <h3>Grok 5hr Session</h3>
          <pre className="dash-log">{grok_session_log}</pre>
        </div>

        <div className="dash-card dash-repos">
          <h3>Upgrade Repos</h3>
          <div className="dash-metric">
            <span className="dash-value">{repos.total}</span>
            <span className="dash-label">repos</span>
          </div>
          <div className="dash-repo-tiers">
            {Object.entries(repos.counts).map(([tier, count]) => (
              <div key={tier} className="dash-tier">
                <span className="dash-tier-name">{tier}</span>
                <span className="dash-tier-count">{count}</span>
              </div>
            ))}
          </div>
          <div className="dash-integrated">
            Integrated: {repos.integrated.join(', ') || 'none'}
          </div>
        </div>

        <div className="dash-card dash-providers">
          <h3>Free Providers</h3>
          <div className="dash-provider-list">
            {Object.entries(free_providers).map(([name, cfg]) => (
              <div key={name} className="dash-provider">
                <span className={`dash-prov-name ${cfg.configured ? 'ok' : ''}`}>
                  {name} {cfg.configured ? '✓' : '✗'}
                </span>
                <span className="dash-prov-model">{cfg.models?.grok || '—'}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
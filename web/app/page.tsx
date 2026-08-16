'use client';

import { useEffect, useState } from 'react';
import Console from '@/components/Console';
import SidePanel from '@/components/SidePanel';
import Dashboard from '@/components/Dashboard';
import './globals.css';

type Tier = { name: string; repo: string; url: string; why: string; integrates_with: string; status: string; version?: string; stars?: string };
type RepoData = { total: number; tiers: number; counts: Record<string, number>; integrated: string[] };

function useScrollEffects() {
  useEffect(() => {
    const nav = document.getElementById('nav');
    const bar = document.getElementById('scrollProgress');
    const onScroll = () => {
      if (nav) nav.classList.toggle('nav-scrolled', window.scrollY > 24);
      if (bar) {
        const h = document.documentElement.scrollHeight - window.innerHeight;
        bar.style.transform = `scaleX(${h > 0 ? window.scrollY / h : 0})`;
      }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener('scroll', onScroll);
  }, []);
}

function useFx() {
  useEffect(() => {
    const canvas = document.getElementById('fx') as HTMLCanvasElement | null;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let raf = 0;
    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const pts: { x: number; y: number; vx: number; vy: number }[] = [];
    for (let i = 0; i < 42; i++) {
      pts.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
      });
    }

    const step = () => {
      if (!ctx || !canvas) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (const p of pts) {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 1.2, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(34, 211, 238, .35)';
        ctx.fill();
      }
      for (let i = 0; i < pts.length; i++) {
        for (let j = i + 1; j < pts.length; j++) {
          const dx = pts[i].x - pts[j].x;
          const dy = pts[i].y - pts[j].y;
          const d = Math.hypot(dx, dy);
          if (d < 130) {
            ctx.beginPath();
            ctx.moveTo(pts[i].x, pts[i].y);
            ctx.lineTo(pts[j].x, pts[j].y);
            ctx.strokeStyle = `rgba(139, 92, 255, ${(1 - d / 130) * 0.25})`;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      }
      raf = requestAnimationFrame(step);
    };

    if (!reduced) raf = requestAnimationFrame(step);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', resize);
    };
  }, []);
}

export default function Home() {
  useScrollEffects();
  useFx();
  const [repos, setRepos] = useState<Record<string, Tier[]> | null>(null);
  const [repoMeta, setRepoMeta] = useState<RepoData | null>(null);

  useEffect(() => {
    fetch('/api/harness/repos')
      .then((r) => r.json())
      .then(setRepos)
      .catch(() => {});
    fetch('/api/harness/repos/summary')
      .then((r) => r.json())
      .then(setRepoMeta)
      .catch(() => {});
  }, []);

  const tierLabels: Record<string, string> = {
    tier1_xai_native: 'Tier 1 · xAI Native',
    tier2_agent_frameworks: 'Tier 2 · Agent Frameworks',
    tier3_specialized: 'Tier 3 · Specialized',
  };

  return (
    <>
      <header className="nav" id="nav">
        <a className="nav-brand" href="#top">
          <span className="nav-mark">◆</span><span>SAHIIX</span>
        </a>
        <nav className="nav-links">
          <a href="#console" className="nav-active">Console</a>
          <a href="#systems">Systems</a>
          <a href="#upgrades">Upgrades</a>
          <a href="#free-grok">Free Grok</a>
          <a href="#dashboard">Dashboard</a>
          <a href="https://sahiix-portfolio.pages.dev" target="_blank" rel="noopener">Portfolio ↗</a>
        </nav>
        <a className="nav-cta" href="#console">Live API</a>
      </header>

      <main id="top">
        <section className="hero">
          <p className="eyebrow reveal">
            <span className="dot"></span>
            <span id="availability">Agentic Harness Bridge</span>
            <span>· v6.0.0</span>
          </p>
          <h1 className="hero-title">
            <span className="hero-name">HARNESS</span>
          </h1>
          <p className="hero-sub">
            Patterns, domain bridges and observability behind one console —
            live, not mockups. Run any endpoint against the running API.
          </p>
        </section>

        <section className="section" id="console">
          <div className="section-head">
            <p className="section-kicker">Control surface</p>
            <h2 className="section-title">Run the harness.</h2>
            <p className="section-sub">Pick an endpoint, edit the payload, execute. Every pattern and bridge in the API.</p>
          </div>
          <div className="grid">
            <Console />
            <SidePanel />
          </div>
        </section>

        <section className="section" id="systems">
          <div className="section-head">
            <p className="section-kicker">Connected systems</p>
            <h2 className="section-title">One harness, every build.</h2>
            <p className="section-sub">The harness links every live SAHIIX build — NEXUS, OS, Jarvis, OPA — behind one console.</p>
          </div>
          <div className="system-grid">
            {[
              { name: 'SAHIIX OS', url: 'https://sahiixx-os.pages.dev', note: 'AI-native OS shell — v4.3 live on Cloudflare + Neon.', accent: '#ff4d4d' },
              { name: 'NEXUS', url: 'https://sahiixx-os.pages.dev/nexus', note: 'Live Dubai deal engine + WhatsApp loop.', accent: '#f59e0b' },
              { name: 'Jarvis', url: 'https://sahiixx-os.pages.dev/jarvis', note: 'Voice agent that controls the machine.', accent: '#7c5cff' },
              { name: 'OPA', url: 'http://127.0.0.1:3082/', note: 'One Person Agency — 200+ module dispatch.', accent: '#22d3ee' },
              { name: 'Portfolio', url: 'https://sahiix-portfolio.pages.dev', note: 'SAHIIX — the operator shell and case studies.', accent: '#8b5cff' },
            ].map((s) => (
              <a key={s.name} className="system-card" href={s.url} target="_blank" rel="noopener" style={{ borderLeftColor: s.accent }}>
                <h3 className="system-name">{s.name}</h3>
                <p className="system-note">{s.note}</p>
                <span className="system-link">Open <span className="system-arrow">↗</span></span>
              </a>
            ))}
          </div>
        </section>

        <section className="section" id="upgrades">
          <div className="section-head">
            <p className="section-kicker">Upgrade radar</p>
            <h2 className="section-title">Repos that max the stack.</h2>
            <p className="section-sub">
              {repoMeta ? `${repoMeta.total} curated repos across ${repoMeta.tiers} tiers. ` : ''}
              Live from the harness <code>/repos</code> registry — Grok (xAI SDK) integrated, rest staged.
            </p>
          </div>
          {repos ? (
            <div className="upgrade-wrap">
              {Object.entries(repos).map(([tier, list]) => (
                <div key={tier} className="upgrade-tier">
                  <h3 className="upgrade-tier-title">{tierLabels[tier] ?? tier}</h3>
                  <div className="upgrade-grid">
                    {list.map((r) => (
                      <a key={r.name} className="upgrade-card" href={r.url} target="_blank" rel="noopener">
                        <div className="upgrade-card-top">
                          <span className="upgrade-name">{r.name}</span>
                          <span className={`upgrade-badge ${r.status === 'integrated' ? 'on' : ''}`}>{r.status}</span>
                        </div>
                        <p className="upgrade-why">{r.why}</p>
                        <p className="upgrade-int">{r.integrates_with}</p>
                        <span className="upgrade-repo">{r.repo} ↗</span>
                      </a>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="section-sub">Loading registry…</p>
          )}
        </section>

        <section className="section" id="free-grok">
          <div className="section-head">
            <p className="section-kicker">Free Grok access</p>
            <h2 className="section-title">Zero-cost Grok 4.x endpoints.</h2>
            <p className="section-sub">
              No xAI API key needed. Configure one free provider in PM2 env, then call <code>/grok/chat</code> (auto-fallback) or <code>/grok/free/chat</code>.
            </p>
          </div>
          <div className="free-grid">
            <div className="free-card">
              <h3>FreeTheAi <span className="free-badge">Recommended</span></h3>
              <p>60+ models incl. Grok via <code>xai/*</code> aliases. OpenAI-compatible.</p>
              <ol className="free-steps">
                <li>Join <a href="https://discord.gg/secrets" target="_blank" rel="noopener">Discord</a></li>
                <li>Run <code>/signup</code> → get API key</li>
                <li>Daily <code>/checkin</code> in Discord</li>
                <li>Set <code>FREETHEAI_API_KEY</code> in PM2 env</li>
              </ol>
              <code className="free-endpoint">Base: https://api.freetheai.xyz/v1</code>
            </div>
            <div className="free-card">
              <h3>Puter <span className="free-badge">Easiest</span></h3>
              <p>Free Grok + 100s models via OpenAI-compatible endpoint.</p>
              <ol className="free-steps">
                <li>Sign up at <a href="https://puter.com" target="_blank" rel="noopener">puter.com</a></li>
                <li>Get auth token from dashboard</li>
                <li>Set <code>PUTER_AUTH_TOKEN</code> in PM2 env</li>
              </ol>
              <code className="free-endpoint">Base: https://api.puter.com/puterai/openai/v1/</code>
            </div>
            <div className="free-card">
              <h3>token-free-gateway <span className="free-badge">Local</span></h3>
              <p>Run locally, 13 providers (Grok, Claude, Gemini, etc.). Browser cookies only.</p>
              <ol className="free-steps">
                <li><code>pip install token-free-gateway</code></li>
                <li><code>tfg start</code> (needs Chrome)</li>
                <li>Point to <code>http://localhost:8080/v1</code></li>
              </ol>
              <code className="free-endpoint">Local only — no cloud key</code>
            </div>
            <div className="free-card">
              <h3>Freeloader <span className="free-badge">Cascade</span></h3>
              <p>177+ free providers with auto-failover (Gemini, Groq, Cerebras, OpenRouter).</p>
              <ol className="free-steps">
                <li>Get free keys: Gemini, Groq, Cerebras, OpenRouter</li>
                <li>Docker: <code>docker run -p 8000:8000 freeloader</code></li>
                <li>Set keys in env</li>
              </ol>
              <code className="free-endpoint">Local gateway with cascade</code>
            </div>
          </div>
        </section>

        <section className="section" id="dashboard">
          <div className="section-head">
            <p className="section-kicker">Live dashboard</p>
            <h2 className="section-title">System pulse.</h2>
            <p className="section-sub">
              Unified view from <code>/dashboard</code> — health, Grok session, repos, providers.
            </p>
          </div>
          <Dashboard />
        </section>
      </main>

      <footer className="footer">
        <div className="footer-inner">
          <span className="nav-brand"><span className="nav-mark">◆</span> SAHIIX</span>
          <p>Agentic Harness Bridge v6.0.0 — FastAPI · Next.js · SSE.</p>
          <a href="#top" className="footer-top">Back to top ↑</a>
        </div>
      </footer>
    </>
  );
}
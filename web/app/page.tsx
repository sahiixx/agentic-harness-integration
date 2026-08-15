'use client';

import { useEffect } from 'react';
import Console from '@/components/Console';
import SidePanel from '@/components/SidePanel';
import './globals.css';

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

  return (
    <>
      <header className="nav" id="nav">
        <a className="nav-brand" href="#top">
          <span className="nav-mark">◆</span><span>SAHIIX</span>
        </a>
        <nav className="nav-links">
          <a href="#console" className="nav-active">Console</a>
          <a href="#systems">Systems</a>
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
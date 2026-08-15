import HealthCard from '@/components/HealthCard';
import PatternTester from '@/components/PatternTester';
import SSEStream from '@/components/SSEStream';
import './globals.css';

export default function Home() {
  return (
    <main style={{ maxWidth: 900, margin: '0 auto', padding: '40px 20px' }}>
      <h1 style={{ fontSize: 32, marginBottom: 8 }}>Agentic Harness Bridge</h1>
      <p style={{ color: '#94a3b8', marginBottom: 32 }}>v6.0.0 — Production integration layer</p>

      <HealthCard />
      <PatternTester />
      <SSEStream />

      <footer style={{ marginTop: 40, paddingTop: 20, borderTop: '1px solid #334155', color: '#64748b', fontSize: 12 }}>
        Built by Sahiix · Next.js 14 + FastAPI + SSE
      </footer>
    </main>
  );
}

# Agentic Harness Web — Next.js 14

Frontend for the Agentic Harness Integration Layer.

## Setup

```bash
cd web/
npm install
```

## Development

```bash
npm run dev
# Opens on http://localhost:3000
# Proxies API calls to http://localhost:8000 via next.config.js rewrites
```

## Build

```bash
npm run build
npm start
```

## Structure

- `app/page.tsx` — Dashboard with Health, Pattern Tester, SSE Stream
- `app/layout.tsx` — Root layout with dark theme
- `components/HealthCard.tsx` — Live API health check
- `components/PatternTester.tsx` — Interactive pattern runner
- `components/SSEStream.tsx` — Real-time SSE demo
- `lib/api.ts` — API client utilities

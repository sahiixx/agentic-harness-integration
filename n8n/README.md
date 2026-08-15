# n8n-nodes-agentic-harness

n8n community node for the Agentic Harness Integration Layer.

## Installation

```bash
# In your n8n custom nodes directory (usually ~/.n8n/custom/)
cd ~/.n8n/custom/
npm install /path/to/agentic-harness-integration/n8n
```

Or build from source:

```bash
cd n8n/
npm install
npm run build
```

## Credentials

1. Go to **Settings → Credentials → New**
2. Select **Agentic Harness API**
3. Enter your Bridge API base URL (e.g., `http://localhost:8000`)
4. Optional: enter API key if authentication is enabled

## Operations

Supports all 11 Bridge endpoints:
- Pattern endpoints: Chain, Route, Parallel, Orchestrate, Evaluate Optimize, ReAct, Reflect
- Domain bridges: NEXUS Enrich, GapClaw Hunt, SARA Generate, GapSolver Discover

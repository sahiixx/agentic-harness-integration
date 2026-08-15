-- SAHIIX Production Database Initialization
-- Run via: psql -h localhost -U sahiix -d sahiix -f init-db.sql

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Core tables
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    scopes TEXT[] DEFAULT '{}',
    rate_limit INTEGER DEFAULT 100,
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS traces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trace_id VARCHAR(64) UNIQUE NOT NULL,
    pattern VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    input_payload JSONB DEFAULT '{}',
    output_payload JSONB DEFAULT '{}',
    model_calls INTEGER DEFAULT 0,
    cost_usd DECIMAL(10,6) DEFAULT 0,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    api_key_id UUID REFERENCES api_keys(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_traces_user_id ON traces(user_id);
CREATE INDEX idx_traces_created_at ON traces(created_at DESC);
CREATE INDEX idx_traces_pattern ON traces(pattern);

CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    company VARCHAR(255),
    title VARCHAR(255),
    linkedin VARCHAR(255),
    enriched_data JSONB DEFAULT '{}',
    source VARCHAR(50),
    score INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'new',
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_source ON leads(source);

CREATE TABLE IF NOT EXISTS deals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    property_id VARCHAR(100),
    property_title VARCHAR(255),
    property_price DECIMAL(20,2),
    property_currency VARCHAR(10) DEFAULT 'AED',
    commission_rate DECIMAL(5,4) DEFAULT 0.02,
    commission_amount DECIMAL(20,2),
    probability DECIMAL(5,4) DEFAULT 0.1,
    stage VARCHAR(50) DEFAULT 'prospecting',
    expected_close_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_deals_lead_id ON deals(lead_id);
CREATE INDEX idx_deals_stage ON deals(stage);

CREATE TABLE IF NOT EXISTS outreach_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deal_id UUID REFERENCES deals(id) ON DELETE CASCADE,
    channel VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    template_id VARCHAR(50),
    content TEXT,
    status VARCHAR(20) DEFAULT 'sent',
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    response_at TIMESTAMPTZ,
    response_content TEXT
);

CREATE INDEX idx_outreach_deal_id ON outreach_logs(deal_id);
CREATE INDEX idx_outreach_sent_at ON outreach_logs(sent_at DESC);

CREATE TABLE IF NOT EXISTS grok_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(64) UNIQUE NOT NULL,
    prompt TEXT NOT NULL,
    response TEXT,
    model VARCHAR(100),
    provider VARCHAR(50),
    tokens_prompt INTEGER,
    tokens_completion INTEGER,
    tokens_total INTEGER,
    cost_usd DECIMAL(10,6),
    latency_ms INTEGER,
    status VARCHAR(20) DEFAULT 'completed',
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_grok_sessions_created_at ON grok_sessions(created_at DESC);

CREATE TABLE IF NOT EXISTS swarm_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id VARCHAR(64) UNIQUE NOT NULL,
    prompt TEXT NOT NULL,
    providers JSONB DEFAULT '[]',
    results JSONB DEFAULT '[]',
    consensus TEXT,
    best_provider VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_swarm_runs_created_at ON swarm_runs(created_at DESC);

CREATE TABLE IF NOT EXISTS health_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    latency_ms INTEGER,
    details JSONB DEFAULT '{}',
    checked_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_health_checks_service ON health_checks(service_name);
CREATE INDEX idx_health_checks_checked_at ON health_checks(checked_at DESC);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    old_value JSONB,
    new_value JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_created_at ON audit_logs(created_at DESC);

-- Functions
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_deals_updated_at BEFORE UPDATE ON deals FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Default admin user (password: changeme - change on first login!)
INSERT INTO users (email, password_hash, full_name, role)
VALUES ('admin@sahiix.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S', 'System Admin', 'admin')
ON CONFLICT (email) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sahiix;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sahiix;
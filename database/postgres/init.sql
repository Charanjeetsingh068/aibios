-- AI-BOS Enterprise Database Initialization Schema
-- Target: PostgreSQL 15

-- Enable UUID Extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: System Audit Logs (RBAC compliance)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    target_component VARCHAR(100) NOT NULL,
    request_details JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index audit logs for rapid querying
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at);

-- Table: System Roles
CREATE TABLE IF NOT EXISTS system_roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Seed Default Roles
INSERT INTO system_roles (name, description) VALUES
('administrator', 'Full platform write, read, and deployment privileges'),
('manager', 'Workflow administration and audit analysis capability'),
('agent', 'AI Agent cognitive runtime authorization'),
('auditor', 'Read-only access to audit logs and trace histories'),
('developer', 'Write access to connectors and routing rules configurations')
ON CONFLICT (name) DO NOTHING;

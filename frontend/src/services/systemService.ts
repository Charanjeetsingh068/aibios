export interface SystemStatus {
  backend: string;
  version: string;
  environment: string;
  uptime: string;
  python_version: string;
  fastapi: string;
}

export interface SystemInfo {
  app_name: string;
  app_version: string;
  os: string;
  hostname: string;
  current_time: string;
  timezone: string;
  memory: string;
  cpu_count: number;
  platform: string;
}

export interface DatabaseConnection {
  connected: boolean;
}

export interface DatabaseStatus {
  postgres: DatabaseConnection;
  mongodb: DatabaseConnection;
  redis: DatabaseConnection;
  qdrant: DatabaseConnection;
}

export interface AgentStatus {
  supervisor_agent: string;
  planner_agent: string;
  executor_agent: string;
  developer_agent: string;
}

const API_BASE = '/api/v1/system';

export async function fetchSystemStatus(): Promise<SystemStatus> {
  const res = await fetch(`${API_BASE}/status`);
  if (!res.ok) {
    throw new Error(`Failed to fetch system status: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchSystemInfo(): Promise<SystemInfo> {
  const res = await fetch(`${API_BASE}/info`);
  if (!res.ok) {
    throw new Error(`Failed to fetch system info: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchDatabaseStatus(): Promise<DatabaseStatus> {
  const res = await fetch(`${API_BASE}/database`);
  if (!res.ok) {
    throw new Error(`Failed to fetch database status: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchAgentStatus(): Promise<AgentStatus> {
  const res = await fetch(`${API_BASE}/agents`);
  if (!res.ok) {
    throw new Error(`Failed to fetch agent status: ${res.statusText}`);
  }
  return res.json();
}

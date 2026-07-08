import axiosInstance from './axiosInstance';

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
  latency_ms?: number;
  version?: string;
  engine?: string;
}

export interface HealthStatus {
  status: string;
  environment: string;
  backend: string;
  cpu: { percent: number; cores: number };
  memory: { percent: number; used_gb: number; total_gb: number };
  disk: { percent: number; used_gb: number; total_gb: number };
  workers: number;
  dependencies: Record<string, string>;
  integrations?: Record<string, { status: 'configured' | 'not_configured'; missing: string[] }>;
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

export async function fetchSystemStatus(): Promise<SystemStatus> {
  const response = await axiosInstance.get('/system/status');
  return response.data;
}

export async function fetchSystemInfo(): Promise<SystemInfo> {
  const response = await axiosInstance.get('/system/info');
  return response.data;
}

export async function fetchDatabaseStatus(): Promise<DatabaseStatus> {
  const response = await axiosInstance.get('/system/database');
  return response.data;
}

export async function fetchAgentStatus(): Promise<AgentStatus> {
  const response = await axiosInstance.get('/system/agents');
  return response.data;
}

export async function fetchHealth(): Promise<HealthStatus> {
  const response = await axiosInstance.get('/health');
  return response.data;
}

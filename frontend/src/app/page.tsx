"use client";

import { useEffect, useState } from 'react';
import { 
  Sun, 
  Moon, 
  Server, 
  Activity, 
  Cpu, 
  Database, 
  Network, 
  Shield
} from 'lucide-react';
import '../styles/dashboard.css';
import { 
  fetchSystemStatus, 
  fetchSystemInfo, 
  fetchDatabaseStatus, 
  fetchAgentStatus,
  SystemStatus,
  SystemInfo,
  DatabaseStatus,
  AgentStatus
} from '../services/systemService';

export default function Dashboard() {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Dynamic API states
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [info, setInfo] = useState<SystemInfo | null>(null);
  const [dbStatus, setDbStatus] = useState<DatabaseStatus | null>(null);
  const [agents, setAgents] = useState<AgentStatus | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [userProfile, setUserProfile] = useState<any>(null);

  // Redirect to login if not authenticated
  useEffect(() => {
    const token = localStorage.getItem('aibos_access_token');
    if (!token) {
      window.location.href = '/auth/login';
      return;
    }

    import('../services/authService').then(({ getMe }) => {
      getMe().then(profile => {
        setUserProfile(profile);
      }).catch(() => {
        window.location.href = '/auth/login';
      });
    });
  }, []);

  // Initialize theme from HTML attribute
  useEffect(() => {
    const docTheme = document.documentElement.getAttribute('data-theme') as 'light' | 'dark';
    if (docTheme) {
      setTheme(docTheme);
    }
  }, []);

  // Fetch all endpoints concurrently
  const loadDashboardData = async () => {
    try {
      setIsError(false);
      // Show skeleton loading if there is no previous data or we are retrying after an error
      if (!status || isError) {
        setIsLoading(true);
      }

      const [statusData, infoData, dbData, agentsData] = await Promise.all([
        fetchSystemStatus(),
        fetchSystemInfo(),
        fetchDatabaseStatus(),
        fetchAgentStatus()
      ]);

      setStatus(statusData);
      setInfo(infoData);
      setDbStatus(dbData);
      setAgents(agentsData);
      setIsError(false);
    } catch (err: any) {
      console.error("Dashboard API query failed:", err);
      setIsError(true);
      setErrorMessage(err?.message || "Could not establish connection to the FastAPI backend API.");
      
      // Clear data to enforce safe states
      setStatus(null);
      setInfo(null);
      setDbStatus(null);
      setAgents(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 10000); // refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    document.documentElement.setAttribute('data-theme', nextTheme);
    localStorage.setItem('aibos-theme', nextTheme);
  };

  const getIndicatorClass = (connected: boolean | undefined) => {
    if (connected === true) return 'online';
    if (connected === false) return 'offline';
    return 'unknown';
  };

  return (
    <div className="dashboard-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="logo-container">
          <div className="logo-icon">Ω</div>
          <span className="logo-text">AI-BOS</span>
        </div>
        
        <nav style={{ display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
          <ul className="nav-list">
            <li>
              <button 
                onClick={() => setActiveTab('dashboard')} 
                className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
                style={{ width: '100%', textAlign: 'left' }}
              >
                <Cpu size={18} />
                Dashboard
              </button>
            </li>
            <li>
              <button 
                onClick={() => setActiveTab('agents')} 
                className={`nav-item ${activeTab === 'agents' ? 'active' : ''}`}
                style={{ width: '100%', textAlign: 'left' }}
              >
                <Network size={18} />
                Multi-Agent Flows
              </button>
            </li>
            <li>
              <button 
                onClick={() => setActiveTab('databases')} 
                className={`nav-item ${activeTab === 'databases' ? 'active' : ''}`}
                style={{ width: '100%', textAlign: 'left' }}
              >
                <Database size={18} />
                Databases & Indexes
              </button>
            </li>
            <li>
              <button 
                onClick={() => setActiveTab('security')} 
                className={`nav-item ${activeTab === 'security' ? 'active' : ''}`}
                style={{ width: '100%', textAlign: 'left' }}
              >
                <Shield size={18} />
                Security & Audits
              </button>
            </li>
          </ul>
        </nav>
        
        <div style={{ marginTop: 'auto', borderTop: '1px solid var(--border-color)', paddingTop: 'var(--space-4)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <div className={status?.backend === 'online' ? "pulse-dot" : ""} style={{ backgroundColor: status?.backend === 'online' ? 'var(--success)' : 'var(--danger)' }}></div>
            <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-secondary)' }}>
              {status?.backend === 'online' ? 'Backend Connected' : 'Backend Disconnected'}
            </span>
          </div>
        </div>
      </aside>

      {/* Main Panel */}
      <main className="main-content">
        <header className="header">
          <div className="header-title-container">
            <h2>AI-BOS Enterprise Console</h2>
            <span className="header-subtitle">Phase 1 — Core Infrastructure Integration</span>
          </div>
          
          <div className="header-actions">
            <button 
              onClick={toggleTheme} 
              className="theme-toggle-btn"
              title="Toggle Light/Dark Theme"
              aria-label="Toggle Theme"
            >
              {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
            </button>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <button
                onClick={() => window.location.href = '/profile'}
                title="User Account Settings"
                style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 'var(--font-xs)', fontWeight: 'bold', color: 'var(--text-secondary)', cursor: 'pointer' }}
              >
                {userProfile ? `${userProfile.first_name[0]}${userProfile.last_name[0]}` : 'U'}
              </button>
              <button
                onClick={async () => {
                  const { logout } = await import('../services/authService');
                  await logout();
                  window.location.href = '/auth/login';
                }}
                style={{ fontSize: 'var(--font-xs)', color: 'var(--danger)', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 'var(--weight-semibold)' }}
              >
                Sign Out
              </button>
            </div>
          </div>
        </header>

        <div className="page-body animate-fade-in">
          {/* Error / Offline Banner */}
          {isError && (
            <div className="error-container">
              <div className="error-title">Offline</div>
              <div className="error-msg">{errorMessage}</div>
              <button className="retry-btn" onClick={loadDashboardData}>
                Retry Connection
              </button>
            </div>
          )}

          {activeTab === 'dashboard' && (
            <>
              {/* Metrics Row */}
              <div className="metrics-grid">
                {isLoading ? (
                  <>
                    <div className="card skeleton-card">
                      <div className="skeleton-line title"></div>
                      <div className="skeleton-line value"></div>
                      <div className="skeleton-line desc"></div>
                    </div>
                    <div className="card skeleton-card">
                      <div className="skeleton-line title"></div>
                      <div className="skeleton-line value"></div>
                      <div className="skeleton-line desc"></div>
                    </div>
                    <div className="card skeleton-card">
                      <div className="skeleton-line title"></div>
                      <div className="skeleton-line value"></div>
                      <div className="skeleton-line desc"></div>
                    </div>
                    <div className="card skeleton-card">
                      <div className="skeleton-line title"></div>
                      <div className="skeleton-line value"></div>
                      <div className="skeleton-line desc"></div>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="card">
                      <div className="card-title">Backend Status</div>
                      <div className="card-value" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                        {(status?.backend || 'OFFLINE').toUpperCase()}
                      </div>
                      <div className="card-desc">
                        <Activity size={12} />
                        Uptime: {status?.uptime || 'N/A'}
                      </div>
                    </div>

                    <div className="card">
                      <div className="card-title">Environment & Version</div>
                      <div className="card-value" style={{ fontSize: 'var(--font-xl)', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        <div>Env: {(status?.environment || 'N/A').toUpperCase()}</div>
                        <div style={{ fontSize: 'var(--font-sm)', color: 'var(--text-secondary)' }}>Version: {status?.version || 'N/A'}</div>
                      </div>
                      <div className="card-desc">
                        <Cpu size={12} />
                        Python {status?.python_version || 'N/A'}
                      </div>
                    </div>

                    <div className="card">
                      <div className="card-title">FastAPI Engine</div>
                      <div className="card-value">{(status?.fastapi || 'OFFLINE').toUpperCase()}</div>
                      <div className="card-desc">
                        <Server size={12} />
                        Asynchronous REST Gateway
                      </div>
                    </div>

                    <div className="card">
                      <div className="card-title">Agent Deployment</div>
                      <div className="card-value" style={{ fontSize: 'var(--font-xl)', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        <div>Supervisor: {agents?.supervisor_agent || 'N/A'}</div>
                        <div style={{ fontSize: 'var(--font-xs)', color: 'var(--text-secondary)' }}>Executor: {agents?.executor_agent || 'N/A'}</div>
                      </div>
                      <div className="card-desc">
                        <Network size={12} />
                        LangGraph Node Registry
                      </div>
                    </div>
                  </>
                )}
              </div>

              {/* Dynamic Health Grid */}
              <div className="card">
                <h3 style={{ marginBottom: 'var(--space-2)' }}>Database Health Integrations</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-sm)', marginBottom: 'var(--space-4)' }}>
                  Active connections parsed from environment variables. Local service connections verify Postgres, MongoDB, Redis, and Qdrant.
                </p>
                {isLoading ? (
                  <div className="skeleton-grid">
                    <div className="skeleton-item"></div>
                    <div className="skeleton-item"></div>
                    <div className="skeleton-item"></div>
                    <div className="skeleton-item"></div>
                  </div>
                ) : (
                  <div className="health-grid">
                    <div className="health-item">
                      <span className="health-item-name">PostgreSQL (Relational)</span>
                      <span className={`health-indicator ${getIndicatorClass(dbStatus?.postgres?.connected)}`}></span>
                    </div>
                    <div className="health-item">
                      <span className="health-item-name">MongoDB (Document)</span>
                      <span className={`health-indicator ${getIndicatorClass(dbStatus?.mongodb?.connected)}`}></span>
                    </div>
                    <div className="health-item">
                      <span className="health-item-name">Redis (Cache/Broker)</span>
                      <span className={`health-indicator ${getIndicatorClass(dbStatus?.redis?.connected)}`}></span>
                    </div>
                    <div className="health-item">
                      <span className="health-item-name">Qdrant (Vector DB)</span>
                      <span className={`health-indicator ${getIndicatorClass(dbStatus?.qdrant?.connected)}`}></span>
                    </div>
                  </div>
                )}
              </div>

              {/* Dynamic Orchestration Pipeline Blueprint */}
              <div className="card">
                <h3 style={{ marginBottom: 'var(--space-4)' }}>Orchestration Pipeline Blueprint</h3>
                <div className="agent-flow-container">
                  <div className="agent-nodes-wrapper">
                    <div className={`agent-node ${status?.fastapi === 'running' ? 'active' : ''}`}>
                      <div className="agent-node-title">API Gateway</div>
                      <div className="agent-node-status">{status?.fastapi === 'running' ? 'FastAPI Active' : 'Offline'}</div>
                    </div>
                    <div className={`connector-line ${agents?.supervisor_agent === 'Running' ? 'active' : ''}`}></div>
                    <div className={`agent-node ${agents?.supervisor_agent === 'Running' ? 'active' : ''}`}>
                      <div className="agent-node-title">Supervisor Node</div>
                      <div className="agent-node-status">{agents?.supervisor_agent || 'Not Installed'}</div>
                    </div>
                    <div className={`connector-line ${agents?.executor_agent === 'Running' ? 'active' : ''}`}></div>
                    <div className={`agent-node ${agents?.executor_agent === 'Running' ? 'active' : ''}`}>
                      <div className="agent-node-title">Executor Agents</div>
                      <div className="agent-node-status">{agents?.executor_agent || 'Not Installed'}</div>
                    </div>
                    <div className={`connector-line ${dbStatus?.qdrant?.connected ? 'active' : ''}`}></div>
                    <div className={`agent-node ${dbStatus?.qdrant?.connected ? 'active' : ''}`}>
                      <div className="agent-node-title">Vector Memory</div>
                      <div className="agent-node-status">{dbStatus?.qdrant?.connected ? 'Qdrant Active' : 'Offline'}</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* System Health Specifications */}
              <div className="card">
                <h3 style={{ marginBottom: 'var(--space-2)' }}>System Health & Host Metrics</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-sm)', marginBottom: 'var(--space-4)' }}>
                  Host environment resource utilization and backend engine telemetry parameters.
                </p>
                {isLoading ? (
                  <div className="skeleton-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
                    <div className="skeleton-item"></div>
                    <div className="skeleton-item"></div>
                    <div className="skeleton-item"></div>
                    <div className="skeleton-item"></div>
                    <div className="skeleton-item"></div>
                  </div>
                ) : (
                  <div className="health-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
                    <div className="health-item" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 'var(--space-1)' }}>
                      <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>Backend Engine</span>
                      <strong style={{ fontSize: 'var(--font-sm)' }}>{(status?.backend || 'OFFLINE').toUpperCase()}</strong>
                    </div>
                    <div className="health-item" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 'var(--space-1)' }}>
                      <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>CPU Count</span>
                      <strong style={{ fontSize: 'var(--font-sm)' }}>{info?.cpu_count || 0} Cores</strong>
                    </div>
                    <div className="health-item" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 'var(--space-1)' }}>
                      <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>Memory Load</span>
                      <strong style={{ fontSize: 'var(--font-sm)' }}>{info?.memory || 'N/A'}</strong>
                    </div>
                    <div className="health-item" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 'var(--space-1)' }}>
                      <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>Environment Mode</span>
                      <strong style={{ fontSize: 'var(--font-sm)' }}>{(status?.environment || 'N/A').toUpperCase()}</strong>
                    </div>
                    <div className="health-item" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 'var(--space-1)' }}>
                      <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>Host Platform</span>
                      <strong style={{ fontSize: 'var(--font-sm)', wordBreak: 'break-all' }}>{info?.platform || 'N/A'}</strong>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}

          {activeTab === 'agents' && (
            <div className="card">
              <h3 style={{ marginBottom: 'var(--space-2)' }}><Network size={18} style={{ marginRight: 6, verticalAlign: 'middle' }} />Multi-Agent Workflow Framework</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-sm)', marginBottom: 'var(--space-4)' }}>
                LangGraph handles complex routing states between sub-specialists in real-time.
              </p>
              <div style={{ background: 'var(--bg-tertiary)', padding: 'var(--space-4)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                <pre style={{ margin: 0, fontFamily: 'var(--font-mono)', fontSize: 'var(--font-xs)', overflowX: 'auto', whiteSpace: 'pre-wrap' }}>
{`# Multi-Agent Routing Routing Graph
from langgraph.graph import StateGraph, END
from app.agents.graph.state import AgentState

# Define Graph Builder
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("supervisor", supervisor_agent_node)
workflow.add_node("crm_agent", crm_agent_node)
workflow.add_node("db_agent", db_agent_node)

# Set Entry and Routing Links
workflow.set_entry_point("supervisor")
workflow.add_conditional_edges(
    "supervisor",
    should_continue_routing,
    {
        "crm": "crm_agent",
        "database": "db_agent",
        "end": END
    }
)
`}
                </pre>
              </div>
            </div>
          )}

          {activeTab === 'databases' && (
            <div className="card">
              <h3 style={{ marginBottom: 'var(--space-2)' }}><Database size={18} style={{ marginRight: 6, verticalAlign: 'middle' }} />Polyglot Persistent Architecture</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-sm)', marginBottom: 'var(--space-4)' }}>
                AI-BOS deploys a database-per-requirement pattern ensuring strict schema control and high-performance indexing:
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                <div style={{ padding: 'var(--space-3)', background: 'var(--bg-tertiary)', borderLeft: '4px solid var(--brand)', borderRadius: '0 var(--radius-xs) var(--radius-xs) 0' }}>
                  <strong>PostgreSQL</strong> — Primary ACID store (Transactions, RBAC schema, metadata).
                </div>
                <div style={{ padding: 'var(--space-3)', background: 'var(--bg-tertiary)', borderLeft: '4px solid var(--success)', borderRadius: '0 var(--radius-xs) var(--radius-xs) 0' }}>
                  <strong>MongoDB</strong> — Agent execution history logs, telemetry, dynamic schema documents.
                </div>
                <div style={{ padding: 'var(--space-3)', background: 'var(--bg-tertiary)', borderLeft: '4px solid var(--warning)', borderRadius: '0 var(--radius-xs) var(--radius-xs) 0' }}>
                  <strong>Redis</strong> — Shared session tokens, socket message pub/sub bus, ephemeral caching.
                </div>
                <div style={{ padding: 'var(--space-3)', background: 'var(--bg-tertiary)', borderLeft: '4px solid var(--info)', borderRadius: '0 var(--radius-xs) var(--radius-xs) 0' }}>
                  <strong>Qdrant Vector Database</strong> — Core semantic retrieval storage, document embedding indexes.
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="card">
              <h3 style={{ marginBottom: 'var(--space-2)' }}><Shield size={18} style={{ marginRight: 6, verticalAlign: 'middle' }} />Security, Secrets & RBAC Boundaries</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-sm)', marginBottom: 'var(--space-4)' }}>
                Ensures RBAC compliance at the router layer before execution reaches agents or databases.
              </p>
              <ul style={{ paddingLeft: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', fontSize: 'var(--font-sm)' }}>
                <li><strong>JWT Cryptography:</strong> Tokens signatures verified in FastAPI CORS gateways.</li>
                <li><strong>Roles Supported:</strong> Administrator, Manager, Agent, Auditor, Developer.</li>
                <li><strong>Rate Limiting:</strong> Configured in API server endpoints.</li>
                <li><strong>Data Protection:</strong> All connections encrypted over TLS protocols.</li>
              </ul>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

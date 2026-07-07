"use client";

import { ShieldAlert } from 'lucide-react';
import '../../../styles/dashboard.css';

export default function UnauthorizedPage() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', backgroundColor: 'var(--bg-primary)', width: '100vw' }}>
      <div className="card" style={{ width: '100%', maxWidth: '460px', padding: 'var(--space-8)', border: '1px solid var(--danger)', borderRadius: 'var(--radius-md)', background: 'var(--bg-secondary)', boxShadow: 'var(--shadow-lg)', textAlign: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 'var(--space-6)' }}>
          <div style={{ width: '56px', height: '56px', borderRadius: '50%', backgroundColor: 'rgba(239, 68, 68, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 'var(--space-4)' }}>
            <ShieldAlert size={28} style={{ color: 'var(--danger)' }} />
          </div>
          <h2 style={{ fontSize: 'var(--font-xl)', fontWeight: 'var(--weight-bold)', color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}>
            Access Denied
          </h2>
          <p style={{ fontSize: 'var(--font-sm)', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
            You do not possess the required Role permissions to access this segment of the AI-BOS console.
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          <button 
            className="retry-btn" 
            onClick={() => window.location.href = '/'}
            style={{ width: '100%', padding: '12px', borderRadius: 'var(--radius-sm)' }}
          >
            Return to Dashboard
          </button>
          
          <a 
            href="/auth/login" 
            style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)', textDecoration: 'none', marginTop: 'var(--space-2)' }}
          >
            Sign in as a different user
          </a>
        </div>
      </div>
    </div>
  );
}

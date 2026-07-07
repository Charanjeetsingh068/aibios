"use client";

import { Clock } from 'lucide-react';
import '../../../styles/dashboard.css';

export default function SessionExpiredPage() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', backgroundColor: 'var(--bg-primary)', width: '100vw' }}>
      <div className="card" style={{ width: '100%', maxWidth: '420px', padding: 'var(--space-8)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', background: 'var(--bg-secondary)', boxShadow: 'var(--shadow-lg)', textAlign: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 'var(--space-6)' }}>
          <div style={{ width: '56px', height: '56px', borderRadius: '50%', backgroundColor: 'var(--bg-tertiary)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 'var(--space-4)', border: '1px solid var(--border-color)' }}>
            <Clock size={28} style={{ color: 'var(--brand)' }} />
          </div>
          <h2 style={{ fontSize: 'var(--font-xl)', fontWeight: 'var(--weight-bold)', color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}>
            Session Expired
          </h2>
          <p style={{ fontSize: 'var(--font-sm)', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
            Your authentication session has expired due to inactivity. Please sign in again to access the portal.
          </p>
        </div>

        <button 
          className="retry-btn" 
          onClick={() => window.location.href = '/auth/login'}
          style={{ width: '100%', padding: '12px', borderRadius: 'var(--radius-sm)' }}
        >
          Sign In Again
        </button>
      </div>
    </div>
  );
}

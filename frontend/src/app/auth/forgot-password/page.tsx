"use client";

import { useState } from 'react';
import { Mail, ArrowLeft } from 'lucide-react';
import { forgotPassword } from '../../../services/authService';
import '../../../styles/dashboard.css';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [devToken, setDevToken] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setIsLoading(true);

    try {
      const res = await forgotPassword({ email });
      setMessage(res.message || 'Verification link has been sent to your email.');
      if (res.token_dev_only) {
        setDevToken(res.token_dev_only);
      }
    } catch (err: any) {
      setError(err.message || 'Could not verify your email address.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', backgroundColor: 'var(--bg-primary)', width: '100vw' }}>
      <div className="card" style={{ width: '100%', maxWidth: '420px', padding: 'var(--space-8)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', background: 'var(--bg-secondary)', boxShadow: 'var(--shadow-lg)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 'var(--space-6)' }}>
          <div className="logo-icon" style={{ width: '48px', height: '48px', fontSize: 'var(--font-2xl)', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 'var(--radius-sm)', marginBottom: 'var(--space-3)' }}>
            🔑
          </div>
          <h2 style={{ fontSize: 'var(--font-xl)', fontWeight: 'var(--weight-bold)', color: 'var(--text-primary)', marginBottom: 'var(--space-1)' }}>
            Recover Password
          </h2>
          <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)', textAlign: 'center' }}>
            Enter your email to receive a password reset token.
          </span>
        </div>

        {error && (
          <div className="error-container" style={{ margin: '0 0 var(--space-4) 0', padding: 'var(--space-3)' }}>
            <span className="error-msg" style={{ margin: 0 }}>{error}</span>
          </div>
        )}

        {message && (
          <div className="card" style={{ margin: '0 0 var(--space-4) 0', padding: 'var(--space-3)', border: '1px solid var(--success)', background: 'rgba(16, 185, 129, 0.05)', color: 'var(--success)', fontSize: 'var(--font-xs)' }}>
            {message}
          </div>
        )}

        {devToken && (
          <div className="card" style={{ margin: '0 0 var(--space-4) 0', padding: 'var(--space-3)', border: '1px solid var(--warning)', background: 'rgba(245, 158, 11, 0.05)', fontSize: 'var(--font-xs)', wordBreak: 'break-all' }}>
            <strong>Local Dev Reset Link:</strong><br/>
            <a href={`/auth/reset-password?token=${devToken}`} style={{ color: 'var(--brand)', textDecoration: 'underline' }}>
              /auth/reset-password?token={devToken}
            </a>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
            <label htmlFor="email" style={{ fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-semibold)', color: 'var(--text-secondary)' }}>
              Corporate Email Address
            </label>
            <div style={{ position: 'relative' }}>
              <Mail size={16} style={{ position: 'absolute', left: '12px', top: '14px', color: 'var(--text-tertiary)' }} />
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                style={{ width: '100%', padding: '10px var(--space-4) 10px 38px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)', fontSize: 'var(--font-sm)', outline: 'none' }}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="retry-btn"
            style={{ width: '100%', padding: '12px', borderRadius: 'var(--radius-sm)', fontSize: 'var(--font-sm)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 'var(--space-2)' }}
          >
            {isLoading ? 'Requesting link...' : 'Send Reset Link'}
          </button>
        </form>

        <div style={{ marginTop: 'var(--space-6)', textAlign: 'center', borderTop: '1px solid var(--border-color)', paddingTop: 'var(--space-4)' }}>
          <a href="/auth/login" style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--space-2)', fontSize: 'var(--font-xs)', color: 'var(--text-secondary)', textDecoration: 'none' }}>
            <ArrowLeft size={14} /> Back to Sign In
          </a>
        </div>
      </div>
    </div>
  );
}

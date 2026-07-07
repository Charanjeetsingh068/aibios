"use client";

import { useState, useEffect } from 'react';
import { Key, CheckCircle, ArrowLeft } from 'lucide-react';
import { resetPassword } from '../../../services/authService';
import '../../../styles/dashboard.css';

export default function ResetPasswordPage() {
  const [token, setToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Get query token parameters
    if (typeof window !== 'undefined') {
      const urlParams = new URLSearchParams(window.location.search);
      const urlToken = urlParams.get('token');
      if (urlToken) {
        setToken(urlToken);
      } else {
        setError('Password reset token is missing. Please request a new link.');
      }
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setIsLoading(true);

    try {
      await resetPassword({ token, new_password: newPassword });
      setMessage('Password updated successfully! You will be redirected to the sign in page shortly.');
      setTimeout(() => {
        window.location.href = '/auth/login';
      }, 3000);
    } catch (err: any) {
      setError(err.message || 'Reset token is invalid or expired.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', backgroundColor: 'var(--bg-primary)', width: '100vw' }}>
      <div className="card" style={{ width: '100%', maxWidth: '420px', padding: 'var(--space-8)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', background: 'var(--bg-secondary)', boxShadow: 'var(--shadow-lg)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 'var(--space-6)' }}>
          <div className="logo-icon" style={{ width: '48px', height: '48px', fontSize: 'var(--font-2xl)', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 'var(--radius-sm)', marginBottom: 'var(--space-3)' }}>
            🔒
          </div>
          <h2 style={{ fontSize: 'var(--font-xl)', fontWeight: 'var(--weight-bold)', color: 'var(--text-primary)', marginBottom: 'var(--space-1)' }}>
            Reset Password
          </h2>
          <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)', textAlign: 'center' }}>
            Set a new secure password for your user account.
          </span>
        </div>

        {error && (
          <div className="error-container" style={{ margin: '0 0 var(--space-4) 0', padding: 'var(--space-3)' }}>
            <span className="error-msg" style={{ margin: 0 }}>{error}</span>
          </div>
        )}

        {message && (
          <div className="card" style={{ margin: '0 0 var(--space-4) 0', padding: 'var(--space-3)', border: '1px solid var(--success)', background: 'rgba(16, 185, 129, 0.05)', color: 'var(--success)', fontSize: 'var(--font-xs)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <CheckCircle size={16} />
            <span>{message}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
            <label htmlFor="password" style={{ fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-semibold)', color: 'var(--text-secondary)' }}>
              New Secure Password
            </label>
            <div style={{ position: 'relative' }}>
              <Key size={16} style={{ position: 'absolute', left: '12px', top: '14px', color: 'var(--text-tertiary)' }} />
              <input
                id="password"
                type="password"
                required
                disabled={!token || !!message}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Min 8 characters"
                style={{ width: '100%', padding: '10px var(--space-4) 10px 38px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)', fontSize: 'var(--font-sm)', outline: 'none' }}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading || !token || !!message}
            className="retry-btn"
            style={{ width: '100%', padding: '12px', borderRadius: 'var(--radius-sm)', fontSize: 'var(--font-sm)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 'var(--space-2)' }}
          >
            {isLoading ? 'Updating Password...' : 'Save New Password'}
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

"use client";

import { useState, useEffect, useRef } from 'react';
import Script from 'next/script';
import { Key, Mail } from 'lucide-react';
import { login, loginWithGoogleCode } from '../../../services/authService';
import '../../../styles/dashboard.css';

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '';

declare global {
  interface Window {
    google?: any;
  }
}

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [googleReady, setGoogleReady] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const googleCodeClientRef = useRef<any>(null);

  // Clear any existing session tokens upon loading the login page
  useEffect(() => {
    localStorage.removeItem('aibos_access_token');
    localStorage.removeItem('aibos_refresh_token');
  }, []);

  const initGoogleCodeClient = () => {
    if (!GOOGLE_CLIENT_ID || !window.google?.accounts?.oauth2) return;
    googleCodeClientRef.current = window.google.accounts.oauth2.initCodeClient({
      client_id: GOOGLE_CLIENT_ID,
      scope: 'openid email profile',
      ux_mode: 'popup',
      callback: async (response: { code?: string; error?: string }) => {
        if (!response.code) {
          setError('Google sign-in was cancelled or failed.');
          setGoogleLoading(false);
          return;
        }
        try {
          await loginWithGoogleCode(response.code);
          window.location.href = '/';
        } catch (err: any) {
          setError(err.message || 'Google sign-in failed. Please try again.');
          setGoogleLoading(false);
        }
      },
    });
    setGoogleReady(true);
  };

  const handleGoogleSignIn = () => {
    setError('');
    setGoogleLoading(true);
    if (!googleCodeClientRef.current) {
      setError('Google sign-in is still loading. Please try again in a moment.');
      setGoogleLoading(false);
      return;
    }
    googleCodeClientRef.current.requestCode();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login({ email, password, remember_me: rememberMe });
      window.location.href = '/';
    } catch (err: any) {
      setError(err.message || 'Incorrect email or password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', backgroundColor: 'var(--bg-primary)', width: '100vw' }}>
      <div className="card" style={{ width: '100%', maxWidth: '420px', padding: 'var(--space-8)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', background: 'var(--bg-secondary)', boxShadow: 'var(--shadow-lg)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 'var(--space-6)' }}>
          <div className="logo-icon" style={{ width: '48px', height: '48px', fontSize: 'var(--font-2xl)', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 'var(--radius-sm)', marginBottom: 'var(--space-3)' }}>
            Ω
          </div>
          <h2 style={{ fontSize: 'var(--font-2xl)', fontWeight: 'var(--weight-bold)', color: 'var(--text-primary)', marginBottom: 'var(--space-1)' }}>
            AI-BOS Enterprise
          </h2>
          <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>
            Phase 2 Authentication Console
          </span>
        </div>

        {error && (
          <div className="error-container" style={{ margin: '0 0 var(--space-4) 0', padding: 'var(--space-3)' }}>
            <span className="error-msg" style={{ margin: 0 }}>{error}</span>
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

          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
            <label htmlFor="password" style={{ fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-semibold)', color: 'var(--text-secondary)' }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <Key size={16} style={{ position: 'absolute', left: '12px', top: '14px', color: 'var(--text-tertiary)' }} />
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                style={{ width: '100%', padding: '10px var(--space-4) 10px 38px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)', fontSize: 'var(--font-sm)', outline: 'none' }}
              />
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 'var(--space-1)' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', fontSize: 'var(--font-xs)', color: 'var(--text-secondary)', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                style={{ accentColor: 'var(--brand)', cursor: 'pointer' }}
              />
              Remember my session
            </label>
            <a href="/auth/forgot-password" style={{ fontSize: 'var(--font-xs)', color: 'var(--brand)', textDecoration: 'none', fontWeight: 'var(--weight-semibold)' }}>
              Forgot password?
            </a>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="retry-btn"
            style={{ width: '100%', padding: '12px', borderRadius: 'var(--radius-sm)', fontSize: 'var(--font-sm)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 'var(--space-2)', marginTop: 'var(--space-2)' }}
          >
            {isLoading ? 'Verifying Credentials...' : 'Sign In'}
          </button>

          {GOOGLE_CLIENT_ID && (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', margin: 'var(--space-2) 0' }}>
                <div style={{ flexGrow: 1, height: 1, backgroundColor: 'var(--border-color)' }} />
                <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>OR</span>
                <div style={{ flexGrow: 1, height: 1, backgroundColor: 'var(--border-color)' }} />
              </div>

              <button
                type="button"
                onClick={handleGoogleSignIn}
                disabled={googleLoading || !googleReady}
                style={{ width: '100%', padding: '12px', borderRadius: 'var(--radius-sm)', fontSize: 'var(--font-sm)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 'var(--space-2)', border: '1px solid var(--border-color)', backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)', cursor: googleReady ? 'pointer' : 'not-allowed' }}
              >
                <svg width="16" height="16" viewBox="0 0 48 48" aria-hidden="true">
                  <path fill="#FFC107" d="M43.611,20.083H42V20H24v8h11.303c-1.649,4.657-6.08,8-11.303,8c-6.627,0-12-5.373-12-12s5.373-12,12-12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C12.955,4,4,12.955,4,24s8.955,20,20,20s20-8.955,20-20C44,22.659,43.862,21.35,43.611,20.083z"/>
                  <path fill="#FF3D00" d="M6.306,14.691l6.571,4.819C14.655,15.108,18.961,12,24,12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C16.318,4,9.656,8.337,6.306,14.691z"/>
                  <path fill="#4CAF50" d="M24,44c5.166,0,9.86-1.977,13.409-5.192l-6.19-5.238C29.211,35.091,26.715,36,24,36c-5.202,0-9.619-3.317-11.283-7.946l-6.522,5.025C9.505,39.556,16.227,44,24,44z"/>
                  <path fill="#1976D2" d="M43.611,20.083H42V20H24v8h11.303c-0.792,2.237-2.231,4.166-4.087,5.571c0.001-0.001,0.002-0.001,0.003-0.002l6.19,5.238C36.971,39.205,44,34,44,24C44,22.659,43.862,21.35,43.611,20.083z"/>
                </svg>
                {googleLoading ? 'Signing in...' : 'Sign in with Google'}
              </button>
            </>
          )}
        </form>
      </div>
      {GOOGLE_CLIENT_ID && (
        <Script
          src="https://accounts.google.com/gsi/client"
          strategy="afterInteractive"
          onLoad={initGoogleCodeClient}
        />
      )}
    </div>
  );
}

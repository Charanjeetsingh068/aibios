"use client";

import { useState, useEffect } from 'react';
import { Mail, Phone, Globe, Shield, Calendar, Clock, ArrowLeft, Key } from 'lucide-react';
import { getMe, UserResponse } from '../../services/authService';
import '../../styles/dashboard.css';

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await getMe();
        setProfile(data);
      } catch (err: any) {
        setError(err.message || 'Failed to retrieve profile details.');
        // Redirect to login if unauthorized
        setTimeout(() => {
          window.location.href = '/auth/login';
        }, 1500);
      } finally {
        setIsLoading(false);
      }
    };
    fetchProfile();
  }, []);

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', backgroundColor: 'var(--bg-primary)' }}>
        <div className="card skeleton-card" style={{ width: '100%', maxWidth: '600px', padding: 'var(--space-8)' }}>
          <div className="skeleton-line title" style={{ width: '40%' }}></div>
          <div className="skeleton-line value"></div>
          <div className="skeleton-line desc" style={{ width: '80%' }}></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', backgroundColor: 'var(--bg-primary)' }}>
        <div className="card" style={{ width: '100%', maxWidth: '400px', padding: 'var(--space-6)', textAlign: 'center', borderColor: 'var(--danger)' }}>
          <div className="error-title">Error</div>
          <div className="error-msg">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', backgroundColor: 'var(--bg-primary)', padding: 'var(--space-8)', width: '100vw' }}>
      <div style={{ maxWidth: '800px', width: '100%', margin: '0 auto' }}>
        <header style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', marginBottom: 'var(--space-8)' }}>
          <button 
            onClick={() => window.location.href = '/'}
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '40px', height: '40px', borderRadius: '50%', border: '1px solid var(--border-color)', backgroundColor: 'var(--bg-secondary)', color: 'var(--text-secondary)', cursor: 'pointer' }}
          >
            <ArrowLeft size={18} />
          </button>
          <div>
            <h1 style={{ fontSize: 'var(--font-2xl)', fontWeight: 'var(--weight-bold)', color: 'var(--text-primary)' }}>
              Account Settings
            </h1>
            <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>
              Manage your personal tenant credentials and profile preferences.
            </span>
          </div>
        </header>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 'var(--space-6)' }}>
          {/* Left Column - Avatar & Core Details */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', height: 'fit-content' }}>
            <div style={{ width: '96px', height: '96px', borderRadius: '50%', backgroundColor: 'var(--bg-tertiary)', border: '2px solid var(--brand)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 'var(--font-3xl)', fontWeight: 'bold', color: 'var(--brand)', marginBottom: 'var(--space-4)' }}>
              {profile ? `${profile.first_name[0]}${profile.last_name[0]}` : 'U'}
            </div>
            <h3 style={{ fontSize: 'var(--font-lg)', fontWeight: 'var(--weight-bold)', color: 'var(--text-primary)' }}>
              {profile?.first_name} {profile?.last_name}
            </h3>
            <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)', marginBottom: 'var(--space-4)' }}>
              Role: {profile?.role_id.toUpperCase().replace('_', ' ')}
            </span>
            <div style={{ width: '100%', borderTop: '1px solid var(--border-color)', paddingTop: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
              <button 
                onClick={() => window.location.href = '/profile/change-password'}
                className="retry-btn"
                style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 'var(--space-2)' }}
              >
                <Key size={14} /> Change Password
              </button>
            </div>
          </div>

          {/* Right Column - User Attributes */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
            <div>
              <h3 style={{ fontSize: 'var(--font-md)', fontWeight: 'var(--weight-bold)', color: 'var(--text-primary)', marginBottom: 'var(--space-4)' }}>
                Profile Details
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', padding: 'var(--space-3)', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
                  <Mail size={18} style={{ color: 'var(--brand)' }} />
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>Email Address</span>
                    <strong style={{ fontSize: 'var(--font-sm)', color: 'var(--text-primary)' }}>{profile?.email}</strong>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', padding: 'var(--space-3)', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
                  <Phone size={18} style={{ color: 'var(--brand)' }} />
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>Contact Number</span>
                    <strong style={{ fontSize: 'var(--font-sm)', color: 'var(--text-primary)' }}>{profile?.phone || 'No phone registered'}</strong>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', padding: 'var(--space-3)', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
                  <Globe size={18} style={{ color: 'var(--brand)' }} />
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>Locale & Timezone</span>
                    <strong style={{ fontSize: 'var(--font-sm)', color: 'var(--text-primary)' }}>
                      Language: {(profile?.language || 'en').toUpperCase()} | Timezone: {profile?.timezone}
                    </strong>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', padding: 'var(--space-3)', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
                  <Shield size={18} style={{ color: 'var(--brand)' }} />
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>Tenant Organization</span>
                    <strong style={{ fontSize: 'var(--font-sm)', color: 'var(--text-primary)' }}>
                      Org ID: {profile?.organization_id} (Active)
                    </strong>
                  </div>
                </div>
              </div>
            </div>

            <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: 'var(--space-4)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <Calendar size={16} style={{ color: 'var(--text-tertiary)' }} />
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>Member Since</span>
                  <span style={{ fontSize: 'var(--font-xs)', fontWeight: 'bold' }}>
                    {profile ? new Date(profile.created_at).toLocaleDateString() : 'N/A'}
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <Clock size={16} style={{ color: 'var(--text-tertiary)' }} />
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>Last Login Log</span>
                  <span style={{ fontSize: 'var(--font-xs)', fontWeight: 'bold' }}>
                    {profile?.last_login ? new Date(profile.last_login).toLocaleString() : 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

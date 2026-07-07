export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token: string;
  user_id: string;
  organization_id: string;
  role: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

export interface UserResponse {
  id: string;
  organization_id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  status: string;
  role_id: string;
  timezone: string;
  language: string;
  created_at: string;
  updated_at: string;
  last_login?: string;
}

const API_BASE = '/api/v1/auth';

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('aibos_access_token');
}

export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('aibos_refresh_token');
}

export function setTokens(tokens: TokenResponse): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('aibos_access_token', tokens.access_token);
  localStorage.setItem('aibos_refresh_token', tokens.refresh_token);
  localStorage.setItem('aibos_user_role', tokens.role);
  localStorage.setItem('aibos_user_id', tokens.user_id);
  localStorage.setItem('aibos_org_id', tokens.organization_id);
}

export function clearTokens(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('aibos_access_token');
  localStorage.removeItem('aibos_refresh_token');
  localStorage.removeItem('aibos_user_role');
  localStorage.removeItem('aibos_user_id');
  localStorage.removeItem('aibos_org_id');
}

export async function login(data: LoginRequest): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Authentication failed. Please verify credentials.');
  }
  const tokenData: TokenResponse = await res.json();
  setTokens(tokenData);
  return tokenData;
}

export async function logout(): Promise<void> {
  const token = getAccessToken();
  if (token) {
    await fetch(`${API_BASE}/logout`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }).catch(() => {});
  }
  clearTokens();
}

export async function refreshAccessToken(): Promise<TokenResponse> {
  const refresh = getRefreshToken();
  if (!refresh) {
    throw new Error('No refresh token available');
  }
  const res = await fetch(`${API_BASE}/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refresh })
  });
  if (!res.ok) {
    clearTokens();
    throw new Error('Session has expired. Please log in again.');
  }
  const tokenData: TokenResponse = await res.json();
  setTokens(tokenData);
  return tokenData;
}

export async function forgotPassword(data: ForgotPasswordRequest): Promise<any> {
  const res = await fetch(`${API_BASE}/forgot-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Could not trigger recovery email.');
  }
  return res.json();
}

export async function resetPassword(data: ResetPasswordRequest): Promise<any> {
  const res = await fetch(`${API_BASE}/reset-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Reset token is invalid or expired.');
  }
  return res.json();
}

export async function changePassword(data: ChangePasswordRequest): Promise<any> {
  const token = getAccessToken();
  if (!token) {
    throw new Error('Not authenticated');
  }
  const res = await fetch(`${API_BASE}/change-password`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(data)
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to update password.');
  }
  clearTokens();
  return res.json();
}

export async function getMe(): Promise<UserResponse> {
  const token = getAccessToken();
  if (!token) {
    throw new Error('Not authenticated');
  }
  const res = await fetch(`${API_BASE}/me`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  if (!res.ok) {
    if (res.status === 401) {
      // Attempt refresh
      try {
        await refreshAccessToken();
        return getMe();
      } catch {
        clearTokens();
        throw new Error('Not authenticated');
      }
    }
    throw new Error('Failed to fetch profile info.');
  }
  return res.json();
}

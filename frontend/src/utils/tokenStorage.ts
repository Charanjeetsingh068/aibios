export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token: string;
  user_id: string;
  organization_id: string;
  role: string;
}

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

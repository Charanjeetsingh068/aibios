import axiosInstance from './axiosInstance';
import { getAccessToken, getRefreshToken, setTokens, clearTokens, TokenResponse } from '../utils/tokenStorage';

export type { TokenResponse };

export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
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

export { getAccessToken, getRefreshToken, setTokens, clearTokens };

export async function login(data: LoginRequest): Promise<TokenResponse> {
  try {
    const response = await axiosInstance.post('/auth/login', data);
    const tokenData: TokenResponse = response.data;
    setTokens(tokenData);
    return tokenData;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Authentication failed. Please verify credentials.');
  }
}

export async function loginWithGoogleCode(code: string): Promise<TokenResponse> {
  try {
    const response = await axiosInstance.post('/oauth/callback/google', { code, state: 'google_popup' });
    const tokenData: TokenResponse = response.data;
    setTokens(tokenData);
    return tokenData;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Google sign-in failed. Please try again.');
  }
}

export async function logout(): Promise<void> {
  try {
    await axiosInstance.post('/auth/logout');
  } catch {
    // Ignore errors on logout
  } finally {
    clearTokens();
  }
}

export async function refreshAccessToken(): Promise<TokenResponse> {
  const refresh = getRefreshToken();
  if (!refresh) {
    throw new Error('No refresh token available');
  }
  try {
    const response = await axiosInstance.post('/auth/refresh', { refresh_token: refresh });
    const tokenData: TokenResponse = response.data;
    setTokens(tokenData);
    return tokenData;
  } catch {
    clearTokens();
    throw new Error('Session has expired. Please log in again.');
  }
}

export async function forgotPassword(data: ForgotPasswordRequest): Promise<any> {
  try {
    const response = await axiosInstance.post('/auth/forgot-password', data);
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Could not trigger recovery email.');
  }
}

export async function resetPassword(data: ResetPasswordRequest): Promise<any> {
  try {
    const response = await axiosInstance.post('/auth/reset-password', data);
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Reset token is invalid or expired.');
  }
}

export async function changePassword(data: ChangePasswordRequest): Promise<any> {
  try {
    const response = await axiosInstance.post('/auth/change-password', data);
    clearTokens();
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to update password.');
  }
}

export async function getMe(): Promise<UserResponse> {
  try {
    const response = await axiosInstance.get('/auth/me');
    return response.data;
  } catch {
    throw new Error('Failed to fetch profile info.');
  }
}

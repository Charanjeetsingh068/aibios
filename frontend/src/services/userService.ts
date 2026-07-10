import axiosInstance from './axiosInstance';

export interface DashboardUser {
  id: string;
  organization_id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  status: string;
  role_id: string;
  roles: string[];
  department?: string;
  designation?: string;
  profile_image?: string;
  timezone: string;
  language: string;
  email_verified: boolean;
  mfa_enabled: boolean;
  last_login?: string;
  last_activity?: string;
  created_at?: string;
  updated_at?: string;
}

export const fetchUsers = async (params: { skip?: number; limit?: number; search?: string; status_filter?: string; organization_id?: string } = {}): Promise<{ users: DashboardUser[]; total: number; skip: number; limit: number }> => {
  const response = await axiosInstance.get('/api/v1/users', { params });
  return response.data;
};

export const fetchUser = async (userId: string): Promise<DashboardUser> => {
  const response = await axiosInstance.get(`/api/v1/users/${userId}`);
  return response.data;
};

export const createUser = async (data: any) => {
  const response = await axiosInstance.post('/api/v1/users', data);
  return response.data;
};

export const inviteUser = async (data: any) => {
  const response = await axiosInstance.post('/api/v1/users/invite', data);
  return response.data;
};

export const updateUser = async (userId: string, data: any) => {
  const response = await axiosInstance.patch(`/api/v1/users/${userId}`, data);
  return response.data;
};

export const suspendUser = async (userId: string) => {
  const response = await axiosInstance.post(`/api/v1/users/${userId}/suspend`);
  return response.data;
};

export const reactivateUser = async (userId: string) => {
  const response = await axiosInstance.post(`/api/v1/users/${userId}/reactivate`);
  return response.data;
};

export const deleteUser = async (userId: string) => {
  const response = await axiosInstance.delete(`/api/v1/users/${userId}`);
  return response.data;
};

export const resetUserPassword = async (userId: string) => {
  const response = await axiosInstance.post(`/api/v1/users/${userId}/reset-password`);
  return response.data;
};

export const forceUserPassword = async (userId: string, password: string) => {
  const response = await axiosInstance.post(`/api/v1/users/${userId}/force-password`, { password });
  return response.data;
};

export const assignUserRole = async (userId: string, roleId: string) => {
  const response = await axiosInstance.post(`/api/v1/users/${userId}/roles`, { role_id: roleId });
  return response.data;
};

export const removeUserRole = async (userId: string, roleId: string) => {
  const response = await axiosInstance.delete(`/api/v1/users/${userId}/roles/${roleId}`);
  return response.data;
};

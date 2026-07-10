import axiosInstance from './axiosInstance';

export interface Permission {
  id: string;
  name: string;
  description: string;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  is_system: boolean;
  permissions: string[];
  created_at: string;
  updated_at: string;
}

export const fetchPermissions = async (): Promise<{ permissions: Permission[] }> => {
  const response = await axiosInstance.get('/api/v1/roles/permissions');
  return response.data;
};

export const fetchRoles = async (): Promise<{ roles: Role[] }> => {
  const response = await axiosInstance.get('/api/v1/roles');
  return response.data;
};

export const createRole = async (data: { id: string; name: string; description?: string; permissions?: string[] }) => {
  const response = await axiosInstance.post('/api/v1/roles', data);
  return response.data;
};

export const updateRole = async (id: string, data: { name?: string; description?: string }) => {
  const response = await axiosInstance.patch(`/api/v1/roles/${id}`, data);
  return response.data;
};

export const deleteRole = async (id: string) => {
  const response = await axiosInstance.delete(`/api/v1/roles/${id}`);
  return response.data;
};

export const assignPermission = async (roleId: string, permissionId: string) => {
  const response = await axiosInstance.post(`/api/v1/roles/${roleId}/permissions`, { permission_id: permissionId });
  return response.data;
};

export const removePermission = async (roleId: string, permissionId: string) => {
  const response = await axiosInstance.delete(`/api/v1/roles/${roleId}/permissions/${permissionId}`);
  return response.data;
};

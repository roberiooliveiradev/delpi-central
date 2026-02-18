// src/data/adminApi.ts

import { ApiClient } from "./apiClient";

export type AdminUser = {
  id: string;
  name: string;
  email: string;
  is_superadmin: boolean;
  roles: { id: string; name: string }[];
  groups: { id: string; name: string }[];
};

export type AdminRole = {
  id: string;
  name: string;
  description?: string | null;
  permissions: { id: string; code: string; name?: string | null }[];
};

export type AdminPermission = {
  id: string;
  code: string;
  name?: string | null;
  description?: string | null;
};

export type AdminGroup = {
  id: string;
  name: string;
  description?: string | null;
  roles: { id: string; name: string }[];
};

export type AdminApp = {
  id: string;
  name: string;
  base_path?: string | null;
  icon?: string | null;
  type?: string | null;
  version?: string | null;
  active?: boolean;
};

export type AdminAppRoute = {
  id: string;
  app_id: string;
  path: string;
  label?: string | null;
  icon?: string | null;
  order?: number | null;
  show_in_menu?: boolean | null;
  active?: boolean;
  permission_id?: string | null;
  permission_code?: string | null;
};

export class AdminApi {
  private client: ApiClient;
  
  constructor(client: ApiClient) {
    this.client = client;
  }
  
  // =========================
  // RBAC
  // =========================
  listUsers(q?: string) {
    const qs = q ? `?q=${encodeURIComponent(q)}` : "";
    return this.client.get<AdminUser[]>(`/core-api/admin/rbac/users${qs}`);
  }

  getUser(userId: string) {
    return this.client.get<AdminUser>(`/core-api/admin/rbac/users/${userId}`);
  }

  listRoles() {
    return this.client.get<AdminRole[]>(`/core-api/admin/rbac/roles`);
  }

  listPermissions() {
    return this.client.get<AdminPermission[]>(`/core-api/admin/rbac/permissions`);
  }

  listGroups() {
    return this.client.get<AdminGroup[]>(`/core-api/admin/rbac/groups`);
  }

  setUserRoles(userId: string, roleIds: string[]) {
    return this.client.put<AdminUser>(
      `/core-api/admin/rbac/users/${userId}/roles`,
      { roleIds }
    );
  }

  setUserGroups(userId: string, groupIds: string[]) {
    return this.client.put<AdminUser>(
      `/core-api/admin/rbac/users/${userId}/groups`,
      { groupIds }
    );
  }

  setRolePermissions(roleId: string, permissionIds: string[]) {
    return this.client.put<AdminRole>(
      `/core-api/admin/rbac/roles/${roleId}/permissions`,
      { permissionIds }
    );
  }

  setGroupRoles(groupId: string, roleIds: string[]) {
    return this.client.put<AdminGroup>(
      `/core-api/admin/rbac/groups/${groupId}/roles`,
      { roleIds }
    );
  }

  // =========================
  // Apps & Routes
  // =========================
  listApps() {
    return this.client.get<AdminApp[]>(`/core-api/admin/apps`);
  }

  createApp(payload: Partial<AdminApp>) {
    return this.client.post<{ ok: boolean; id: string }>(
      `/core-api/admin/apps`,
      payload
    );
  }

  updateApp(appId: string, payload: Partial<AdminApp>) {
    return this.client.put<{ ok: boolean }>(
      `/core-api/admin/apps/${appId}`,
      payload
    );
  }

  listRoutes(appId: string) {
    return this.client.get<AdminAppRoute[]>(
      `/core-api/admin/apps/${appId}/routes`
    );
  }

  createRoute(appId: string, payload: Partial<AdminAppRoute>) {
    return this.client.post<{ ok: boolean; id: string }>(
      `/core-api/admin/apps/${appId}/routes`,
      payload
    );
  }

  updateRoute(routeId: string, payload: Partial<AdminAppRoute>) {
    return this.client.put<{ ok: boolean }>(
      `/core-api/admin/apps/routes/${routeId}`,
      payload
    );
  }

  activateApp(appId: string) {
    return this.client.post<{ ok: boolean }>(`/core-api/admin/apps/${appId}/activate`);
  }

  deactivateApp(appId: string) {
    return this.client.post<{ ok: boolean }>(`/core-api/admin/apps/${appId}/deactivate`);
  }

  activateRoute(routeId: string) {
    return this.client.post<{ ok: boolean }>(`/core-api/admin/apps/routes/${routeId}/activate`);
  }

  deactivateRoute(routeId: string) {
    return this.client.post<{ ok: boolean }>(`/core-api/admin/apps/routes/${routeId}/deactivate`);
  }
}

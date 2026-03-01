// src/data/adminApi.ts
import { ApiClient } from "./apiClient";

export type PaginationMeta = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type PaginatedResponse<T> = {
  data: T[];
  pagination: PaginationMeta;
};

export type AdminUser = {
  id: string;
  name: string;
  email: string;
  is_superadmin: boolean;
};

export type AdminRole = {
  id: string;
  name: string;
  description?: string | null;
};

export type AdminPermission = {
  id: string;
  code: string;
  name?: string | null;
  description?: string | null;
  module?: string | null;
};

export type AdminGroup = {
  id: string;
  name: string;
  description?: string | null;
};

export type ListQueryOptions = {
  page?: number;
  pageSize?: number;
  q?: string;
  sort?: string;
  direction?: "asc" | "desc";
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

export type PluginVersion = {
  version: string;
  checksum: string;
  created_at: string | null;
};

export type RegisterPluginResponse = {
  status: "registered";
  appId: string;
  version: string;
};

export type RollbackPluginResponse = {
  status: "rolled_back";
  version: string;
};

export class AdminApi {
  public client: ApiClient;
  constructor(client: ApiClient) {
    this.client = client;
  }

  private buildQuery(options?: ListQueryOptions) {
    const params = new URLSearchParams();
    if (options?.page) params.append("page", String(options.page));
    if (options?.pageSize) params.append("page_size", String(options.pageSize));
    if (options?.q) params.append("q", options.q);
    if (options?.sort) params.append("sort", options.sort);
    if (options?.direction) params.append("direction", options.direction);

    const queryString = params.toString();
    return queryString ? `?${queryString}` : "";
  }

  /* =========================
     Plugins / Manifest
  ========================= */
  getPluginManifest(appId: string) {
    return this.client.get<any>(
      `/core-api/admin/plugins/${appId}/manifest`
    );
  }
    
  registerManifest(manifest: any) {
    return this.client.post(
      `/core-api/admin/plugins/register`,
      manifest
    );
  }

  updatePluginManifest(appId: string, manifest: any) {
    return this.client.put(
      `/core-api/admin/plugins/${appId}/manifest`,
      manifest
    );
  }
  
  /* =========================
    Plugin Versions / Rollback
  ========================= */

  listPluginVersions(appId: string) {
    return this.client.get(
      `/core-api/admin/plugins/${appId}/versions`
    );
  }

  rollbackPlugin(appId: string, version: string) {
    return this.client.post(
      `/core-api/admin/plugins/${appId}/rollback`,
      { version }
    );
  }
  
  deletePlugin(appId: string) {
    return this.client.delete(
      `/core-api/admin/plugins/${appId}`
    );
  }

  bulkUnregisterPlugins(ids: string[]) {
    return this.client.post<{ ok: boolean; deleted: number }>(
      `/core-api/admin/plugins/bulk-unregister`,
      { ids }
    );
  }
  
  /* =========================
     RBAC - Users
  ========================= */

  listUsers(options?: ListQueryOptions) {
    const qs = this.buildQuery(options);
    return this.client.get<PaginatedResponse<AdminUser>>(
      `/core-api/admin/rbac/users${qs}`
    );
  }

  getUser(userId: string) {
    return this.client.get<AdminUser>(`/core-api/admin/rbac/users/${userId}`);
  }

  updateUser(
    userId: string,
    payload: {
      roleIds?: string[];
      groupIds?: string[];
      is_superadmin?: boolean;
    }
  ) {
    return this.client.put<{ ok: boolean }>(
      `/core-api/admin/rbac/users/${userId}`,
      payload
    );
  }

  getUserRoles(userId: string) {
    return this.client.get<PaginatedResponse<{ id: string; name: string }>>(
      `/core-api/admin/users/${userId}/roles`
    );
  }

  getUserGroups(userId: string) {
    return this.client.get<PaginatedResponse<{ id: string; name: string }>>(
      `/core-api/admin/users/${userId}/groups`
    );
  }

  deleteUser(userId: string) {
    return this.client.delete<{ ok: boolean }>(
      `/core-api/admin/rbac/users/${userId}`
    );
  }

  bulkDeleteUsers(ids: string[]) {
    return this.client.post<{ ok: boolean; deleted: number }>(
      `/core-api/admin/rbac/users/bulk-delete`,
      { ids }
    );
  }

  /* =========================
     RBAC - Roles
  ========================= */

  listRoles(options?: ListQueryOptions) {
    const qs = this.buildQuery(options);
    return this.client.get<PaginatedResponse<AdminRole>>(
      `/core-api/admin/rbac/roles${qs}`
    );
  }

  createRole(payload: { name: string; description?: string | null }) {
    return this.client.post<AdminRole>(`/core-api/admin/rbac/roles`, payload);
  }

  updateRole(roleId: string, payload: Partial<AdminRole>) {
    return this.client.put<AdminRole>(
      `/core-api/admin/rbac/roles/${roleId}`,
      payload
    );
  }

  deleteRole(roleId: string) {
    return this.client.delete<{ ok: boolean }>(
      `/core-api/admin/rbac/roles/${roleId}`
    );
  }

  bulkDeleteRoles(ids: string[]) {
    return this.client.post<{ ok: boolean; deleted: number }>(
      `/core-api/admin/rbac/roles/bulk-delete`,
      { ids }
    );
  }

  setRolePermissions(roleId: string, permissionIds: string[]) {
    return this.client.put<AdminRole>(
      `/core-api/admin/rbac/roles/${roleId}/permissions`,
      { permissionIds }
    );
  }

  /* =========================
     RBAC - Permissions
  ========================= */

  listPermissions(options?: ListQueryOptions) {
    const qs = this.buildQuery(options);
    return this.client.get<PaginatedResponse<AdminPermission>>(
      `/core-api/admin/rbac/permissions${qs}`
    );
  }

  /* =========================
     RBAC - Groups
  ========================= */

  listGroups(options?: ListQueryOptions) {
    const qs = this.buildQuery(options);
    return this.client.get<PaginatedResponse<AdminGroup>>(
      `/core-api/admin/rbac/groups${qs}`
    );
  }

  createGroup(payload: { name: string; description?: string | null }) {
    return this.client.post<AdminGroup>(`/core-api/admin/rbac/groups`, payload);
  }

  updateGroup(groupId: string, payload: Partial<AdminGroup>) {
    return this.client.put<AdminGroup>(
      `/core-api/admin/rbac/groups/${groupId}`,
      payload
    );
  }

  deleteGroup(groupId: string) {
    return this.client.delete<{ ok: boolean }>(
      `/core-api/admin/rbac/groups/${groupId}`
    );
  }

  bulkDeleteGroups(ids: string[]) {
    return this.client.post<{ ok: boolean; deleted: number }>(
      `/core-api/admin/rbac/groups/bulk-delete`,
      { ids }
    );
  }

  setGroupRoles(groupId: string, roleIds: string[]) {
    return this.client.put<AdminGroup>(
      `/core-api/admin/rbac/groups/${groupId}/roles`,
      { roleIds }
    );
  }

  /* =========================
     Apps / Routes (mantém)
  ========================= */

  listApps(options?: ListQueryOptions) {
    const qs = this.buildQuery(options);
    return this.client.get<PaginatedResponse<AdminApp>>(
      `/core-api/admin/apps${qs}`
    );
  }

  updateApp(appId: string, payload: Partial<AdminApp>) {
    return this.client.put<{ ok: boolean }>(`/core-api/admin/apps/${appId}`, payload);
  }


  /* =========================
    Plugin Activation
  ========================= */

  setPluginActive(appId: string, active: boolean) {
    return this.client.post<{ ok: boolean }>(
      `/core-api/admin/plugins/${appId}/active`,
      { active }
    );
  }

  bulkActivatePlugins(ids: string[]) {
    return this.client.post<{ ok: boolean; updated: number }>(
      `/core-api/admin/plugins/bulk-activate`,
      { ids }
    );
  }

  bulkDeactivatePlugins(ids: string[]) {
    return this.client.post<{ ok: boolean; updated: number }>(
      `/core-api/admin/plugins/bulk-activate`, // mesmo endpoint
      { ids, active: false }
    );
  }

  /* =========================
    Routes Actions
  ========================= */

  listRoutes(appId: string, options?: ListQueryOptions) {
    const qs = this.buildQuery(options);
    return this.client.get<PaginatedResponse<AdminAppRoute>>(
      `/core-api/admin/apps/${appId}/routes${qs}`
    );
  }

  updateRoute(routeId: string, payload: Partial<AdminAppRoute>) {
    return this.client.put<{ ok: boolean }>(
      `/core-api/admin/apps/routes/${routeId}`,
      payload
    );
  }

  deleteRoute(routeId: string) {
    return this.client.delete<{ ok: boolean }>(
      `/core-api/admin/apps/routes/${routeId}`
    );
  }

  bulkDeactivateRoutes(ids: string[]) {
    return this.client.post<{ ok: boolean; updated: number }>(
      `/core-api/admin/apps/routes/bulk-deactivate`,
      { ids }
    );
  }

  bulkDeleteRoutes(ids: string[]) {
    return this.client.post<{ ok: boolean; deleted: number }>(
      `/core-api/admin/apps/routes/bulk-delete`,
      { ids }
    );
  }

  bulkActivateRoutes(ids: string[]) {
    return this.client.post<{ ok: boolean; updated: number }>(
      `/core-api/admin/apps/routes/bulk-activate`,
      { ids }
    );
  }

  // RBAC - Role Permissions (GET)
  getRolePermissions(roleId: string) {
    return this.client.get<{
      data: any[]; // depende do formato do backend
      pagination: PaginationMeta;
    }>(`/core-api/admin/rbac/roles/${roleId}/permissions?page=1&page_size=999`);
  }

  // RBAC - Group Roles (GET)
  getGroupRoles(groupId: string) {
    return this.client.get<{
      data: any[];
      pagination: PaginationMeta;
    }>(`/core-api/admin/rbac/groups/${groupId}/roles?page=1&page_size=999`);
  }


}


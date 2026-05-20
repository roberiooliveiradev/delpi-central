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

export type ListQueryOptions = {
  page?: number;
  pageSize?: number;
  q?: string;
  sort?: string;
  direction?: "asc" | "desc";
};

export type ListUsersQueryOptions = ListQueryOptions & {
  isSuperadmin?: boolean;
  online?: "true" | "false";
  roleId?: string;
  groupId?: string;
};

export type AdminUser = {
  id: string;
  name: string;
  email: string;
  active?: boolean;
  is_superadmin: boolean;
  last_login_at?: string | null;
  birth_date?: string | null;
};

export type OnlineUserPresence = {
  userId: string;
  name?: string | null;
  email?: string | null;
  active?: boolean | null;
  connectionCount: number;
  connectedAt: string;
  lastSeenAt: string;
};

export type OnlineUsersPresenceResponse = {
  items: OnlineUserPresence[];
  total: number;
  ttlSeconds: number;
  enabled: boolean;
};

export type AdminStatisticsRankItem = {
  id: string;
  name: string;
  count: number;
};

export type AdminStatisticsTypeCount = {
  type: string;
  count: number;
};

export type AdminAppUsageLiveUser = {
  id: string;
  name?: string | null;
  email?: string | null;
};

export type AdminAppUsageLiveItem = {
  appId: string;
  appName: string;
  userCount: number;
  sessionCount: number;
  users: AdminAppUsageLiveUser[];
  lastSeenAt: string;
};

export type AdminAppUsageSnapshot = {
  enabled: boolean;
  ttlSeconds: number;
  inUseNow: number;
  live: AdminAppUsageLiveItem[];
  topUsed: AdminStatisticsRankItem[];
  ghostApps: AdminStatisticsRankItem[];
  usedInPeriod: number;
};

export type AdminStatistics = {
  generatedAt: string;
  users: {
    total: number;
    active: number;
    inactive: number;
    superadmins: number;
    online: number;
    withBirthDate: number;
    loggedInLast7Days: number;
    loggedInLast30Days: number;
    withoutDirectRoles: number;
    withoutGroups: number;
  };
  apps: {
    total: number;
    active: number;
    inactive: number;
    routesTotal: number;
    routesActive: number;
    routesInactive: number;
    byType: AdminStatisticsTypeCount[];
    usage: AdminAppUsageSnapshot;
  };
  roles: {
    total: number;
    system: number;
    custom: number;
    withoutUsers: number;
    topByUsers: AdminStatisticsRankItem[];
  };
  groups: {
    total: number;
    active: number;
    inactive: number;
    withoutUsers: number;
    topByUsers: AdminStatisticsRankItem[];
    topByRoles: AdminStatisticsRankItem[];
  };
  permissions: {
    total: number;
  };
  notifications: {
    dispatchesTotal: number;
    dispatchesPending: number;
    dispatchesCompleted: number;
    dispatchesFailed: number;
  };
  assignments: {
    userRoles: number;
    userGroups: number;
    groupRoles: number;
    rolePermissions: number;
  };
};

export type AdminRole = {
  id: string;
  name: string;
  description?: string | null;
};

export type AdminGroup = {
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

export type AdminPermissionUsageRole = {
  id: string;
  name: string;
  description?: string | null;
};

export type AdminPermissionUsageGroup = {
  id: string;
  name: string;
  description?: string | null;
  via_roles: {
    id: string;
    name: string;
  }[];
};

export type AdminPermissionUsage = {
  permission: AdminPermission;
  roles: AdminPermissionUsageRole[];
  groups: AdminPermissionUsageGroup[];
};

export type AdminApp = {
  id: string;
  name: string;
  description?: string | null;
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

export type CreateRoutePayload = {
  path: string;
  label: string;
  icon: string;
  order: number;
  permissionCode?: string | null;
  showInMenu?: boolean;
  active?: boolean;
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

    const qs = params.toString();

    return qs ? `?${qs}` : "";
  }

  /* =========================
     Plugins / Manifest
  ========================= */

  getPluginManifest(appId: string) {
    return this.client.get<any>(
      `/core-api/admin/apps/${appId}/manifest`
    );
  }

  registerManifest(manifest: any) {
    return this.client.post<RegisterPluginResponse>(
      `/core-api/admin/apps/register`,
      manifest
    );
  }

  updatePluginManifest(appId: string, manifest: any) {
    return this.client.put<{ ok: boolean }>(
      `/core-api/admin/apps/${appId}/manifest`,
      manifest
    );
  }

  deletePlugin(appId: string) {
    return this.client.delete<{ ok: boolean }>(
      `/core-api/admin/apps/${appId}`
    );
  }

  bulkUnregisterPlugins(ids: string[]) {
    return this.client.post<{ ok: boolean; deleted: number }>(
      `/core-api/admin/apps/bulk-unregister`,
      { ids }
    );
  }

  /* =========================
     Plugin Versions / Rollback
  ========================= */

  listPluginVersions(appId: string) {
    return this.client.get<PluginVersion[]>(
      `/core-api/admin/apps/${appId}/versions`
    );
  }

  rollbackPlugin(appId: string, version: string) {
    return this.client.post<RollbackPluginResponse>(
      `/core-api/admin/apps/${appId}/rollback`,
      { version }
    );
  }

  /* =========================
     Apps
  ========================= */

  listApps(options?: ListQueryOptions) {
    const qs = this.buildQuery(options);

    return this.client.get<PaginatedResponse<AdminApp>>(
      `/core-api/admin/apps${qs}`
    );
  }

  updateApp(appId: string, payload: Partial<AdminApp>) {
    return this.client.put<{ ok: boolean }>(
      `/core-api/admin/apps/${appId}`,
      payload
    );
  }

  setPluginActive(appId: string, active: boolean) {
    return this.client.post<{ ok: boolean }>(
      `/core-api/admin/apps/${appId}/active`,
      { active }
    );
  }

  bulkActivatePlugins(ids: string[]) {
    return this.client.post<{ ok: boolean; updated: number }>(
      `/core-api/admin/apps/bulk-activate`,
      { ids, active: true }
    );
  }

  bulkDeactivatePlugins(ids: string[]) {
    return this.client.post<{ ok: boolean; updated: number }>(
      `/core-api/admin/apps/bulk-activate`,
      { ids, active: false }
    );
  }

  /* =========================
     App Routes
  ========================= */

  listRoutes(appId: string, options?: ListQueryOptions) {
    const qs = this.buildQuery(options);

    return this.client.get<AdminAppRoute[]>(
      `/core-api/admin/apps/${appId}/routes${qs}`
    );
  }

  createRoute(appId: string, payload: CreateRoutePayload) {
    return this.client.post<AdminAppRoute>(
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

  deleteRoute(routeId: string) {
    return this.client.delete<{ ok: boolean }>(
      `/core-api/admin/apps/routes/${routeId}`
    );
  }

  bulkDeleteRoutes(ids: string[]) {
    return this.client.post<{ ok: boolean; deleted: number }>(
      `/core-api/admin/apps/routes/bulk-delete`,
      { ids }
    );
  }

  /* =========================
     RBAC - Users
  ========================= */

  listUsers(options?: ListUsersQueryOptions) {
    const params = new URLSearchParams();

    if (options?.page) params.append("page", String(options.page));
    if (options?.pageSize) params.append("page_size", String(options.pageSize));
    if (options?.q) params.append("q", options.q);
    if (options?.sort) params.append("sort", options.sort);
    if (options?.direction) params.append("direction", options.direction);
    if (options?.isSuperadmin !== undefined) {
      params.append("is_superadmin", String(options.isSuperadmin));
    }
    if (options?.online) params.append("online", options.online);
    if (options?.roleId) params.append("role_id", options.roleId);
    if (options?.groupId) params.append("group_id", options.groupId);

    const qs = params.toString();

    return this.client.get<PaginatedResponse<AdminUser>>(
      `/core-api/admin/rbac/users${qs ? `?${qs}` : ""}`
    );
  }

  listOnlineUsers() {
    return this.client.get<OnlineUsersPresenceResponse>(
      "/core-api/admin/users/presence",
    );
  }

  getAdminStatistics() {
    return this.client.get<AdminStatistics>("/core-api/admin/statistics");
  }

  getAppUsage() {
    return this.client.get<AdminAppUsageSnapshot>("/core-api/admin/apps/usage");
  }

  updateUser(
    userId: string,
    payload: {
      roleIds?: string[];
      groupIds?: string[];
      is_superadmin?: boolean;
      birthDate?: string | null;
    }
  ) {
    return this.client.put<{ ok: boolean }>(
      `/core-api/admin/rbac/users/${userId}`,
      payload
    );
  }

  deleteUser(userId: string) {
    return this.client.delete<{ ok: boolean }>(
      `/core-api/admin/rbac/users/${userId}`
    );
  }

  bulkDeleteUsers(ids: string[]) {
    return this.client.post<{ ok: boolean; deleted: number; skipped?: number }>(
      `/core-api/admin/rbac/users/bulk-delete`,
      { ids }
    );
  }

  getUserRoles(userId: string) {
    return this.client.get<PaginatedResponse<AdminRole>>(
      `/core-api/admin/rbac/users/${userId}/roles?page=1&page_size=999`
    );
  }

  getUserGroups(userId: string) {
    return this.client.get<PaginatedResponse<AdminGroup>>(
      `/core-api/admin/rbac/users/${userId}/groups?page=1&page_size=999`
    );
  }

  addRoleToUser(userId: string, roleId: string) {
    return this.client.post<{ ok: boolean }>(
      `/core-api/admin/rbac/users/${userId}/roles/${roleId}`,
      {}
    );
  }

  removeRoleFromUser(userId: string, roleId: string) {
    return this.client.delete<{ ok: boolean }>(
      `/core-api/admin/rbac/users/${userId}/roles/${roleId}`
    );
  }

  addGroupToUser(userId: string, groupId: string) {
    return this.client.post<{ ok: boolean }>(
      `/core-api/admin/rbac/users/${userId}/groups/${groupId}`,
      {}
    );
  }

  removeGroupFromUser(userId: string, groupId: string) {
    return this.client.delete<{ ok: boolean }>(
      `/core-api/admin/rbac/users/${userId}/groups/${groupId}`
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
    return this.client.post<{ id: string }>(
      `/core-api/admin/rbac/roles`,
      payload
    );
  }

  updateRole(roleId: string, payload: Partial<AdminRole>) {
    return this.client.put<{ ok: boolean }>(
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
    return this.client.post<{ ok: boolean; deleted: number; skipped?: number }>(
      `/core-api/admin/rbac/roles/bulk-delete`,
      { ids }
    );
  }

  getRolePermissions(roleId: string) {
    return this.client.get<PaginatedResponse<AdminPermission>>(
      `/core-api/admin/rbac/roles/${roleId}/permissions?page=1&page_size=999`
    );
  }

  setRolePermissions(roleId: string, permissionIds: string[]) {
    return this.client.put<{ ok: boolean }>(
      `/core-api/admin/rbac/roles/${roleId}/permissions`,
      { permissionIds }
    );
  }

  addPermissionToRole(roleId: string, permissionId: string) {
    return this.client.post<{ ok: boolean }>(
      `/core-api/admin/rbac/roles/${roleId}/permissions`,
      { id: permissionId }
    );
  }

  removePermissionFromRole(roleId: string, permissionId: string) {
    return this.client.delete<{ ok: boolean }>(
      `/core-api/admin/rbac/roles/${roleId}/permissions/${permissionId}`
    );
  }

  getRoleUsers(roleId: string) {
    return this.client.get<PaginatedResponse<AdminUser>>(
      `/core-api/admin/rbac/roles/${roleId}/users?page=1&page_size=999`
    );
  }

  addUserToRole(roleId: string, userId: string) {
    return this.client.post<{ ok: boolean }>(
      `/core-api/admin/rbac/roles/${roleId}/users/${userId}`,
      {}
    );
  }

  removeUserFromRole(roleId: string, userId: string) {
    return this.client.delete<{ ok: boolean }>(
      `/core-api/admin/rbac/roles/${roleId}/users/${userId}`
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
    return this.client.post<{ id: string }>(
      `/core-api/admin/rbac/groups`,
      payload
    );
  }

  updateGroup(groupId: string, payload: Partial<AdminGroup>) {
    return this.client.put<{ ok: boolean }>(
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
    return this.client.post<{ ok: boolean; deleted: number; skipped?: number }>(
      `/core-api/admin/rbac/groups/bulk-delete`,
      { ids }
    );
  }

  getGroupRoles(groupId: string) {
    return this.client.get<PaginatedResponse<AdminRole>>(
      `/core-api/admin/rbac/groups/${groupId}/roles?page=1&page_size=999`
    );
  }

  setGroupRoles(groupId: string, roleIds: string[]) {
    return this.client.put<{ ok: boolean }>(
      `/core-api/admin/rbac/groups/${groupId}/roles`,
      { roleIds }
    );
  }

  addRoleToGroup(groupId: string, roleId: string) {
    return this.client.post<{ ok: boolean }>(
      `/core-api/admin/rbac/groups/${groupId}/roles/${roleId}`,
      {}
    );
  }

  removeRoleFromGroup(groupId: string, roleId: string) {
    return this.client.delete<{ ok: boolean }>(
      `/core-api/admin/rbac/groups/${groupId}/roles/${roleId}`
    );
  }

  getGroupUsers(groupId: string) {
    return this.client.get<PaginatedResponse<AdminUser>>(
      `/core-api/admin/rbac/groups/${groupId}/users?page=1&page_size=999`
    );
  }

  addUserToGroup(groupId: string, userId: string) {
    return this.client.post<{ ok: boolean }>(
      `/core-api/admin/rbac/groups/${groupId}/users/${userId}`,
      {}
    );
  }

  removeUserFromGroup(groupId: string, userId: string) {
    return this.client.delete<{ ok: boolean }>(
      `/core-api/admin/rbac/groups/${groupId}/users/${userId}`
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

  getPermissionUsage(permissionId: string) {
    return this.client.get<AdminPermissionUsage>(
      `/core-api/admin/rbac/permissions/${permissionId}/usage`
    );
  }
}
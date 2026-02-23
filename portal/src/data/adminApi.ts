// src/data/adminApi.ts

import { ApiClient } from "./apiClient";

/* ======================================================
   Tipos base
====================================================== */

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

/* ======================================================
   RBAC Types
====================================================== */

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

/* ======================================================
   Apps
====================================================== */

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

/* ======================================================
   API
====================================================== */

export class AdminApi {
  private client: ApiClient;

  constructor(client: ApiClient) {
    this.client = client;
  }

  /* ======================================================
     Helpers
  ====================================================== */

  private buildPaginationQuery(
    page?: number,
    pageSize?: number,
    q?: string
  ) {
    const params = new URLSearchParams();

    if (page) params.append("page", String(page));
    if (pageSize) params.append("page_size", String(pageSize));
    if (q) params.append("q", q);

    const queryString = params.toString();
    return queryString ? `?${queryString}` : "";
  }

  /* ======================================================
     RBAC
  ====================================================== */

  listUsers(options?: {
    page?: number;
    pageSize?: number;
    q?: string;
  }) {
    const qs = this.buildPaginationQuery(
      options?.page,
      options?.pageSize,
      options?.q
    );

    return this.client.get<PaginatedResponse<AdminUser>>(
      `/core-api/admin/rbac/users${qs}`
    );
  }

  getUser(userId: string) {
    return this.client.get<AdminUser>(
      `/core-api/admin/rbac/users/${userId}`
    );
  }

  listRoles(options?: {
    page?: number;
    pageSize?: number;
  }) {
    const qs = this.buildPaginationQuery(
      options?.page,
      options?.pageSize
    );

    return this.client.get<PaginatedResponse<AdminRole>>(
      `/core-api/admin/rbac/roles${qs}`
    );
  }

  listPermissions(options?: {
    page?: number;
    pageSize?: number;
  }) {
    const qs = this.buildPaginationQuery(
      options?.page,
      options?.pageSize
    );

    return this.client.get<PaginatedResponse<AdminPermission>>(
      `/core-api/admin/rbac/permissions${qs}`
    );
  }

  listGroups(options?: {
    page?: number;
    pageSize?: number;
  }) {
    const qs = this.buildPaginationQuery(
      options?.page,
      options?.pageSize
    );

    return this.client.get<PaginatedResponse<AdminGroup>>(
      `/core-api/admin/rbac/groups${qs}`
    );
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

  /* ======================================================
     Apps & Routes (mantido igual)
  ====================================================== */


  listApps(options?: { page?: number; pageSize?: number }) {
    const qs = this.buildPaginationQuery(
      options?.page,
      options?.pageSize
  );

  return this.client.get<PaginatedResponse<AdminApp>>(
    `/core-api/admin/apps${qs}`
  );
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

  listRoutes(
    appId: string,
    options?: { page?: number; pageSize?: number }
  ) {
    const qs = this.buildPaginationQuery(
      options?.page,
      options?.pageSize
    );

    return this.client.get<PaginatedResponse<AdminAppRoute>>(
      `/core-api/admin/apps/${appId}/routes${qs}`
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
    return this.client.post<{ ok: boolean }>(
      `/core-api/admin/apps/${appId}/activate`
    );
  }

  deactivateApp(appId: string) {
    return this.client.post<{ ok: boolean }>(
      `/core-api/admin/apps/${appId}/deactivate`
    );
  }

  activateRoute(routeId: string) {
    return this.client.post<{ ok: boolean }>(
      `/core-api/admin/apps/routes/${routeId}/activate`
    );
  }

  deactivateRoute(routeId: string) {
    return this.client.post<{ ok: boolean }>(
      `/core-api/admin/apps/routes/${routeId}/deactivate`
    );
  }
}
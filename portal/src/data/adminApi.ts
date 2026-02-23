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

export type ListQueryOptions = {
  page?: number;
  pageSize?: number;
  q?: string;
  sort?: string;
  direction?: "asc" | "desc";
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
  public client: ApiClient; // 👈 exposto (você já vinha usando)
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
     RBAC
  ========================= */

  listUsers(options?: ListQueryOptions) {
    const qs = this.buildQuery(options);
    return this.client.get<PaginatedResponse<AdminUser>>(
      `/core-api/admin/rbac/users${qs}`
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

  listRoles(options?: ListQueryOptions) {
    const qs = this.buildQuery(options);
    return this.client.get<PaginatedResponse<AdminRole>>(
      `/core-api/admin/rbac/roles${qs}`
    );
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

  listPermissions(options?: ListQueryOptions) {
    const qs = this.buildQuery(options);
    return this.client.get<PaginatedResponse<AdminPermission>>(
      `/core-api/admin/rbac/permissions${qs}`
    );
  }

  listGroups(options?: ListQueryOptions) {
    const qs = this.buildQuery(options);
    return this.client.get<PaginatedResponse<AdminGroup>>(
      `/core-api/admin/rbac/groups${qs}`
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

  deleteApp(appId: string) {
    return this.client.delete<{ ok: boolean }>(
      `/core-api/admin/apps/${appId}`
    );
  }

  bulkDeleteApps(ids: string[]) {
    return this.client.post<{ ok: boolean; deleted: number }>(
      `/core-api/admin/apps/bulk-delete`,
      { ids }
    );
  }

  bulkActivateApps(ids: string[]) {
    return this.client.post<{ ok: boolean; updated: number }>(
      `/core-api/admin/apps/bulk-activate`,
      { ids }
    );
  }

  bulkDeactivateApps(ids: string[]) {
    return this.client.post<{ ok: boolean; updated: number }>(
      `/core-api/admin/apps/bulk-deactivate`,
      { ids }
    );
  }

  /* =========================
     Routes
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
}
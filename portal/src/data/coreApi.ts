// src/data/coreApi.ts

import { ApiClient } from "./apiClient";

export interface MeResponse {
  id: string;
  name: string;
  email: string;
  roles: string[];
  groups: string[];
  permissions: string[];
  is_superadmin?: boolean;
}

export type AppRenderMode =
  | "embedded"
  | "external"
  | "federated";

export interface RouteItem {
  app: string;
  app_name?: string;
  app_icon?: string;

  path: string;
  permission?: string;

  icon?: string;
  label?: string;

  entry?: string;
  showInMenu?: boolean;
  order?: number;
}

export interface AppItem {
  id: string;
  name: string;
  basePath: string;
  icon?: string;

  type: "iframe" | "microfrontend" | "backend-only";

  entryUrl?: string;
  renderMode?: AppRenderMode;

  routes?: RouteItem[];
}

export interface DashboardResponse {
  appsCount: number;
  rolesCount: number;
  permissionsCount: number;
  recentActivity: string[];
}

export interface NotificationItem {
  id: string;
  title?: string | null;
  message: string;
  type: "info" | "success" | "warning" | "error";
  read: boolean;
  createdAt: string;
}

export interface FavoriteAppItem {
  id: string;
  name: string;
  base_path: string;
  icon?: string;
  order_index: number;
}

/**
 * Backend às vezes retorna objeto indexado
 * convertemos para array
 */
function normalizeArray<T>(data: unknown): T[] {
  if (Array.isArray(data)) return data;

  if (data && typeof data === "object") {
    return Object.values(data as Record<string, T>);
  }

  return [];
}

export class CoreApi {
  private client: ApiClient;

  constructor(client: ApiClient) {
    this.client = client;
  }

  // -------------------------------------------------------
  // USER CONTEXT
  // -------------------------------------------------------

  getMe() {
    return this.client.get<MeResponse>("/core-api/me");
  }

  async getApps(): Promise<AppItem[]> {
    const data = await this.client.get<unknown>("/core-api/me/apps");
    return normalizeArray<AppItem>(data);
  }

  // -------------------------------------------------------
  // FAVORITES
  // -------------------------------------------------------

  async getFavoriteApps(): Promise<FavoriteAppItem[]> {
    const data = await this.client.get<unknown>(
      "/core-api/me/apps/favorites"
    );

    return normalizeArray<FavoriteAppItem>(data);
  }

  addFavoriteApp(appId: string) {
    return this.client.post<{ ok: boolean }>(
      `/core-api/me/apps/favorites/${appId}`
    );
  }

  removeFavoriteApp(appId: string) {
    return this.client.delete<{ ok: boolean }>(
      `/core-api/me/apps/favorites/${appId}`
    );
  }

  // -------------------------------------------------------
  // DASHBOARD
  // -------------------------------------------------------

  getDashboard() {
    return this.client.get<DashboardResponse>("/core-api/me/dashboard");
  }

  // -------------------------------------------------------
  // NOTIFICATIONS
  // -------------------------------------------------------

  getNotifications() {
    return this.client.get<NotificationItem[]>(
      "/core-api/me/notifications"
    );
  }

  markNotificationRead(id: string) {
    return this.client.post<{ ok: boolean }>(
      `/core-api/me/notifications/${id}/read`
    );
  }

  markAllNotificationsRead() {
    return this.client.post<{ ok: boolean }>(
      "/core-api/me/notifications/read-all"
    );
  }
}
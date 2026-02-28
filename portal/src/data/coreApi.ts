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
  | "embedded"     // iframe interno (mesmo domínio)
  | "external"     // abre em nova aba
  | "federated";   // microfrontend via Module Federation

export interface AppItem {
  id: string;
  name: string;
  basePath: string;    
  icon?: string | null;
  type: "iframe" | "microfrontend" | "backend-only";
  entryUrl?: string | null;
  renderMode?: AppRenderMode;
}

export interface RouteItem {
  app: string;
  app_name?: string;
  app_icon?: string | null;
  path: string;
  permission: string;
  icon?: string | null;
  label?: string | null;
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

export class CoreApi {
  private client: ApiClient;

  constructor(client: ApiClient) {
    this.client = client;
  }

  getMe() {
    return this.client.get<MeResponse>("/core-api/me");
  }

  getApps() {
    return this.client.get<AppItem[]>("/core-api/me/apps");
  }

  getRoutes() {
    return this.client.get<RouteItem[]>("/core-api/me/routes");
  }

  getDashboard() {
    return this.client.get<DashboardResponse>("/core-api/dashboard");
  }

  getNotifications() {
    return this.client.get<NotificationItem[]>("/core-api/notifications");
  }

  markNotificationRead(id: string) {
    return this.client.post<{ ok: boolean }>(
      `/core-api/notifications/${id}/read`
    );
  }

  markAllNotificationsRead() {
    return this.client.post<{ ok: boolean }>(
      `/core-api/notifications/read-all`
    );
  }

  getFavoriteApps() {
    return this.client.get<FavoriteAppItem[]>(
      "/core-api/me/apps/favorites"
    );
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
}
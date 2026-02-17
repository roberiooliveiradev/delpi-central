// src/data/coreApi.ts

import { ApiClient } from "./apiClient";

export interface MeResponse {
  id: string;
  name: string;
  email: string;
  roles: string[];
  groups: string[];
  permissions: string[];
}

export interface AppItem {
  id: string;
  name: string;
  basePath: string;
  icon?: string;
}

export interface RouteItem {
  app: string;
  path: string;
  permission: string;
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
    return this.client.get<{ ok: boolean }>(`/core-api/notifications/${id}/read`); // se preferir GET
    // melhor: client.post(...) — se você tiver post no ApiClient
  }

  markAllNotificationsRead() {
    return this.client.get<{ ok: boolean }>(`/core-api/notifications/read-all`);
  }
}

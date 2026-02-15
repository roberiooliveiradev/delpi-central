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

}

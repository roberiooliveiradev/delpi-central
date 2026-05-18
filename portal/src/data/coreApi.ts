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

export type NotificationType = "info" | "success" | "warning" | "error";

export type NotificationCategory =
  | "system"
  | "welcome"
  | "birthday"
  | "company_event"
  | "announcement"
  | "custom";

export type NotificationPresentation = "text" | "html" | "template";

export type NotificationTemplateId = string;

export type NotificationTemplateFieldSpec = {
  key: string;
  label: string;
  placeholder?: string;
  required?: boolean;
};

export interface NotificationTemplateDefinition {
  id: NotificationTemplateId;
  label: string;
  category: NotificationCategory;
  defaultType: NotificationType;
  defaultTitle: string;
  defaultMessage: string;
  requiredVars?: string[];
  optionalVars?: string[];
  recipientVars?: string[];
  recipientAutoVars?: string[];
  isSystem?: boolean;
  hint?: string | null;
  fields: NotificationTemplateFieldSpec[];
}

export type NotificationActionType = "portal_route" | "external_url";

export interface NotificationAction {
  type: NotificationActionType;
  label: string;
  target: string;
}

export interface NotificationItem {
  id: string;
  title?: string | null;
  message: string;
  type: NotificationType;
  category: NotificationCategory;
  presentation: NotificationPresentation;
  htmlContent?: string | null;
  icon?: string | null;
  action?: NotificationAction | null;
  metadata?: Record<string, unknown> | null;
  expiresAt?: string | null;
  read: boolean;
  createdAt: string;
}

export interface DispatchNotificationsPayload {
  broadcast?: boolean;
  userIds?: string[];
  emails?: string[];
  title?: string | null;
  message: string;
  type?: NotificationType;
  category?: NotificationCategory;
  presentation?: NotificationPresentation;
  htmlContent?: string | null;
  templateId?: NotificationTemplateId;
  templateVars?: Record<string, string>;
  icon?: string | null;
  action?: {
    type: NotificationActionType | "none";
    label?: string;
    target?: string;
  } | null;
  metadata?: Record<string, unknown>;
  expiresAt?: string | null;
  sourceApp?: string;
}

export interface DispatchNotificationsResponse {
  createdCount: number;
  notificationIds: string[];
}

export type NotificationHistoryStatus = "all" | "unread" | "read";

export interface NotificationHistoryResponse {
  items: NotificationItem[];
  total: number;
  limit: number;
  offset: number;
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

  private normalizeNotificationItem(item: NotificationItem): NotificationItem {
    return {
      ...item,
      category: item.category ?? "system",
      presentation: item.presentation ?? "text",
      type: item.type ?? "info",
      metadata: item.metadata ?? null,
    };
  }

  async getNotifications(): Promise<NotificationItem[]> {
    const data = await this.client.get<unknown>("/core-api/me/notifications");
    const items = normalizeArray<NotificationItem>(data);

    return items.map((item) => this.normalizeNotificationItem(item));
  }

  async getNotificationHistory(params?: {
    status?: NotificationHistoryStatus;
    limit?: number;
    offset?: number;
  }): Promise<NotificationHistoryResponse> {
    const search = new URLSearchParams();
    if (params?.status) {
      search.set("status", params.status);
    }
    if (params?.limit != null) {
      search.set("limit", String(params.limit));
    }
    if (params?.offset != null) {
      search.set("offset", String(params.offset));
    }

    const query = search.toString();
    const path = `/core-api/me/notifications/history${query ? `?${query}` : ""}`;
    const data = await this.client.get<NotificationHistoryResponse>(path);

    return {
      ...data,
      items: (data.items ?? []).map((item) => this.normalizeNotificationItem(item)),
    };
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

  dispatchNotifications(payload: DispatchNotificationsPayload) {
    return this.client.post<DispatchNotificationsResponse>(
      "/core-api/admin/notifications",
      payload
    );
  }

  listNotificationTemplates() {
    return this.client.get<NotificationTemplateDefinition[]>(
      "/core-api/admin/notifications/templates",
    );
  }

  createNotificationTemplate(
    payload: Omit<NotificationTemplateDefinition, "id" | "isSystem">,
  ) {
    return this.client.post<NotificationTemplateDefinition>(
      "/core-api/admin/notifications/templates",
      payload,
    );
  }

  deleteNotificationTemplate(templateId: string) {
    return this.client.delete<{ ok: boolean }>(
      `/core-api/admin/notifications/templates/${templateId}`,
    );
  }
}
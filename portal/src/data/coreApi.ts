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

export interface NotificationPreferencesResponse {
  mutedCategories: NotificationCategory[];
  mutableCategories: NotificationCategory[];
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
  isImportant?: boolean;
  createdAt: string;
}

export interface DispatchNotificationsPayload {
  broadcast?: boolean;
  userIds?: string[];
  emails?: string[];
  roleIds?: string[];
  groupIds?: string[];
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
  scheduledAt?: string | null;
  sourceApp?: string;
}

export interface DispatchNotificationsResponse {
  dispatchId?: string;
  status?: string;
  scheduledAt?: string | null;
  createdCount: number;
  notificationIds: string[];
  recipientCount?: number;
  errorMessage?: string | null;
}

export type NotificationDispatchStatus = "pending" | "processing" | "completed" | "failed";

export interface NotificationDispatchItem {
  id: string;
  createdByUserId?: string | null;
  status: NotificationDispatchStatus;
  scheduledAt?: string | null;
  processedAt?: string | null;
  broadcast: boolean;
  recipientCount: number;
  createdCount: number;
  title?: string | null;
  category: NotificationCategory;
  presentation: NotificationPresentation;
  templateId?: string | null;
  sourceApp?: string | null;
  errorMessage?: string | null;
  createdAt: string;
}

export interface NotificationDispatchListResponse {
  items: NotificationDispatchItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface ProcessPendingDispatchesResponse {
  processed: number;
  completed: number;
  failed: number;
  errors: { dispatchId: string; error: string }[];
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
      isImportant: Boolean(item.isImportant),
    };
  }

  async getNotifications(): Promise<NotificationItem[]> {
    const data = await this.client.get<unknown>("/core-api/me/notifications");
    const items = normalizeArray<NotificationItem>(data);

    return items
      .map((item) => this.normalizeNotificationItem(item))
      .sort((a, b) => {
        if (Boolean(a.isImportant) !== Boolean(b.isImportant)) {
          return a.isImportant ? -1 : 1;
        }
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
      });
  }

  async getNotificationHistory(params?: {
    status?: NotificationHistoryStatus;
    category?: NotificationCategory | "";
    importantOnly?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<NotificationHistoryResponse> {
    const search = new URLSearchParams();
    if (params?.status) {
      search.set("status", params.status);
    }
    if (params?.category) {
      search.set("category", params.category);
    }
    if (params?.importantOnly) {
      search.set("important", "true");
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

  deleteNotification(id: string) {
    return this.client.delete<{ ok: boolean }>(`/core-api/me/notifications/${id}`);
  }

  setNotificationImportant(id: string, isImportant: boolean) {
    return this.client.patch<{ ok: boolean; isImportant: boolean }>(
      `/core-api/me/notifications/${id}/important`,
      { isImportant },
    );
  }

  getNotificationPreferences() {
    return this.client.get<{
      mutedCategories?: NotificationCategory[];
      mutableCategories?: NotificationCategory[];
    }>("/core-api/me/notifications/preferences").then((data) => ({
      mutedCategories: data.mutedCategories ?? [],
      mutableCategories: data.mutableCategories ?? [],
    }));
  }

  updateNotificationPreferences(mutedCategories: NotificationCategory[]) {
    return this.client
      .patch<{
        mutedCategories?: NotificationCategory[];
        mutableCategories?: NotificationCategory[];
      }>("/core-api/me/notifications/preferences", { mutedCategories })
      .then((data) => ({
        mutedCategories: data.mutedCategories ?? [],
        mutableCategories: data.mutableCategories ?? [],
      }));
  }

  dispatchNotifications(payload: DispatchNotificationsPayload) {
    return this.client.post<DispatchNotificationsResponse>(
      "/core-api/admin/notifications",
      payload
    );
  }

  listNotificationDispatches(params?: { limit?: number; offset?: number }) {
    const search = new URLSearchParams();
    if (params?.limit != null) {
      search.set("limit", String(params.limit));
    }
    if (params?.offset != null) {
      search.set("offset", String(params.offset));
    }
    const query = search.toString();
    return this.client.get<NotificationDispatchListResponse>(
      `/core-api/admin/notifications/dispatches${query ? `?${query}` : ""}`,
    );
  }

  processPendingNotificationDispatches(body?: { limit?: number }) {
    return this.client.post<ProcessPendingDispatchesResponse>(
      "/core-api/admin/notifications/dispatches/process-pending",
      body ?? {},
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
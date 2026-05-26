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
  | "access"
  | "custom"
  | "controle_mp"
  | "transformometro";

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
  excludedUserIds?: string[];
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

export type NotificationDispatchRevokedFilter = "all" | "active" | "revoked";

export interface ListNotificationDispatchesParams {
  limit?: number;
  offset?: number;
  status?: NotificationDispatchStatus;
  category?: NotificationCategory;
  sourceApp?: string;
  search?: string;
  revoked?: NotificationDispatchRevokedFilter;
  dateFrom?: string;
  dateTo?: string;
}

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
  revokedAt?: string | null;
}

export interface NotificationDispatchRecipient {
  id?: string;
  userId?: string;
  notificationId?: string;
  name: string;
  email: string;
  read?: boolean;
  createdAt?: string | null;
}

export interface NotificationDispatchTargeting {
  broadcast: boolean;
  userIds: string[];
  emails: string[];
  roleIds: string[];
  groupIds: string[];
  excludedUserIds: string[];
  sourceApp?: string | null;
  actionType?: string | null;
  actionLabel?: string | null;
  actionTarget?: string | null;
  metadata?: Record<string, unknown>;
}

export interface NotificationDispatchCreatedBy {
  id: string;
  name: string;
  email: string;
}

export interface NotificationDispatchDetail extends NotificationDispatchItem {
  payload: Record<string, unknown>;
  notificationIds: string[];
  createdBy?: NotificationDispatchCreatedBy | null;
  targeting: NotificationDispatchTargeting;
  intendedRecipients: NotificationDispatchRecipient[];
  eligibleRecipientCount?: number | null;
  deliveredRecipients: NotificationDispatchRecipient[];
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

// -------------------------------------------------------
// LGPD TYPES
// -------------------------------------------------------

export interface ConsentItem {
  id: string;
  purpose: string;
  granted: boolean;
  grantedAt: string | null;
  revokedAt: string | null;
}

export interface PrivacyInfoRaw {
  dpo: { name: string; email: string };
  privacyPolicyUrl: string;
  consentPurposes: Record<string, string>;
  dataRetentionDays: Record<string, number>;
  rights: string[];
}

export interface PrivacyInfo {
  dpo: { name: string; email: string };
  privacy_policy_url: string;
  consent_purposes: { key: string; label: string }[];
  retention_periods: Record<string, string>;
  data_subject_rights: string[];
}

export interface DataExportResponse {
  exportDate: string;
  profile: Record<string, unknown>;
  consents: Record<string, unknown>[];
  notifications: Record<string, unknown>[];
  usageEvents: Record<string, unknown>[];
  auditLogs: Record<string, unknown>[];
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

  // -------------------------------------------------------
  // LGPD — CONSENTS
  // -------------------------------------------------------

  async getConsents(): Promise<ConsentItem[]> {
    const data = await this.client.get<{ items?: unknown }>("/core-api/me/consents");
    return normalizeArray<ConsentItem>(data?.items ?? data);
  }

  grantConsent(purpose: string) {
    return this.client.post<ConsentItem>("/core-api/me/consents", { purpose });
  }

  revokeConsent(purpose: string) {
    return this.client.delete<ConsentItem>(`/core-api/me/consents/${purpose}`);
  }

  // -------------------------------------------------------
  // LGPD — PRIVACY & DATA EXPORT
  // -------------------------------------------------------

  async getPrivacyInfo(): Promise<PrivacyInfo> {
    const raw = await this.client.get<PrivacyInfoRaw>("/core-api/me/privacy");
    return {
      dpo: raw.dpo,
      privacy_policy_url: raw.privacyPolicyUrl ?? "",
      consent_purposes: Object.entries(raw.consentPurposes ?? {}).map(
        ([key, label]) => ({ key, label }),
      ),
      retention_periods: Object.fromEntries(
        Object.entries(raw.dataRetentionDays ?? {}).map(
          ([k, v]) => [k, `${v} dias`],
        ),
      ),
      data_subject_rights: raw.rights ?? [],
    };
  }

  getDataExport() {
    return this.client.get<DataExportResponse>("/core-api/me/data-export");
  }

  dispatchNotifications(payload: DispatchNotificationsPayload) {
    return this.client.post<DispatchNotificationsResponse>(
      "/core-api/admin/notifications",
      payload
    );
  }

  resolveNotificationRecipients(
    payload: Pick<
      DispatchNotificationsPayload,
      "roleIds" | "groupIds" | "excludedUserIds" | "broadcast" | "userIds" | "emails" | "message"
    >,
  ) {
    return this.client.post<{ users: { id: string; name: string; email: string }[]; total: number }>(
      "/core-api/admin/notifications/resolve-recipients",
      payload,
    );
  }

  getNotificationDispatch(dispatchId: string) {
    return this.client.get<NotificationDispatchDetail>(
      `/core-api/admin/notifications/dispatches/${dispatchId}`,
    );
  }

  deleteNotificationDispatch(dispatchId: string) {
    return this.client.delete<{
      ok: boolean;
      deletedDispatch: boolean;
      deletedNotifications: number;
    }>(`/core-api/admin/notifications/dispatches/${dispatchId}`);
  }

  bulkDeleteNotificationDispatches(dispatchIds: string[]) {
    return this.client.post<{
      ok: boolean;
      requested: number;
      revoked: number;
      deletedNotifications: number;
      deletedDispatches: number;
      errors: { dispatchId: string; error: string }[];
    }>("/core-api/admin/notifications/dispatches/bulk-delete", { dispatchIds });
  }

  updateScheduledNotificationDispatch(
    dispatchId: string,
    payload: DispatchNotificationsPayload,
  ) {
    return this.client.put<NotificationDispatchItem>(
      `/core-api/admin/notifications/dispatches/${dispatchId}`,
      payload,
    );
  }

  listNotificationDispatches(params?: ListNotificationDispatchesParams) {
    const search = new URLSearchParams();
    if (params?.limit != null) {
      search.set("limit", String(params.limit));
    }
    if (params?.offset != null) {
      search.set("offset", String(params.offset));
    }
    if (params?.status) {
      search.set("status", params.status);
    }
    if (params?.category) {
      search.set("category", params.category);
    }
    if (params?.sourceApp) {
      search.set("sourceApp", params.sourceApp);
    }
    if (params?.search) {
      search.set("search", params.search);
    }
    if (params?.revoked) {
      search.set("revoked", params.revoked);
    }
    if (params?.dateFrom) {
      search.set("dateFrom", params.dateFrom);
    }
    if (params?.dateTo) {
      search.set("dateTo", params.dateTo);
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
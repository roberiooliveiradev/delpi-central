export type NotificationType = "info" | "success" | "warning" | "error";

export type NotificationItem = {
  id: string;
  title?: string | null;
  message: string;
  type: NotificationType;
  read: boolean;
  createdAt: string;
};

export type DispatchNotificationsPayload = {
  broadcast?: boolean;
  userIds?: string[];
  emails?: string[];
  title?: string | null;
  message: string;
  type?: NotificationType;
  sourceApp?: string;
};

export type DispatchNotificationsResponse = {
  createdCount: number;
  notificationIds: string[];
};

type TokenProvider = () => string | undefined | Promise<string | undefined>;

type CoreApiOptions = {
  getAccessToken?: TokenProvider;
};

const CORE_API_BASE_URL = "/core-api";

async function getAuthHeaders(options: CoreApiOptions): Promise<HeadersInit> {
  const token = await options.getAccessToken?.();

  if (!token) {
    return {
      "Content-Type": "application/json",
    };
  }

  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    const message =
      payload?.errors?.[0]?.message ??
      payload?.message ??
      `Request failed (${response.status})`;

    throw new Error(message);
  }

  return payload as T;
}

function normalizeNotifications(data: unknown): NotificationItem[] {
  if (!Array.isArray(data)) {
    return [];
  }

  return data as NotificationItem[];
}

export async function listUnreadNotifications(
  options: CoreApiOptions,
): Promise<NotificationItem[]> {
  const response = await fetch(`${CORE_API_BASE_URL}/me/notifications`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  const data = await parseJsonResponse<unknown>(response);
  return normalizeNotifications(data);
}

export async function markNotificationRead(
  notificationId: string,
  options: CoreApiOptions,
): Promise<void> {
  const response = await fetch(
    `${CORE_API_BASE_URL}/me/notifications/${notificationId}/read`,
    {
      method: "POST",
      headers: await getAuthHeaders(options),
    },
  );

  await parseJsonResponse<{ ok: boolean }>(response);
}

export async function markAllNotificationsRead(options: CoreApiOptions): Promise<void> {
  const response = await fetch(`${CORE_API_BASE_URL}/me/notifications/read-all`, {
    method: "POST",
    headers: await getAuthHeaders(options),
  });

  await parseJsonResponse<{ ok: boolean }>(response);
}

export async function dispatchAdminNotifications(
  payload: DispatchNotificationsPayload,
  options: CoreApiOptions,
): Promise<DispatchNotificationsResponse> {
  const response = await fetch(`${CORE_API_BASE_URL}/admin/notifications`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<DispatchNotificationsResponse>(response);
}

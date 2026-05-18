import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  listUnreadNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  type NotificationItem,
} from "../../data/api/coreApi";

type UseChatNotificationsOptions = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  pollIntervalMs?: number;
};

const DEFAULT_POLL_INTERVAL_MS = 60_000;

export function useChatNotifications({
  getAccessToken,
  pollIntervalMs = DEFAULT_POLL_INTERVAL_MS,
}: UseChatNotificationsOptions) {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadInFlightRef = useRef(false);

  const apiOptions = useMemo(() => ({ getAccessToken }), [getAccessToken]);

  const unreadCount = useMemo(
    () => notifications.filter((item) => !item.read).length,
    [notifications],
  );

  const reload = useCallback(async () => {
    if (!getAccessToken) {
      return;
    }

    const token = await getAccessToken();
    if (!token) {
      setNotifications([]);
      return;
    }

    if (loadInFlightRef.current) {
      return;
    }

    loadInFlightRef.current = true;
    setIsLoading(true);
    setError(null);

    try {
      const items = await listUnreadNotifications(apiOptions);
      setNotifications(items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar notificações");
    } finally {
      loadInFlightRef.current = false;
      setIsLoading(false);
    }
  }, [apiOptions, getAccessToken]);

  const markRead = useCallback(
    async (notificationId: string) => {
      await markNotificationRead(notificationId, apiOptions);
      setNotifications((current) => current.filter((item) => item.id !== notificationId));
    },
    [apiOptions],
  );

  const markAllRead = useCallback(async () => {
    await markAllNotificationsRead(apiOptions);
    setNotifications([]);
  }, [apiOptions]);

  useEffect(() => {
    void reload();
  }, [reload]);

  useEffect(() => {
    if (!pollIntervalMs) {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      void reload();
    }, pollIntervalMs);

    const handleFocus = () => {
      void reload();
    };

    window.addEventListener("focus", handleFocus);

    return () => {
      window.clearInterval(intervalId);
      window.removeEventListener("focus", handleFocus);
    };
  }, [pollIntervalMs, reload]);

  return {
    notifications,
    unreadCount,
    isLoading,
    error,
    reload,
    markRead,
    markAllRead,
  };
}

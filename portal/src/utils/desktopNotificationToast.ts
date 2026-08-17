/**
 * Toasts do sistema operacional via Web Notification API.
 * Dedup por id em sessionStorage; preferência local em localStorage.
 */

export const DESKTOP_TOASTS_ENABLED_KEY = "delpi.notifications.desktopToastsEnabled";
const TOASTED_IDS_KEY = "delpi.notifications.desktopToastIds";
const MAX_TOASTED_IDS = 200;

export type DesktopToastNotification = {
  id: string;
  title?: string | null;
  message: string;
  category?: string;
  actionType?: string | null;
  actionTarget?: string | null;
};

export function isDesktopNotificationSupported(): boolean {
  return typeof window !== "undefined" && "Notification" in window;
}

export function getDesktopNotificationPermission(): NotificationPermission | "unsupported" {
  if (!isDesktopNotificationSupported()) return "unsupported";
  return Notification.permission;
}

export function isDesktopToastsEnabled(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return window.localStorage.getItem(DESKTOP_TOASTS_ENABLED_KEY) === "true";
  } catch {
    return false;
  }
}

export function setDesktopToastsEnabled(enabled: boolean): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(DESKTOP_TOASTS_ENABLED_KEY, enabled ? "true" : "false");
  } catch {
    /* ignore quota / private mode */
  }
}

export async function requestDesktopNotificationPermission(): Promise<
  NotificationPermission | "unsupported"
> {
  if (!isDesktopNotificationSupported()) return "unsupported";
  if (Notification.permission === "granted") return "granted";
  if (Notification.permission === "denied") return "denied";
  try {
    return await Notification.requestPermission();
  } catch {
    return Notification.permission;
  }
}

function readToastedIds(): Set<string> {
  if (typeof window === "undefined") return new Set();
  try {
    const raw = window.sessionStorage.getItem(TOASTED_IDS_KEY);
    if (!raw) return new Set();
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return new Set();
    return new Set(parsed.filter((id): id is string => typeof id === "string" && id.length > 0));
  } catch {
    return new Set();
  }
}

function writeToastedIds(ids: Set<string>): void {
  if (typeof window === "undefined") return;
  try {
    const list = Array.from(ids);
    const trimmed = list.length > MAX_TOASTED_IDS ? list.slice(list.length - MAX_TOASTED_IDS) : list;
    window.sessionStorage.setItem(TOASTED_IDS_KEY, JSON.stringify(trimmed));
  } catch {
    /* ignore */
  }
}

function markToasted(id: string): void {
  const ids = readToastedIds();
  ids.add(id);
  writeToastedIds(ids);
}

function alreadyToasted(id: string): boolean {
  return readToastedIds().has(id);
}

/**
 * Seed: marca ids já conhecidos sem exibir toast (primeira carga da sessão).
 */
export function seedDesktopToastSeenIds(notifications: DesktopToastNotification[]): void {
  const ids = readToastedIds();
  let changed = false;
  for (const item of notifications) {
    if (!item?.id || ids.has(item.id)) continue;
    ids.add(item.id);
    changed = true;
  }
  if (changed) writeToastedIds(ids);
}

export function showDesktopNotificationToast(
  notification: DesktopToastNotification,
  options?: { onActivate?: (item: DesktopToastNotification) => void },
): boolean {
  if (!isDesktopNotificationSupported()) return false;
  if (!isDesktopToastsEnabled()) return false;
  if (Notification.permission !== "granted") return false;
  if (!notification?.id || alreadyToasted(notification.id)) return false;

  const title = (notification.title || "").trim() || "Minha DELPI";
  const body = (notification.message || "").trim().slice(0, 180);
  try {
    const toast = new Notification(title, {
      body,
      tag: notification.id,
      renotify: false,
    });
    markToasted(notification.id);
    toast.onclick = () => {
      try {
        window.focus();
      } catch {
        /* ignore */
      }
      options?.onActivate?.(notification);
      toast.close();
    };
    return true;
  } catch {
    return false;
  }
}

/**
 * Exibe toast para notificações novas (ids ainda não vistos nesta sessão).
 * Na primeira chamada após seed, só ids realmente novos disparam toast.
 */
export function showDesktopToastsForNewNotifications(
  notifications: DesktopToastNotification[],
  options?: { onActivate?: (item: DesktopToastNotification) => void; seedIfEmpty?: boolean },
): number {
  if (!isDesktopNotificationSupported()) return 0;
  if (!isDesktopToastsEnabled()) return 0;
  if (Notification.permission !== "granted") return 0;

  const known = readToastedIds();
  if (options?.seedIfEmpty && known.size === 0) {
    seedDesktopToastSeenIds(notifications);
    return 0;
  }

  let shown = 0;
  for (const item of notifications) {
    if (showDesktopNotificationToast(item, options)) {
      shown += 1;
    }
  }
  return shown;
}

import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertTriangle, X } from "lucide-react";

import { AuthContext } from "../../state/AuthContext";
import type { NotificationItem } from "../../data/coreApi";
import {
  resolveNotificationPreferenceDisplay,
} from "../../utils/notificationCatalog";
import { useNotificationCatalog } from "../../state/NotificationCatalogContext";
import { executeNotificationAction } from "../../utils/notificationNavigation";
import { shouldOpenAppLauncher, openAppLauncher } from "../../utils/appLauncher";
import {
  clearImportantNotificationSnooze,
  isImportantNotificationSnoozed,
  readImportantNotificationSnoozeUntil,
  shouldBreakImportantNotificationSnooze,
  snoozeImportantNotificationOverlay,
} from "../../utils/importantNotificationSnooze";
import { playImportantNotificationChime } from "../../utils/importantNotificationChime";
import { resolveNotificationSeverityTone } from "../../utils/notificationSeverityTone";
import { Button } from "../../ui-kit";

import "./ImportantNotificationAttention.css";

function normalizeAppPath(basePath: string): string {
  const normalized = basePath.startsWith("/") ? basePath : `/${basePath}`;
  return normalized.replace(/\/+$/, "") || "/";
}

function sortByCreatedDesc(a: NotificationItem, b: NotificationItem): number {
  return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
}

function formatRelativeCreatedAt(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const diffMs = Date.now() - date.getTime();
  const minutes = Math.floor(diffMs / 60_000);
  if (minutes < 1) return "agora";
  if (minutes < 60) return `há ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `há ${hours} h`;
  const days = Math.floor(hours / 24);
  return `há ${days} d`;
}

/**
 * Painel de atenção para notificações importantes não lidas.
 * Persiste até ACK / abrir app / adiar (não auto-dismiss como o tour).
 */
export function ImportantNotificationAttention() {
  const navigate = useNavigate();
  const { notifications, apps, markNotificationRead } = useContext(AuthContext);
  const { catalog } = useNotificationCatalog();
  const [snoozedUntil, setSnoozedUntil] = useState<number | null>(() =>
    readImportantNotificationSnoozeUntil(),
  );
  const [tick, setTick] = useState(0);

  const importantUnread = useMemo(
    () =>
      notifications
        .filter((item) => !item.read && Boolean(item.isImportant))
        .sort(sortByCreatedDesc),
    [notifications],
  );

  useEffect(() => {
    const ids = importantUnread.map((item) => item.id);
    if (shouldBreakImportantNotificationSnooze(ids)) {
      clearImportantNotificationSnooze();
      setSnoozedUntil(null);
    }
  }, [importantUnread]);

  useEffect(() => {
    if (snoozedUntil == null) return;
    const remaining = snoozedUntil - Date.now();
    if (remaining <= 0) {
      clearImportantNotificationSnooze();
      setSnoozedUntil(null);
      return;
    }
    const timer = window.setTimeout(() => {
      clearImportantNotificationSnooze();
      setSnoozedUntil(null);
      setTick((value) => value + 1);
    }, remaining);
    return () => window.clearTimeout(timer);
  }, [snoozedUntil]);

  const appBasePaths = useMemo(
    () => apps.map((item) => normalizeAppPath(item.basePath)),
    [apps],
  );

  const queue = useMemo(() => {
    void tick;
    if (snoozedUntil != null && snoozedUntil > Date.now()) {
      return [] as NotificationItem[];
    }
    return importantUnread;
  }, [importantUnread, snoozedUntil, tick]);

  const current = queue[0] ?? null;
  const othersCount = Math.max(0, queue.length - 1);

  useEffect(() => {
    if (!current?.id) return;
    void playImportantNotificationChime({ notificationId: current.id });
  }, [current?.id]);

  const display = useMemo(() => {
    if (!current) return null;
    return resolveNotificationPreferenceDisplay(current.category, catalog, apps);
  }, [current, catalog, apps]);

  const handleSnooze = useCallback(() => {
    const until = snoozeImportantNotificationOverlay(importantUnread.map((item) => item.id));
    setSnoozedUntil(until);
  }, [importantUnread]);

  const handleMarkRead = useCallback(async () => {
    if (!current) return;
    await markNotificationRead(current.id);
  }, [current, markNotificationRead]);

  const handleOpenApp = useCallback(async () => {
    if (!current) return;
    const action = current.action;
    if (!action) {
      await markNotificationRead(current.id);
      navigate("/notifications");
      return;
    }
    if (shouldOpenAppLauncher(action, current.metadata)) {
      openAppLauncher();
      await markNotificationRead(current.id);
      return;
    }
    executeNotificationAction(action, current.metadata, { appBasePaths });
    if (action.type === "portal_route" && action.target) {
      const target = action.target.startsWith("/") ? action.target : `/${action.target}`;
      navigate(target);
    }
    await markNotificationRead(current.id);
  }, [appBasePaths, current, markNotificationRead, navigate]);

  if (!current || !display) {
    return null;
  }

  const title = (current.title || "").trim() || display.notificationName;
  const message = (current.message || "").trim();
  const severity = resolveNotificationSeverityTone(current.type);

  return (
    <div
      className="important-notification-attention"
      role="alertdialog"
      aria-labelledby="important-notification-attention-title"
      aria-describedby="important-notification-attention-body"
    >
      <div
        className={[
          "important-notification-attention__panel",
          `important-notification-attention__panel--${severity.cssModifier}`,
        ].join(" ")}
        data-tone={severity.tone}
      >
        <header className="important-notification-attention__header">
          <span className="important-notification-attention__badge" aria-hidden="true">
            <AlertTriangle size={20} />
          </span>
          <span
            id="important-notification-attention-title"
            className="important-notification-attention__eyebrow"
          >
            {severity.attentionEyebrow}
          </span>
          <button
            type="button"
            className="important-notification-attention__dismiss"
            onClick={handleSnooze}
            aria-label="Adiar alerta por 15 minutos"
            title="Adiar por 15 minutos"
          >
            <X size={16} />
          </button>
        </header>

        <div id="important-notification-attention-body" className="important-notification-attention__body">
          <h3 className="important-notification-attention__title">{title}</h3>
          {message ? (
            <p className="important-notification-attention__message">{message}</p>
          ) : null}
          <p className="important-notification-attention__meta">
            {display.applicationName}
            {current.createdAt ? ` · ${formatRelativeCreatedAt(current.createdAt)}` : null}
          </p>
        </div>

        <footer className="important-notification-attention__footer">
          <Button type="button" variant="ghost" size="md" onClick={() => void handleMarkRead()}>
            Marcar como lida
          </Button>
          <Button type="button" variant="primary" size="md" onClick={() => void handleOpenApp()}>
            Abrir aplicativo
          </Button>
        </footer>

        {othersCount > 0 ? (
          <p className="important-notification-attention__queue" role="status">
            +{othersCount} outra{othersCount === 1 ? "" : "s"} importante
            {othersCount === 1 ? "" : "s"}
          </p>
        ) : null}
      </div>
    </div>
  );
}

/** True when the sidebar bell should soft-pulse for unread important (not snoozed). */
export function hasActiveImportantNotificationAttention(
  notifications: NotificationItem[],
  now = Date.now(),
): boolean {
  const importantUnreadIds = notifications
    .filter((item) => !item.read && Boolean(item.isImportant))
    .map((item) => item.id);
  if (importantUnreadIds.length === 0) return false;
  if (shouldBreakImportantNotificationSnooze(importantUnreadIds, now)) return true;
  if (isImportantNotificationSnoozed(now)) return false;
  return true;
}

import { Bell, CheckCheck } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import type { NotificationItem } from "../../../data/api/coreApi";

import "./ChatNotificationBell.css";

type ChatNotificationBellProps = {
  notifications: NotificationItem[];
  unreadCount: number;
  isLoading?: boolean;
  error?: string | null;
  onReload: () => Promise<void>;
  onMarkRead: (notificationId: string) => Promise<void>;
  onMarkAllRead: () => Promise<void>;
};

function formatRelativeTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  const diffMs = Date.now() - date.getTime();
  const diffMinutes = Math.floor(diffMs / 60_000);

  if (diffMinutes < 1) {
    return "agora";
  }

  if (diffMinutes < 60) {
    return `${diffMinutes} min`;
  }

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours} h`;
  }

  return date.toLocaleDateString("pt-BR");
}

export function ChatNotificationBell({
  notifications,
  unreadCount,
  isLoading,
  error,
  onReload,
  onMarkRead,
  onMarkAllRead,
}: ChatNotificationBellProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) {
      return undefined;
    }

    void onReload();

    const handlePointerDown = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, [isOpen, onReload]);

  return (
    <div className="mdc-notification-bell" ref={containerRef}>
      <button
        type="button"
        className="mdc-notification-bell__trigger"
        aria-label="Notificações"
        aria-expanded={isOpen}
        onClick={() => setIsOpen((current) => !current)}
      >
        <Bell size={18} aria-hidden="true" />
        {unreadCount > 0 ? (
          <span className="mdc-notification-bell__badge" aria-hidden="true">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        ) : null}
      </button>

      {isOpen ? (
        <div className="mdc-notification-bell__panel" role="dialog" aria-label="Notificações">
          <header className="mdc-notification-bell__header">
            <strong>Notificações</strong>
            {notifications.length > 0 ? (
              <button
                type="button"
                className="mdc-notification-bell__mark-all"
                onClick={() => void onMarkAllRead()}
              >
                <CheckCheck size={14} aria-hidden="true" />
                Marcar todas
              </button>
            ) : null}
          </header>

          {isLoading ? <p className="mdc-notification-bell__hint">Carregando...</p> : null}
          {error ? <p className="mdc-notification-bell__error">{error}</p> : null}

          {!isLoading && notifications.length === 0 ? (
            <p className="mdc-notification-bell__hint">Nenhuma notificação pendente.</p>
          ) : null}

          <ul className="mdc-notification-bell__list">
            {notifications.map((notification) => (
              <li key={notification.id}>
                <button
                  type="button"
                  className={`mdc-notification-bell__item mdc-notification-bell__item--${notification.type}`}
                  onClick={() => void onMarkRead(notification.id)}
                >
                  <span className="mdc-notification-bell__item-title">
                    {notification.title || "Notificação"}
                  </span>
                  <span className="mdc-notification-bell__item-message">{notification.message}</span>
                  <span className="mdc-notification-bell__item-time">
                    {formatRelativeTime(notification.createdAt)}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

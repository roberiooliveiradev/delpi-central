// src/components/notifications/NotificationCard.tsx

import {
  Bell,
  Cake,
  Calendar,
  Megaphone,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

import type { NotificationCategory, NotificationItem } from "../../data/coreApi";
import { executeNotificationAction } from "../../utils/notificationNavigation";
import { NotificationTemplateView } from "./NotificationTemplateView";
import {
  getTemplateDefinition,
  getTemplateIdFromMetadata,
  getTemplateVarsFromMetadata,
} from "./notificationTemplates";

import "./NotificationCard.css";

type NotificationCardProps = {
  notification: NotificationItem;
  onMarkRead: (id: string) => void;
  onNavigate?: () => void;
  compact?: boolean;
};

const CATEGORY_ICONS: Record<NotificationCategory, LucideIcon> = {
  system: Bell,
  welcome: Sparkles,
  birthday: Cake,
  company_event: Calendar,
  announcement: Megaphone,
  custom: Bell,
};

const CATEGORY_LABELS: Record<NotificationCategory, string> = {
  system: "Sistema",
  welcome: "Boas-vindas",
  birthday: "Aniversário",
  company_event: "Evento",
  announcement: "Comunicado",
  custom: "Personalizada",
};

export function NotificationCard({
  notification,
  onMarkRead,
  onNavigate,
  compact = false,
}: NotificationCardProps) {
  const Icon = CATEGORY_ICONS[notification.category] ?? Bell;
  const templateId = getTemplateIdFromMetadata(notification.metadata);
  const templateDefinition =
    notification.presentation === "template" ? getTemplateDefinition(templateId) : null;

  function handleOpen() {
    if (notification.action) {
      executeNotificationAction(notification.action);
      onNavigate?.();
    }

    void onMarkRead(notification.id);
  }

  return (
    <article
      className={`notification-card notification-card--${notification.type} ${
        compact ? "notification-card--compact" : ""
      } ${!notification.read ? "notification-card--unread" : ""}`}
    >
      <div className="notification-card__icon" aria-hidden="true">
        <Icon size={18} />
      </div>

      <div className="notification-card__body">
        <div className="notification-card__meta">
          <span className="notification-card__category">
            {CATEGORY_LABELS[notification.category]}
          </span>
          {!notification.read ? <span className="notification-card__dot" /> : null}
        </div>

        {!templateDefinition && notification.title ? (
          <h4 className="notification-card__title">{notification.title}</h4>
        ) : null}

        {templateDefinition ? (
          <NotificationTemplateView
            definition={templateDefinition}
            vars={getTemplateVarsFromMetadata(notification.metadata)}
            compact={compact}
          />
        ) : notification.presentation === "html" && notification.htmlContent ? (
          <div
            className="notification-card__html"
            dangerouslySetInnerHTML={{ __html: notification.htmlContent }}
          />
        ) : (
          <p className="notification-card__message">{notification.message}</p>
        )}

        {notification.action ? (
          <button type="button" className="notification-card__cta" onClick={handleOpen}>
            {notification.action.label}
          </button>
        ) : (
          <button type="button" className="notification-card__cta notification-card__cta--ghost" onClick={handleOpen}>
            Marcar como lida
          </button>
        )}
      </div>
    </article>
  );
}

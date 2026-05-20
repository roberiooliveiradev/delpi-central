// src/components/notifications/NotificationCard.tsx

import { useContext, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  Bell,
  Cake,
  Calendar,
  Check,
  Megaphone,
  MessageCircle,
  Sparkles,
  Star,
  Trash2,
  type LucideIcon,
} from "lucide-react";

import type { NotificationCategory, NotificationItem } from "../../data/coreApi";
import { AuthContext } from "../../state/AuthContext";
import { executeNotificationAction } from "../../utils/notificationNavigation";
import {
  buildPortalEmbeddedPath,
  isEmbeddedDeepLinkNotification,
  normalizeAppPath,
  resolvePortalRoute,
} from "../../utils/embeddedAppNotification";
import { NotificationTemplateView } from "./NotificationTemplateView";
import { NOTIFICATION_TEMPLATE_DEFINITIONS } from "./notificationTemplates";
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
  onDelete?: (id: string) => void;
  onToggleImportant?: (id: string, isImportant: boolean) => void;
  /** @deprecated use variant="compact" */
  compact?: boolean;
  variant?: "compact" | "page";
  /** Seleção em lote (apenas variant="page") */
  selectionEnabled?: boolean;
  selected?: boolean;
  onSelectedChange?: (selected: boolean) => void;
};

function formatNotificationDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  const now = Date.now();
  const diffMs = now - date.getTime();
  const oneDay = 24 * 60 * 60 * 1000;

  if (diffMs < oneDay && date.getDate() === new Date(now).getDate()) {
    return `Hoje, ${date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}`;
  }

  if (diffMs < 7 * oneDay) {
    return date.toLocaleDateString("pt-BR", {
      weekday: "short",
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  return date.toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const CATEGORY_ICONS: Record<NotificationCategory, LucideIcon> = {
  system: Bell,
  welcome: Sparkles,
  birthday: Cake,
  company_event: Calendar,
  announcement: Megaphone,
  custom: Bell,
  controle_mp: MessageCircle,
};

const CATEGORY_LABELS: Record<NotificationCategory, string> = {
  system: "Sistema",
  welcome: "Boas-vindas",
  birthday: "Aniversário",
  company_event: "Evento",
  announcement: "Comunicado",
  custom: "Personalizada",
  controle_mp: "Controle MP",
};

export function NotificationCard({
  notification,
  onMarkRead,
  onNavigate,
  onDelete,
  onToggleImportant,
  compact = false,
  variant,
  selectionEnabled = false,
  selected = false,
  onSelectedChange,
}: NotificationCardProps) {
  const navigate = useNavigate();
  const { apps } = useContext(AuthContext);

  const appBasePaths = useMemo(
    () => apps.map((item) => normalizeAppPath(item.basePath)),
    [apps]
  );

  const layout = variant ?? (compact ? "compact" : "page");
  const isPage = layout === "page";
  const Icon = CATEGORY_ICONS[notification.category] ?? Bell;
  const templateId = getTemplateIdFromMetadata(notification.metadata);
  const templateDefinition =
    notification.presentation === "template"
      ? getTemplateDefinition(NOTIFICATION_TEMPLATE_DEFINITIONS, templateId)
      : null;
  const formattedDate = formatNotificationDate(notification.createdAt);

  function handleMarkReadOnly() {
    void onMarkRead(notification.id);
  }

  function handleAction() {
    if (!notification.action) {
      void onMarkRead(notification.id);
      return;
    }

    executeNotificationAction(notification.action, notification.metadata, {
      appBasePaths,
    });

    if (notification.action.type === "portal_route") {
      onNavigate?.();
      const portalRoute = resolvePortalRoute(notification.action.target, appBasePaths);
      const target = isEmbeddedDeepLinkNotification(
        notification.metadata,
        notification.action.type
      )
        ? buildPortalEmbeddedPath(portalRoute, String(notification.metadata?.deepPath ?? ""))
        : portalRoute;
      navigate(target);
    }

    void onMarkRead(notification.id);
  }

  const content = templateDefinition ? (
    <NotificationTemplateView
      definition={templateDefinition}
      vars={getTemplateVarsFromMetadata(notification.metadata)}
      compact={!isPage}
    />
  ) : notification.presentation === "html" && notification.htmlContent ? (
    <div
      className="notification-card__html"
      dangerouslySetInnerHTML={{ __html: notification.htmlContent }}
    />
  ) : (
    <p className="notification-card__message">{notification.message}</p>
  );

  if (isPage) {
    const isImportant = Boolean(notification.isImportant);

    return (
      <article
        className={[
          "notification-card",
          "notification-card--page",
          `notification-card--${notification.type}`,
          notification.read ? "notification-card--read" : "notification-card--unread",
          isImportant ? "notification-card--important" : "",
          selectionEnabled ? "notification-card--selectable" : "",
          selectionEnabled && selected ? "notification-card--selected" : "",
        ].join(" ")}
      >
        {selectionEnabled ? (
          <label className="notification-card__select">
            <input
              type="checkbox"
              className="notification-card__select-input"
              checked={selected}
              onChange={(event) => onSelectedChange?.(event.target.checked)}
              aria-label={`Selecionar notificação ${notification.title || notification.category}`}
            />
            <span className="notification-card__select-box" aria-hidden="true" />
          </label>
        ) : null}

        <div className="notification-card__icon" aria-hidden="true">
          <Icon size={20} />
        </div>

        <div className="notification-card__main">
          <header className="notification-card__header">
            <div className="notification-card__meta">
              {isImportant ? (
                <span className="notification-card__important-badge">
                  <Star size={12} aria-hidden="true" />
                  Importante
                </span>
              ) : null}
              <span className="notification-card__category">
                {CATEGORY_LABELS[notification.category]}
              </span>
              {formattedDate ? (
                <time className="notification-card__time" dateTime={notification.createdAt}>
                  {formattedDate}
                </time>
              ) : null}
              {!notification.read ? <span className="notification-card__dot" aria-hidden="true" /> : null}
            </div>

            <div className="notification-card__actions">
              {onToggleImportant ? (
                <button
                  type="button"
                  className={
                    isImportant
                      ? "notification-card__icon-btn notification-card__icon-btn--active"
                      : "notification-card__icon-btn"
                  }
                  onClick={() => onToggleImportant(notification.id, !isImportant)}
                  aria-label={isImportant ? "Remover dos importantes" : "Marcar como importante"}
                  title={isImportant ? "Remover dos importantes" : "Marcar como importante"}
                >
                  <Star size={16} aria-hidden="true" />
                </button>
              ) : null}

              {!notification.read ? (
                <button
                  type="button"
                  className="notification-card__icon-btn"
                  onClick={handleMarkReadOnly}
                  aria-label="Marcar como lida"
                  title="Marcar como lida"
                >
                  <Check size={16} aria-hidden="true" />
                </button>
              ) : (
                <span className="notification-card__read-badge">Lida</span>
              )}

              {onDelete ? (
                <button
                  type="button"
                  className="notification-card__icon-btn notification-card__icon-btn--danger"
                  onClick={() => onDelete(notification.id)}
                  aria-label="Excluir notificação"
                  title="Excluir"
                >
                  <Trash2 size={16} aria-hidden="true" />
                </button>
              ) : null}
            </div>
          </header>

          {!templateDefinition && notification.title ? (
            <h4 className="notification-card__title">{notification.title}</h4>
          ) : null}

          <div className="notification-card__content">{content}</div>

          {notification.action ? (
            <footer className="notification-card__footer">
              <button type="button" className="notification-card__cta" onClick={handleAction}>
                {notification.action.label}
              </button>
            </footer>
          ) : null}
        </div>
      </article>
    );
  }

  const isImportant = Boolean(notification.isImportant);
  const hasQuickActions = Boolean(onToggleImportant || onDelete);

  return (
    <article
      className={[
        "notification-card",
        "notification-card--compact",
        `notification-card--${notification.type}`,
        !notification.read ? "notification-card--unread" : "",
        isImportant ? "notification-card--important" : "",
      ].join(" ")}
    >
      <div className="notification-card__icon" aria-hidden="true">
        <Icon size={18} />
      </div>

      <div className="notification-card__body">
        <div className="notification-card__compact-head">
          <div className="notification-card__meta">
            {isImportant ? (
              <span
                className="notification-card__important-badge notification-card__important-badge--compact"
                title="Importante"
              >
                <Star size={10} aria-hidden="true" />
              </span>
            ) : null}
            <span className="notification-card__category">
              {CATEGORY_LABELS[notification.category]}
            </span>
            {!notification.read ? <span className="notification-card__dot" aria-hidden="true" /> : null}
          </div>

          {hasQuickActions ? (
            <div className="notification-card__actions notification-card__actions--compact">
              {onToggleImportant ? (
                <button
                  type="button"
                  className={
                    isImportant
                      ? "notification-card__icon-btn notification-card__icon-btn--compact notification-card__icon-btn--active"
                      : "notification-card__icon-btn notification-card__icon-btn--compact"
                  }
                  onClick={() => onToggleImportant(notification.id, !isImportant)}
                  aria-label={isImportant ? "Remover dos importantes" : "Marcar como importante"}
                  title={isImportant ? "Remover dos importantes" : "Marcar como importante"}
                >
                  <Star size={14} aria-hidden="true" />
                </button>
              ) : null}

              {!notification.read ? (
                <button
                  type="button"
                  className="notification-card__icon-btn notification-card__icon-btn--compact"
                  onClick={handleMarkReadOnly}
                  aria-label="Marcar como lida"
                  title="Marcar como lida"
                >
                  <Check size={14} aria-hidden="true" />
                </button>
              ) : null}

              {onDelete ? (
                <button
                  type="button"
                  className="notification-card__icon-btn notification-card__icon-btn--compact notification-card__icon-btn--danger"
                  onClick={() => onDelete(notification.id)}
                  aria-label="Excluir notificação"
                  title="Excluir"
                >
                  <Trash2 size={14} aria-hidden="true" />
                </button>
              ) : null}
            </div>
          ) : null}
        </div>

        {!templateDefinition && notification.title ? (
          <h4 className="notification-card__title">{notification.title}</h4>
        ) : null}

        {content}

        {notification.action ? (
          <button type="button" className="notification-card__cta" onClick={handleAction}>
            {notification.action.label}
          </button>
        ) : !hasQuickActions ? (
          <button
            type="button"
            className="notification-card__cta notification-card__cta--ghost"
            onClick={handleMarkReadOnly}
          >
            Marcar como lida
          </button>
        ) : null}
      </div>
    </article>
  );
}

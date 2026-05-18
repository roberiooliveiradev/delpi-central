// src/components/notifications/NotificationTemplateView.tsx

import type { NotificationTemplateDefinition } from "./notificationTemplates";
import { buildTemplatePreview } from "./notificationTemplates";

import "./NotificationTemplateView.css";

type NotificationTemplateViewProps = {
  definition: NotificationTemplateDefinition;
  vars: Record<string, string>;
  compact?: boolean;
};

export function NotificationTemplateView({
  definition,
  vars,
  compact = false,
}: NotificationTemplateViewProps) {
  const preview = buildTemplatePreview(definition, vars);

  return (
    <div className={`notification-template-view ${compact ? "notification-template-view--compact" : ""}`}>
      <p className="notification-template-view__title">{preview.title}</p>
      <p className="notification-template-view__message">{preview.message}</p>

      {definition.id === "company_event_v1" ? (
        <ul className="notification-template-view__details">
          {vars.eventDate ? <li>{vars.eventDate}</li> : null}
          {vars.location ? <li>{vars.location}</li> : null}
        </ul>
      ) : null}

      {definition.id === "welcome_v1" ? (
        <p className="notification-template-view__hint">
          Explore os aplicativos no menu lateral e personalize seus favoritos.
        </p>
      ) : null}

      {definition.id === "birthday_v1" ? (
        <p className="notification-template-view__hint">🎂 Um ótimo ano novo de conquistas!</p>
      ) : null}
    </div>
  );
}

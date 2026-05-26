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

      {definition.id === "app_access_granted_v1" && vars.appNames ? (
        <ul className="notification-template-view__details">
          {vars.appNames.split(",").map((app) => (
            <li key={app.trim()}>{app.trim()}</li>
          ))}
        </ul>
      ) : null}

      {definition.hint ? (
        <p className="notification-template-view__hint">{definition.hint}</p>
      ) : null}
    </div>
  );
}

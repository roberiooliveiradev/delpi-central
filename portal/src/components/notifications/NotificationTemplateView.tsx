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

      {definition.id === "app_access_granted_v1"
        ? (() => {
            const apps = [
              ...new Set(
                (vars.appNames ?? "")
                  .split(",")
                  .map((item) => item.trim())
                  .filter(Boolean),
              ),
            ];
            const appKeys = new Set(apps.map((name) => name.toLowerCase()));
            const features = [
              ...new Set(
                (vars.featureNames ?? "")
                  .split(",")
                  .map((item) => item.trim())
                  .filter(Boolean),
              ),
            ].filter((feature) => {
              const base = feature.includes(":")
                ? feature.split(":")[0].trim().toLowerCase()
                : feature.toLowerCase();
              return !appKeys.has(base) && !appKeys.has(feature.toLowerCase());
            });

            const systemPermissions = [
              ...new Set(
                (vars.systemPermissionNames ?? "")
                  .split(",")
                  .map((item) => item.trim())
                  .filter(Boolean),
              ),
            ];

            return (
              <>
                {apps.length > 1 ? (
                  <ul className="notification-template-view__details">
                    {apps.map((app) => (
                      <li key={app}>{app}</li>
                    ))}
                  </ul>
                ) : null}

                {systemPermissions.length > 0 ? (
                  <ul className="notification-template-view__details notification-template-view__details--system">
                    {systemPermissions.map((perm) => (
                      <li key={perm}>{perm}</li>
                    ))}
                  </ul>
                ) : null}

                {features.length > 0 ? (
                  <ul className="notification-template-view__details notification-template-view__details--features">
                    {features.map((feature) => (
                      <li key={feature}>{feature}</li>
                    ))}
                  </ul>
                ) : null}
              </>
            );
          })()
        : null}

      {definition.hint ? (
        <p className="notification-template-view__hint">{definition.hint}</p>
      ) : null}
    </div>
  );
}

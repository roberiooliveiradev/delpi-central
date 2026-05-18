// src/utils/notificationNavigation.ts

import type { NotificationAction } from "../data/coreApi";

export function executeNotificationAction(action: NotificationAction | null | undefined) {
  if (!action?.target) {
    return;
  }

  if (action.type === "external_url") {
    window.open(action.target, "_blank", "noopener,noreferrer");
    return;
  }

  if (action.type === "portal_route") {
    window.location.assign(action.target);
  }
}

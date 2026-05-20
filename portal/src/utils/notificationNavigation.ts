// src/utils/notificationNavigation.ts

import type { NotificationAction } from "../data/coreApi";
import {
  dispatchControleMpNotificationNavigate,
  isControleMpNotification,
  stashControleMpDeepPath,
} from "./controleMpNotification";

export function executeNotificationAction(
  action: NotificationAction | null | undefined,
  metadata?: Record<string, unknown> | null
) {
  if (!action?.target) {
    return;
  }

  if (isControleMpNotification(metadata)) {
    stashControleMpDeepPath(metadata.deepPath!);
    dispatchControleMpNotificationNavigate({
      portalRoute: action.target,
      deepPath: metadata.deepPath!,
    });
  }

  if (action.type === "external_url") {
    window.open(action.target, "_blank", "noopener,noreferrer");
    return;
  }

  if (action.type === "portal_route") {
    window.location.assign(action.target);
  }
}

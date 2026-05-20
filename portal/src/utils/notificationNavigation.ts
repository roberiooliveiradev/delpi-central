// src/utils/notificationNavigation.ts

import type { NotificationAction } from "../data/coreApi";
import {
  dispatchEmbeddedNotificationNavigate,
  isEmbeddedDeepLinkNotification,
  resolvePortalRoute,
  stashEmbeddedDeepLink,
} from "./embeddedAppNotification";

export type ExecuteNotificationActionOptions = {
  /** basePath de cada app (AuthContext.apps) para alinhar action.target */
  appBasePaths?: string[];
};

export function executeNotificationAction(
  action: NotificationAction | null | undefined,
  metadata?: Record<string, unknown> | null,
  options?: ExecuteNotificationActionOptions
) {
  if (!action?.target) {
    return;
  }

  const appBasePaths = options?.appBasePaths ?? [];

  if (isEmbeddedDeepLinkNotification(metadata, action.type)) {
    const portalRoute = resolvePortalRoute(action.target, appBasePaths);
    const source =
      typeof metadata?.source === "string" ? metadata.source : undefined;

    stashEmbeddedDeepLink({
      portalRoute,
      deepPath: metadata.deepPath,
      source,
    });

    dispatchEmbeddedNotificationNavigate({
      portalRoute,
      deepPath: metadata.deepPath,
      source,
    });

    // SPA: react-router (onNavigate no NotificationCard). Sem reload completo.
    if (action.type === "portal_route") {
      return;
    }
  }

  if (action.type === "external_url") {
    window.open(action.target, "_blank", "noopener,noreferrer");
    return;
  }

  if (action.type === "portal_route") {
    window.location.assign(resolvePortalRoute(action.target, appBasePaths));
  }
}

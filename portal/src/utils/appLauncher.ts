// src/utils/appLauncher.ts

import type { NotificationAction } from "../data/coreApi";
import { getTemplateIdFromMetadata, getTemplateVarsFromMetadata } from "../components/notifications/notificationTemplates";
import { normalizeAppPath } from "./embeddedAppNotification";

/** Rota virtual: abre o catálogo de apps (modal AppLauncher), não uma página. */
export const PORTAL_APP_LAUNCHER_ROUTE = "/__apps";

export const DELPI_OPEN_APP_LAUNCHER_EVENT = "DELPI_OPEN_APP_LAUNCHER";
export const DELPI_CLOSE_APP_LAUNCHER_EVENT = "DELPI_CLOSE_APP_LAUNCHER";

export function isAppLauncherRoute(target: string | null | undefined): boolean {
  return normalizeAppPath(target ?? "") === PORTAL_APP_LAUNCHER_ROUTE;
}

function countAppsInAccessVars(metadata: Record<string, unknown> | null | undefined): number {
  const vars = getTemplateVarsFromMetadata(metadata);
  const names = (vars.appNames ?? "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  return new Set(names).size;
}

/** CTA “Ver aplicativos” com mais de um app → catálogo, não home nem app único. */
export function shouldOpenAppLauncher(
  action: NotificationAction | null | undefined,
  metadata?: Record<string, unknown> | null,
): boolean {
  if (!action?.target) {
    return false;
  }

  if (isAppLauncherRoute(action.target)) {
    return true;
  }

  const label = (action.label ?? "").trim().toLowerCase();
  if (label !== "ver aplicativos") {
    return false;
  }

  if (getTemplateIdFromMetadata(metadata) !== "app_access_granted_v1") {
    return false;
  }

  return countAppsInAccessVars(metadata) > 1;
}

export function openAppLauncher() {
  window.dispatchEvent(new CustomEvent(DELPI_OPEN_APP_LAUNCHER_EVENT));
}

export function closeAppLauncher() {
  window.dispatchEvent(new CustomEvent(DELPI_CLOSE_APP_LAUNCHER_EVENT));
}

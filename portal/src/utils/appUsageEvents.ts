// portal/src/utils/appUsageEvents.ts

export const APP_USAGE_OPEN_EVENT = "delpi:app-usage-open";
export const APP_USAGE_CLOSE_EVENT = "delpi:app-usage-close";

export type AppUsageOpenDetail = {
  appId: string;
  routePath: string;
  /**
   * Apps external (nova aba): não dá para inspecionar a aba externa.
   * O portal combina janela de graça + Page Visibility para estimar uso ao vivo.
   */
  external?: boolean;
};

export type AppUsageCloseDetail = {
  appId?: string;
};

export function notifyAppOpened(
  appId: string,
  routePath: string,
  options?: { external?: boolean },
) {
  if (!appId?.trim()) return;

  window.dispatchEvent(
    new CustomEvent<AppUsageOpenDetail>(APP_USAGE_OPEN_EVENT, {
      detail: {
        appId: appId.trim(),
        routePath: routePath || "/",
        external: options?.external,
      },
    }),
  );
}

export function notifyAppClosed(appId?: string) {
  window.dispatchEvent(
    new CustomEvent<AppUsageCloseDetail>(APP_USAGE_CLOSE_EVENT, {
      detail: appId?.trim() ? { appId: appId.trim() } : {},
    }),
  );
}

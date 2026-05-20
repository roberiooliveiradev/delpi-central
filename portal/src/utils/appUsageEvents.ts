// portal/src/utils/appUsageEvents.ts

export const APP_USAGE_OPEN_EVENT = "delpi:app-usage-open";

export type AppUsageOpenDetail = {
  appId: string;
  routePath: string;
};

export function notifyAppOpened(appId: string, routePath: string) {
  if (!appId?.trim()) return;

  window.dispatchEvent(
    new CustomEvent<AppUsageOpenDetail>(APP_USAGE_OPEN_EVENT, {
      detail: {
        appId: appId.trim(),
        routePath: routePath || "/",
      },
    }),
  );
}

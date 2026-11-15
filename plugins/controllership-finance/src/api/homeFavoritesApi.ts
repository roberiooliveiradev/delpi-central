import type { PluginNavigationTarget } from "../app/pluginRoutes";
import { cfApiUrl, httpGet, httpPut } from "./httpClient";

type CfEnvelope<T> = {
  success: boolean;
  message?: string;
  data?: T | null;
};

export type HomeFavoriteItem = {
  viewId: PluginNavigationTarget;
  search?: string;
};

export function homeFavoriteKey(item: { viewId: string; search?: string }): string {
  return `${item.viewId}::${item.search ?? ""}`;
}

export async function getHomeFavorites(signal?: AbortSignal): Promise<HomeFavoriteItem[]> {
  const response = await httpGet<CfEnvelope<{ items: HomeFavoriteItem[] }>>(
    cfApiUrl("/me/home-favorites"),
    { signal },
  );
  const items = response?.data?.items;
  return Array.isArray(items) ? items : [];
}

export async function putHomeFavorites(
  items: HomeFavoriteItem[],
  signal?: AbortSignal,
): Promise<HomeFavoriteItem[]> {
  const response = await httpPut<CfEnvelope<{ items: HomeFavoriteItem[] }>>(
    cfApiUrl("/me/home-favorites"),
    { items },
    { signal },
  );
  const saved = response?.data?.items;
  return Array.isArray(saved) ? saved : [];
}

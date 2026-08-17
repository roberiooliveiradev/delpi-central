import type { PluginNavigationTarget } from "../app/pluginRoutes";
import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import { commercialApiUrl, httpGet, httpPut } from "./httpClient";

export type HomeFavoriteItem = {
  viewId: PluginNavigationTarget;
  search?: string;
};

export function homeFavoriteKey(item: { viewId: string; search?: string }): string {
  return `${item.viewId}::${item.search ?? ""}`;
}

export async function getHomeFavorites(signal?: AbortSignal): Promise<HomeFavoriteItem[]> {
  const response = await httpGet<ApiSuccessResponse<{ items: HomeFavoriteItem[] }>>(
    commercialApiUrl("/me/home-favorites"),
    { signal },
  );
  const data = unwrapEnvelope(response, "Erro ao carregar favoritos.");
  return Array.isArray(data.items) ? data.items : [];
}

export async function putHomeFavorites(
  items: HomeFavoriteItem[],
  signal?: AbortSignal,
): Promise<HomeFavoriteItem[]> {
  const response = await httpPut<ApiSuccessResponse<{ items: HomeFavoriteItem[] }>>(
    commercialApiUrl("/me/home-favorites"),
    { items },
    { signal },
  );
  const data = unwrapEnvelope(response, "Erro ao salvar favoritos.");
  return Array.isArray(data.items) ? data.items : [];
}

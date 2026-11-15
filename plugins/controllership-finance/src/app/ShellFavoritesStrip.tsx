import { useCallback, useEffect, useMemo, useState } from "react";

import {
  homeFavoriteKey,
  type HomeFavoriteItem,
} from "../api/homeFavoritesApi";
import {
  refreshHomeFavorites,
  replaceHomeFavorites,
  setHomeFavoritesLocal,
  subscribeHomeFavorites,
} from "./homeFavoritesStore";
import { navigatePluginView } from "./pluginNavigation";
import { useViewerContext } from "./ViewerContext";
import { CfTopBarFavoritesStrip } from "./controllershipFinanceUi";
import {
  HUB_CONTENT,
  hubRouteLabelByView,
  resolveHubSections,
} from "../content/pluginRouteCatalog";

type ShellFavoritesStripProps = {
  basePath: string;
};

function favoriteStillAllowed(
  item: HomeFavoriteItem,
  capabilities: {
    access: boolean;
    manage: boolean;
    accessDre: boolean;
    lnfAccess: boolean;
  },
): boolean {
  const sections = resolveHubSections(capabilities);
  for (const section of sections) {
    for (const route of section.routes) {
      if (route.kind === "external" || !route.viewId) continue;
      if (route.viewId !== item.viewId) continue;
      if ((route.search ?? undefined) === (item.search ?? undefined)) {
        return true;
      }
    }
  }
  for (const section of sections) {
    for (const route of section.routes) {
      if (route.kind === "external" || !route.viewId) continue;
      if (route.viewId === item.viewId && !route.search) return true;
    }
  }
  return false;
}

/**
 * Favoritos do shell — chrome do kit; persistência via homeFavoritesStore / BFF.
 */
export function ShellFavoritesStrip({ basePath }: ShellFavoritesStripProps) {
  const { viewer } = useViewerContext();
  const [favorites, setFavorites] = useState<HomeFavoriteItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const copy = HUB_CONTENT.features;

  const capabilities = useMemo(
    () => ({
      access: viewer === null || viewer.capabilities.access === true,
      manage: viewer?.capabilities.manage === true,
      accessDre:
        viewer?.capabilities.accessDre === true &&
        viewer?.capabilities.access !== true,
      lnfAccess: viewer?.capabilities.lnfAccess === true,
    }),
    [viewer],
  );

  const visibleFavorites = useMemo(
    () => favorites.filter((item) => favoriteStillAllowed(item, capabilities)),
    [capabilities, favorites],
  );

  useEffect(() => subscribeHomeFavorites(setFavorites), []);

  useEffect(() => {
    const controller = new AbortController();
    void refreshHomeFavorites(controller.signal)
      .then(() => {
        if (!controller.signal.aborted) setError(null);
      })
      .catch(() => {
        if (!controller.signal.aborted) setError(copy.favoritesLoadError);
      });
    return () => controller.abort();
  }, [copy.favoritesLoadError]);

  const removeFavorite = useCallback(
    async (item: HomeFavoriteItem) => {
      const previous = favorites;
      const key = homeFavoriteKey(item);
      const next = favorites.filter((entry) => homeFavoriteKey(entry) !== key);
      setHomeFavoritesLocal(next);
      try {
        await replaceHomeFavorites(next);
        setError(null);
      } catch {
        setHomeFavoritesLocal(previous);
        setError(copy.favoritesSaveError);
      }
    },
    [copy.favoritesSaveError, favorites],
  );

  return (
    <CfTopBarFavoritesStrip
      items={visibleFavorites.map((item) => ({
        id: homeFavoriteKey(item),
        label: hubRouteLabelByView(item.viewId, item.search) ?? item.viewId,
      }))}
      onSelect={(id) => {
        const item = visibleFavorites.find((entry) => homeFavoriteKey(entry) === id);
        if (!item) return;
        navigatePluginView(item.viewId, {
          basePath,
          search: item.search,
        });
      }}
      onRemove={(id) => {
        const item = visibleFavorites.find((entry) => homeFavoriteKey(entry) === id);
        if (item) void removeFavorite(item);
      }}
      title={copy.favoritesTitle}
      emptyLabel={copy.favoritesEmpty}
      errorLabel={error}
      openAriaLabel={copy.favoritesMenuOpenAriaLabel}
      closeAriaLabel={copy.favoritesMenuCloseAriaLabel}
      removeLabel={(label) => `${copy.unpinLabel}: ${label}`}
    />
  );
}

import { useCallback, useEffect, useState } from "react";

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
import { HUB_CONTENT, hubRouteLabelByView } from "../content/pluginRouteCatalog";
import { CommercialTopBarFavoritesStrip } from "./commercialUi";

type ShellFavoritesStripProps = {
  basePath: string;
};

/**
 * Favoritos do shell — chrome do kit; persistência via homeFavoritesStore / commercial-api.
 */
export function ShellFavoritesStrip({ basePath }: ShellFavoritesStripProps) {
  const [favorites, setFavorites] = useState<HomeFavoriteItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const copy = HUB_CONTENT.features;

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
    <CommercialTopBarFavoritesStrip
      items={favorites.map((item) => ({
        id: homeFavoriteKey(item),
        label: hubRouteLabelByView(item.viewId, item.search) ?? item.viewId,
      }))}
      onSelect={(id) => {
        const item = favorites.find((entry) => homeFavoriteKey(entry) === id);
        if (!item) return;
        navigatePluginView(item.viewId, {
          basePath,
          search: item.search,
        });
      }}
      onRemove={(id) => {
        const item = favorites.find((entry) => homeFavoriteKey(entry) === id);
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

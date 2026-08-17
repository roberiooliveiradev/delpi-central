import { useCallback, useEffect, useState } from "react";

import {
  getHomeFavorites,
  homeFavoriteKey,
  putHomeFavorites,
  type HomeFavoriteItem,
} from "../api/homeFavoritesApi";
import {
  CommercialHubChipRow,
  CommercialRouteChip,
} from "./commercialUi";
import { navigatePluginView } from "./pluginNavigation";
import { HUB_CONTENT, hubRouteLabelByView } from "../content/pluginRouteCatalog";

type ShellFavoritesStripProps = {
  basePath: string;
};

/**
 * Favoritos do shell — renderizados no slot `secondary` da TopBar.
 */
export function ShellFavoritesStrip({ basePath }: ShellFavoritesStripProps) {
  const [favorites, setFavorites] = useState<HomeFavoriteItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const copy = HUB_CONTENT.features;

  useEffect(() => {
    const controller = new AbortController();
    void getHomeFavorites(controller.signal)
      .then((items) => {
        if (!controller.signal.aborted) {
          setFavorites(items);
          setError(null);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setFavorites([]);
          setError(copy.favoritesLoadError);
        }
      });
    return () => controller.abort();
  }, [copy.favoritesLoadError]);

  const removeFavorite = useCallback(
    async (item: HomeFavoriteItem) => {
      const key = homeFavoriteKey(item);
      const previous = favorites;
      const next = favorites.filter((entry) => homeFavoriteKey(entry) !== key);
      setFavorites(next);
      try {
        const saved = await putHomeFavorites(next);
        setFavorites(saved);
        setError(null);
      } catch {
        setFavorites(previous);
        setError(copy.favoritesSaveError);
      }
    },
    [copy.favoritesSaveError, favorites],
  );

  if (error && favorites.length === 0) {
    return (
      <p className="cm-home-inline-error" role="status">
        {error}
      </p>
    );
  }

  if (favorites.length === 0) {
    return null;
  }

  return (
    <>
      {error ? (
        <p className="cm-home-inline-error" role="status">
          {error}
        </p>
      ) : null}
      <CommercialHubChipRow label={copy.favoritesTitle} aria-label={copy.favoritesTitle}>
        {favorites.map((item) => {
          const label = hubRouteLabelByView(item.viewId, item.search) ?? item.viewId;
          return (
            <CommercialRouteChip
              key={homeFavoriteKey(item)}
              tone="pinned"
              label={label}
              onNavigate={() =>
                navigatePluginView(item.viewId, {
                  basePath,
                  search: item.search,
                })
              }
              onRemove={() => {
                void removeFavorite(item);
              }}
              removeLabel={copy.unpinLabel}
            />
          );
        })}
      </CommercialHubChipRow>
    </>
  );
}

import { useEffect, useState } from "react";

import { navigatePluginView } from "./pluginNavigation";
import {
  loadHomeFavoritesFromStorage,
  removeHomeFavorite,
  subscribeHomeFavorites,
} from "./homeFavoritesStore";
import type { HomeFavoriteItem } from "../features/home/homeFavorites";
import { HUB_CONTENT, hubRouteLabelByView } from "../content/pluginRouteCatalog";
import { SuppliesTopBarFavoritesStrip } from "./suppliesUi";

type ShellFavoritesStripProps = {
  basePath: string;
};

/**
 * Favoritos do shell — chrome do kit; persistência localStorage do portal.
 */
export function ShellFavoritesStrip({ basePath }: ShellFavoritesStripProps) {
  const [favorites, setFavorites] = useState<HomeFavoriteItem[]>([]);
  const copy = HUB_CONTENT.home;

  useEffect(() => subscribeHomeFavorites(setFavorites), []);

  useEffect(() => {
    loadHomeFavoritesFromStorage();
  }, []);

  return (
    <SuppliesTopBarFavoritesStrip
      items={favorites.map((item) => ({
        id: item.viewId,
        label: hubRouteLabelByView(item.viewId) ?? item.label,
      }))}
      onSelect={(id: string) => {
        navigatePluginView(id, { basePath });
      }}
      onRemove={(id: string) => {
        removeHomeFavorite(id);
      }}
      title={copy.favoritesTitle}
      emptyLabel={copy.favoritesEmpty}
      openAriaLabel={copy.favoritesMenuOpenAriaLabel}
      closeAriaLabel={copy.favoritesMenuCloseAriaLabel}
      removeLabel={(label: string) => `${copy.unpinLabel}: ${label}`}
    />
  );
}

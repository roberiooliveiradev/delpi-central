import { useCallback, useEffect, useRef, useState } from "react";
import {
  AnchoredPanelPortal,
  ContextMenuItem,
} from "@delpi/plugin-ui/index";
import { Star, X } from "lucide-react";

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

type ShellFavoritesStripProps = {
  basePath: string;
};

/**
 * Favoritos do shell — gatilho na TopBar + popover (sync via homeFavoritesStore).
 */
export function ShellFavoritesStrip({ basePath }: ShellFavoritesStripProps) {
  const [favorites, setFavorites] = useState<HomeFavoriteItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
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

  const count = favorites.length;
  const triggerLabel =
    count > 0
      ? `${copy.favoritesTitle} (${count.toLocaleString("pt-BR")})`
      : copy.favoritesTitle;

  return (
    <div
      ref={rootRef}
      className={["cm-shell-favorites", open ? "cm-shell-favorites--open" : null]
        .filter(Boolean)
        .join(" ")}
    >
      <button
        type="button"
        className="cm-shell-favorites__trigger"
        aria-label={open ? copy.favoritesMenuCloseAriaLabel : copy.favoritesMenuOpenAriaLabel}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <Star
          className="cm-shell-favorites__trigger-icon"
          size={16}
          strokeWidth={1.75}
          aria-hidden="true"
        />
        <span className="cm-shell-favorites__trigger-label">{triggerLabel}</span>
      </button>

      <AnchoredPanelPortal
        open={open}
        anchorRef={rootRef}
        panelRef={panelRef}
        className="delpi-ui-context-menu cm-shell-favorites__panel"
        variant="bare"
        role="menu"
        aria-label={copy.favoritesTitle}
        preferredPlacement="bottom"
        gap={6}
        portalScopeClassName="dashboard-commercial"
        onDismiss={() => setOpen(false)}
      >
        {error ? (
          <p className="cm-shell-favorites__status" role="status">
            {error}
          </p>
        ) : null}
        {count === 0 && !error ? (
          <p className="cm-shell-favorites__status" role="status">
            {copy.favoritesEmpty}
          </p>
        ) : null}
        {favorites.map((item) => {
          const label = hubRouteLabelByView(item.viewId, item.search) ?? item.viewId;
          return (
            <div key={homeFavoriteKey(item)} className="cm-shell-favorites__row" role="none">
              <ContextMenuItem
                label={label}
                icon={Star}
                onSelect={() => {
                  setOpen(false);
                  navigatePluginView(item.viewId, {
                    basePath,
                    search: item.search,
                  });
                }}
              />
              <button
                type="button"
                className="cm-shell-favorites__remove"
                aria-label={`${copy.unpinLabel}: ${label}`}
                onClick={(event) => {
                  event.preventDefault();
                  event.stopPropagation();
                  void removeFavorite(item);
                }}
              >
                <X size={14} strokeWidth={2} aria-hidden="true" />
              </button>
            </div>
          );
        })}
      </AnchoredPanelPortal>
    </div>
  );
}

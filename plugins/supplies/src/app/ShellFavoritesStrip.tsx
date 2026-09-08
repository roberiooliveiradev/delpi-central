import { useCallback, useEffect, useRef, useState } from "react";
import {
  AnchoredPanelPortal,
  ContextMenuItem,
} from "@delpi/plugin-ui/index";
import { Star, X } from "lucide-react";

import { navigatePluginView } from "./pluginNavigation";
import {
  loadHomeFavoritesFromStorage,
  removeHomeFavorite,
  subscribeHomeFavorites,
} from "./homeFavoritesStore";
import type { HomeFavoriteItem } from "../features/home/homeFavorites";
import { HUB_CONTENT, hubRouteLabelByView } from "../content/pluginRouteCatalog";
import { SP_PORTAL_SCOPE } from "./suppliesUi";

type ShellFavoritesStripProps = {
  basePath: string;
};

/**
 * Favoritos do shell — gatilho na TopBar + popover (padrão Comercial; localStorage).
 */
export function ShellFavoritesStrip({ basePath }: ShellFavoritesStripProps) {
  const [favorites, setFavorites] = useState<HomeFavoriteItem[]>([]);
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const copy = HUB_CONTENT.home;

  useEffect(() => subscribeHomeFavorites(setFavorites), []);

  useEffect(() => {
    loadHomeFavoritesFromStorage();
  }, []);

  const removeFavorite = useCallback((item: HomeFavoriteItem) => {
    removeHomeFavorite(item.viewId);
  }, []);

  const count = favorites.length;
  const triggerLabel =
    count > 0
      ? `${copy.favoritesTitle} (${count.toLocaleString("pt-BR")})`
      : copy.favoritesTitle;

  return (
    <div
      ref={rootRef}
      className={["sp-shell-favorites", open ? "sp-shell-favorites--open" : null]
        .filter(Boolean)
        .join(" ")}
    >
      <button
        type="button"
        className="sp-shell-favorites__trigger"
        aria-label={open ? copy.favoritesMenuCloseAriaLabel : copy.favoritesMenuOpenAriaLabel}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <Star
          className="sp-shell-favorites__trigger-icon"
          size={16}
          strokeWidth={1.75}
          aria-hidden="true"
        />
        <span className="sp-shell-favorites__trigger-label delpi-ui-topbar-collapse-label">
          {triggerLabel}
        </span>
      </button>

      <AnchoredPanelPortal
        open={open}
        anchorRef={rootRef}
        panelRef={panelRef}
        className="delpi-ui-context-menu sp-shell-favorites__panel"
        variant="bare"
        role="menu"
        aria-label={copy.favoritesTitle}
        preferredPlacement="bottom"
        gap={6}
        portalScopeClassName={SP_PORTAL_SCOPE}
        onDismiss={() => setOpen(false)}
      >
        {count === 0 ? (
          <p className="sp-shell-favorites__status" role="status">
            {copy.favoritesEmpty}
          </p>
        ) : null}
        {favorites.map((item) => {
          const label = hubRouteLabelByView(item.viewId) ?? item.label;
          return (
            <div key={item.viewId} className="sp-shell-favorites__row" role="none">
              <ContextMenuItem
                label={label}
                icon={Star}
                onSelect={() => {
                  setOpen(false);
                  navigatePluginView(item.viewId, { basePath });
                }}
              />
              <button
                type="button"
                className="sp-shell-favorites__remove"
                aria-label={`${copy.unpinLabel}: ${label}`}
                onClick={(event) => {
                  event.preventDefault();
                  event.stopPropagation();
                  removeFavorite(item);
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

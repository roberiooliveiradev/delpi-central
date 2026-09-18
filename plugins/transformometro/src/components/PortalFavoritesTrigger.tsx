import { useEffect, useRef, useState } from "react";
import {
  AnchoredPanelPortal,
  ContextMenuItem,
  topBarSearchTriggerBemClasses,
} from "@delpi/plugin-ui/index";
import { Star, X } from "lucide-react";

import { useCanManagePortal } from "../state/portalChrome";
import {
  subscribePortalFavorites,
  togglePortalFavorite,
  visiblePortalFavorites,
  type PortalFavoriteItem,
} from "../state/portalFavorites";

const SEARCH = topBarSearchTriggerBemClasses("ds");

type PortalFavoritesTriggerProps = {
  onNavigate: (path: string) => void;
};

export function PortalFavoritesTrigger({ onNavigate }: PortalFavoritesTriggerProps) {
  const canManage = useCanManagePortal();
  const [favorites, setFavorites] = useState<PortalFavoriteItem[]>([]);
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const visible = visiblePortalFavorites(favorites, canManage);
  const count = visible.length;
  const label = count > 0 ? `Favoritos (${count.toLocaleString("pt-BR")})` : "Favoritos";

  useEffect(() => subscribePortalFavorites(setFavorites), []);

  return (
    <div ref={rootRef} className="tm-topbar-favorites">
      <button
        type="button"
        className={SEARCH.root}
        aria-label={open ? "Fechar favoritos" : "Abrir favoritos"}
        aria-haspopup="menu"
        aria-expanded={open}
        title="Favoritos"
        onClick={() => setOpen((current) => !current)}
      >
        <Star size={16} strokeWidth={1.75} aria-hidden="true" />
        <span className={`${SEARCH.label} delpi-ui-topbar-collapse-label`}>{label}</span>
      </button>
      <AnchoredPanelPortal
        open={open}
        anchorRef={rootRef}
        panelRef={panelRef}
        className="delpi-ui-context-menu"
        variant="bare"
        role="menu"
        aria-label="Favoritos"
        preferredPlacement="bottom"
        gap={6}
        portalScopeClassName="dashboard-transformometro"
        onDismiss={() => setOpen(false)}
      >
        {count === 0 ? (
          <p className="tm-favorites-status" role="status">
            Clique na estrela de um caminho para fixá-lo aqui.
          </p>
        ) : (
          visible.map((item) => (
            <div key={item.path} className="tm-favorites-row" role="none">
              <ContextMenuItem
                label={item.label}
                icon={Star}
                onSelect={() => {
                  setOpen(false);
                  onNavigate(item.path);
                }}
              />
              <button
                type="button"
                className="tm-favorites-remove"
                aria-label={`Remover dos favoritos: ${item.label}`}
                onClick={(event) => {
                  event.preventDefault();
                  event.stopPropagation();
                  togglePortalFavorite(item);
                }}
              >
                <X size={14} strokeWidth={2} aria-hidden="true" />
              </button>
            </div>
          ))
        )}
      </AnchoredPanelPortal>
    </div>
  );
}

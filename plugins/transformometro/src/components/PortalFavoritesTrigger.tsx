import { useEffect, useState } from "react";
import {
  TopBarFavoritesStrip,
  topBarFavoritesStripBemClasses,
} from "@delpi/plugin-ui/index";

import { useCanManagePortal } from "../state/portalChrome";
import {
  subscribePortalFavorites,
  togglePortalFavorite,
  visiblePortalFavorites,
  type PortalFavoriteItem,
} from "../state/portalFavorites";

const FAVORITES = topBarFavoritesStripBemClasses("ds");

type PortalFavoritesTriggerProps = {
  onNavigate: (path: string) => void;
};

export function PortalFavoritesTrigger({ onNavigate }: PortalFavoritesTriggerProps) {
  const canManage = useCanManagePortal();
  const [favorites, setFavorites] = useState<PortalFavoriteItem[]>([]);
  const visible = visiblePortalFavorites(favorites, canManage);

  useEffect(() => subscribePortalFavorites(setFavorites), []);

  return (
    <TopBarFavoritesStrip
      classNames={FAVORITES}
      portalScopeClassName="dashboard-transformometro"
      items={visible.map((item) => ({ id: item.path, label: item.label }))}
      onSelect={onNavigate}
      onRemove={(path) => {
        const item = visible.find((entry) => entry.path === path);
        if (item) togglePortalFavorite(item);
      }}
      title="Favoritos"
      emptyLabel="Clique na estrela de um caminho para fixá-lo aqui."
      openAriaLabel="Abrir favoritos"
      closeAriaLabel="Fechar favoritos"
      removeLabel={(label) => `Remover dos favoritos: ${label}`}
    />
  );
}

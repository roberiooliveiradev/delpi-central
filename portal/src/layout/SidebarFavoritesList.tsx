import { AppLauncherCard } from "../components/AppLauncherCard";
import { AppLauncherReorderList } from "../components/AppLauncherReorderList";
import type { FavoriteAppItem } from "../data/coreApi";

type GroupedRoutes = Record<
  string,
  {
    appName: string;
    appIcon?: string | null;
    routes: any[];
  }
>;

type CatalogApp = {
  id: string;
  name: string;
  icon?: string | null;
  basePath?: string | null;
};

type PinnedEntry = readonly [string, GroupedRoutes[string]];

type Props = {
  entries: PinnedEntry[];
  favorites: FavoriteAppItem[];
  apps: CatalogApp[];
  openApps: Record<string, boolean>;
  onToggleOpen: (appId: string) => void;
  onNavigate: (path: string) => void;
  onReorder: (appIds: string[]) => Promise<void>;
};

export const SidebarFavoritesList = ({
  entries,
  favorites,
  apps,
  openApps,
  onToggleOpen,
  onNavigate,
  onReorder,
}: Props) => {
  const appIds = entries.map(([appId]) => appId);

  return (
    <AppLauncherReorderList
      appIds={appIds}
      favorites={favorites}
      onReorder={onReorder}
    >
      {entries.map(([appId, group]) => {
        const isOpen = openApps[appId] ?? false;
        const catalogApp = apps.find((app) => app.id === appId);

        return (
          <AppLauncherCard
            key={appId}
            variant="sidebar"
            reorderable
            app={
              catalogApp ?? {
                id: appId,
                name: group.appName,
                icon: group.appIcon,
              }
            }
            routes={group.routes}
            isOpen={isOpen}
            onToggleOpen={onToggleOpen}
            onOpenSingle={() => {
              const route = group.routes[0];
              if (route) {
                onNavigate(route.path);
                return;
              }
              if (catalogApp?.basePath) onNavigate(catalogApp.basePath);
            }}
            onGoToRoute={onNavigate}
          />
        );
      })}
    </AppLauncherReorderList>
  );
};

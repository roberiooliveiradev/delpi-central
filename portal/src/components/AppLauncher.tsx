// src/components/AppLauncher.tsx

import { useContext, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import {
  Search,
} from "lucide-react";
import "./AppLauncher.css";
import { AppLauncherCard } from "./AppLauncherCard";

interface Props {
  onClose: () => void;
  dock?: "center" | "sidebar";
}

type RouteItem = {
  app: string;
  path: string;
  label?: string | null;
  icon?: string | null;
  order?: number;
  showInMenu?: boolean;
};

type AppItem = {
  id: string;
  name: string;
  icon?: string | null;
  base_path?: string;
};

type SearchResult =
  | { kind: "app"; app: AppItem; score: number }
  | { kind: "route"; app: AppItem; route: RouteItem; score: number };

function normalize(s: string) {
  return (s ?? "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .trim();
}


export const AppLauncher = ({ 
    onClose, 
    dock = "center" 
  }: Props) => {
  
  const {
    apps,
    routes,
    favorites,
    addFavorite,
    removeFavorite,
  } = useContext(AuthContext);

  const navigate = useNavigate();

  // const [openAppId, setOpenAppId] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  const inputRef = useRef<HTMLInputElement | null>(null);

  const [showAllPinned, setShowAllPinned] = useState(false);
  const [showAllRecent, setShowAllRecent] = useState(false);

  const RECENT_KEY = "delpi.recent.apps";

  const registerRecent = (appId: string) => {
    const existing = JSON.parse(
      localStorage.getItem(RECENT_KEY) || "[]"
    ) as string[];

    const next = [appId, ...existing.filter(id => id !== appId)].slice(0, 10);

    localStorage.setItem(RECENT_KEY, JSON.stringify(next));
  };
  
  const [openPinnedAppId, setOpenPinnedAppId] = useState<string | null>(null);
  const [openRecentAppId, setOpenRecentAppId] = useState<string | null>(null);
  
  // Autofocus + atalhos
  useEffect(() => {
    inputRef.current?.focus();

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();

      // Enter abre o primeiro resultado quando estiver pesquisando
      if (e.key === "Enter") {
        const q = normalize(query);
        if (!q) return;

        const first = searchResults[0];
        if (!first) return;

        e.preventDefault();
        if (first.kind === "route") goTo(first.route.path);
        if (first.kind === "app") openAppOrDefault(first.app.id);
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query]);

  const routesByApp = useMemo(() => {
    const map: Record<string, RouteItem[]> = {};
    (apps ?? []).forEach((a: any) => (map[a.id] = []));

    (routes ?? []).forEach((r: RouteItem) => {
      if (!r?.app || !map[r.app]) return;
      map[r.app].push(r);
    });

    Object.keys(map).forEach((appId) => {
      map[appId] = map[appId]
        .slice()
        .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
        .sort((a, b) => {
          const la = (a.label ?? a.path) as string;
          const lb = (b.label ?? b.path) as string;
          return la.localeCompare(lb);
        });
    });

    return map;
  }, [apps, routes]);

  const prettifyLabel = (route: RouteItem) => {
    if (route.label) return route.label;
    const last =
      route.path
        .split("/")
        .filter(Boolean)
        .pop()
        ?.replace(/-/g, " ")
        .replace(/\b\w/g, (c: string) => c.toUpperCase()) ?? route.path;

    return last;
  };

  const goTo = (path: string) => {
    const route = routes.find(r => r.path === path);
    if (route?.app) registerRecent(route.app);

    navigate(path);
    onClose();
  };

  // const handleOpenApp = (appId: string) => {
  //   setOpenAppId((prev) => (prev === appId ? null : appId));
  // };

  const openAppOrDefault = (appId: string) => {
    const appRoutes = routesByApp[appId] ?? [];
    const hasNoRoutes = appRoutes.length === 0;
    const hasSingleRoute = appRoutes.length === 1;
    // const hasMultipleRoutes = appRoutes.length > 1;

    if (hasSingleRoute) {
      registerRecent(appId);
      goTo(appRoutes[0].path);
      return;
    }

    if (hasNoRoutes) {
      goTo("/");
      return;
    }

    if (hasSingleRoute) {
      goTo(appRoutes[0].path);
      return;
    }

    // if (hasMultipleRoutes) {
    //   handleOpenApp(appId);
    // }
  };

  const togglePin = async (appId: string) => {
    const isPinned = favorites.some(f => f.id === appId);

    if (isPinned) {
      await removeFavorite(appId);
    } else {
      await addFavorite(appId);
    }
  };

  const pinnedApps = useMemo(() => {
    if (!favorites?.length) return apps.slice(0, 12);

    const favoriteIds = favorites.map(f => f.id);

    const pinnedOrdered = favoriteIds
      .map(id => apps.find(a => a.id === id))
      .filter(Boolean) as AppItem[];

    const rest = apps
      .filter(a => !favoriteIds.includes(a.id))
      .sort((a, b) => a.name.localeCompare(b.name));

    return [...pinnedOrdered, ...rest];
  }, [apps, favorites]);

  const visiblePinned = showAllPinned
  ? pinnedApps
  : pinnedApps.slice(0, 4);

  const recentApps = useMemo(() => {
    const stored = JSON.parse(
      localStorage.getItem(RECENT_KEY) || "[]"
    ) as string[];

    const ordered = stored
      .map(id => apps.find(a => a.id === id))
      .filter(Boolean) as AppItem[];

    return showAllRecent ? ordered : ordered.slice(0, 4);
  }, [apps, showAllRecent]);


  const searchResults: SearchResult[] = useMemo(() => {
    const q = normalize(query);
    if (!q) return [];

    const aList = (apps ?? []) as AppItem[];
    const results: SearchResult[] = [];

    for (const app of aList) {
      const appName = normalize(app.name);
      const appScore =
        appName === q ? 100 : appName.startsWith(q) ? 70 : appName.includes(q) ? 50 : 0;

      if (appScore > 0) results.push({ kind: "app", app, score: appScore });

      const appRoutes = routesByApp[app.id] ?? [];
      for (const route of appRoutes) {
        const label = normalize(prettifyLabel(route));
        const path = normalize(route.path);

        const score =
          label === q || path === q
            ? 95
            : label.startsWith(q) || path.startsWith(q)
              ? 65
              : label.includes(q) || path.includes(q)
                ? 45
                : 0;

        if (score > 0) results.push({ kind: "route", app, route, score });
      }
    }

    // Ordena por score desc, depois por nome/label
    return results
      .sort((a, b) => b.score - a.score)
      .slice(0, 24);
  }, [apps, query, routesByApp]);

  const isSearching = normalize(query).length > 0;

  return (
    <div 
      className="launcher-overlay" 
      data-dock={dock}
      onClick={onClose}
    >
      <div className={`launcher-modal startmenu ${
          dock === "sidebar" ? "dock-sidebar" : ""
        }`} onClick={(e) => e.stopPropagation()}>
        
        <div className="launcher-header">
          <span>Aplicativos</span>
          <button
            className="launcher-close"
            onClick={onClose}
            aria-label="Fechar"
          >
            ✕
          </button>
        </div>
        <div className="launcher-searchbar">
          <Search size={18} />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Pesquisar aplicativos disponíveis"
            aria-label="Pesquisar aplicativos"
          />
        </div>
        <div className="launcher-body">
          {!isSearching ? (
            <>
              <div className="launcher-section">
                <div className="launcher-section-header">
                  <span>Fixado</span>
                  <button
                    className="launcher-section-action"
                    onClick={() => setShowAllPinned(prev => !prev)}
                  >
                    {showAllPinned ? "Mostrar menos" : "Mostrar tudo"}
                  </button>
                </div>

                <div className="launcher-pinned-grid">
                  {visiblePinned.map((app) => {
                    const isPinned = favorites.some(f => f.id === app.id);
                    const isOpen = openPinnedAppId === app.id;
                    const appRoutes = routesByApp[app.id] ?? [];

                    return (
                      <AppLauncherCard
                        key={app.id}
                        app={app}
                        routes={appRoutes}
                        isOpen={isOpen}
                        isPinned={isPinned}
                        onToggleOpen={(id) => {
                          setOpenRecentAppId(null);
                          setOpenPinnedAppId(prev => (prev === id ? null : id));
                        }}
                        onOpenSingle={openAppOrDefault}
                        onGoToRoute={goTo}
                        onTogglePin={togglePin}
                      />
                    );
                  })}
                </div>
              </div>

              <div className="launcher-divider" />

              <div className="launcher-section">
                <div className="launcher-section-header">
                  <span>Recentes</span>
                  <button
                    className="launcher-section-action"
                    onClick={() => setShowAllRecent(prev => !prev)}
                  >
                    {showAllRecent ? "Mostrar menos" : "Mostrar tudo"}
                  </button>
                </div>

                {recentApps.length === 0 ? (
                  <div className="launcher-reco-empty">
                    Nenhum app acessado recentemente.
                  </div>
                ) : (
                  <div className="launcher-pinned-grid">
                    {recentApps.map(app => {
                      const isPinned = favorites.some(f => f.id === app.id);
                      const isOpen = openRecentAppId === app.id;
                      const appRoutes = routesByApp[app.id] ?? [];

                      return (
                        <AppLauncherCard
                          key={app.id}
                          app={app}
                          routes={appRoutes}
                          isOpen={isOpen}
                          isPinned={isPinned}
                          onToggleOpen={(id) => {
                            setOpenPinnedAppId(null);
                            setOpenRecentAppId(prev => (prev === id ? null : id));
                          }}
                          onOpenSingle={openAppOrDefault}
                          onGoToRoute={goTo}
                          onTogglePin={togglePin}
                        />
                      );
                    })}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="launcher-section">
              <div className="launcher-section-header">
                <span>Resultados</span>
                <span className="launcher-section-action">{searchResults.length} itens</span>
              </div>

              <div className="launcher-results">
                {searchResults.length === 0 ? (
                  <div className="launcher-empty">Nenhum resultado encontrado.</div>
                ) : (
                <div className="launcher-pinned-grid">
                  {searchResults.length === 0 ? (
                    <div className="launcher-empty">Nenhum resultado encontrado.</div>
                  ) : (
                    searchResults.map((r, idx) => {

                      if (r.kind === "app") {
                        const isPinned = favorites.some(f => f.id === r.app.id);
                        const appRoutes = routesByApp[r.app.id] ?? [];

                        return (
                          <AppLauncherCard
                            key={`app:${r.app.id}:${idx}`}
                            app={r.app}
                            routes={appRoutes}
                            isPinned={isPinned}
                            searchKind="app"
                            onOpenSingle={openAppOrDefault}
                            onGoToRoute={goTo}
                            onTogglePin={togglePin}
                          />
                        );
                      }

                      // resultado de rota
                      const isPinned = favorites.some(f => f.id === r.app.id);

                      return (
                        <AppLauncherCard
                          key={`route:${r.route.path}:${idx}`}
                          app={r.app}
                          routes={[r.route]}
                          isOpen={true}
                          isPinned={isPinned}
                          searchKind="route"
                          searchParentApp={r.app.name}
                          onOpenSingle={() => goTo(r.route.path)}
                          onGoToRoute={goTo}
                          onTogglePin={togglePin}
                        />
                      );
                    })
                  )}
                </div>
                )}
              </div>

              <div className="launcher-hint">
                Dica: pressione <kbd>Enter</kbd> para abrir o primeiro resultado,{" "}
                <kbd>Esc</kbd> para fechar.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
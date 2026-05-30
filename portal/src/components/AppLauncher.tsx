// src/components/AppLauncher.tsx

import { useContext, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import {
  Search,
  SearchX,
} from "lucide-react";
import "./AppLauncher.css";
import { AppLauncherCard } from "./AppLauncherCard";
import { useRoutesByApp } from "../hooks/useRoutesByApp";
import { pushRecentApp } from "../utils/recentApps";
import { filterLaunchableApps, isLaunchableApp } from "../utils/launchableApps";

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
  basePath?: string;
  type?: "iframe" | "microfrontend" | "backend-only";
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

  const [openAppId, setOpenAppId] = useState<string | null>(null);
  const [openSearchAppId, setOpenSearchAppId] = useState<string | null>(null);

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

  const routesByApp = useRoutesByApp();

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
    if (route?.app) pushRecentApp(route.app);

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
    const catalogApp = apps.find((app) => app.id === appId);

    if (hasSingleRoute) {
      pushRecentApp(appId);
      goTo(appRoutes[0].path);
      return;
    }

    if (hasNoRoutes) {
      if (catalogApp?.basePath) {
        pushRecentApp(appId);
        goTo(catalogApp.basePath);
      }
      return;
    }

    // Múltiplas rotas: expandir card (onToggleOpen)
  };

  const togglePin = async (appId: string) => {
    const catalogApp = apps.find((app) => app.id === appId);
    if (!isLaunchableApp(catalogApp)) return;

    const isPinned = favorites.some(f => f.id === appId);

    if (isPinned) {
      await removeFavorite(appId);
    } else {
      await addFavorite(appId);
    }
  };

  const launchableApps = useMemo(() => filterLaunchableApps(apps), [apps]);

  const availableApps = useMemo(() => {
    const favoriteIds = favorites.map(f => f.id);

    const pinnedOrdered = favoriteIds
      .map(id => launchableApps.find(a => a.id === id))
      .filter(Boolean) as AppItem[];

    const rest = launchableApps
      .filter(a => !favoriteIds.includes(a.id))
      .sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));

    return [...pinnedOrdered, ...rest];
  }, [launchableApps, favorites]);


  const searchResults: SearchResult[] = useMemo(() => {
    const q = normalize(query);
    if (!q) return [];

    const aList = launchableApps as AppItem[];
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
  }, [launchableApps, query, routesByApp]);

  const isSearching = normalize(query).length > 0;

  return (
    <div 
      className="launcher-overlay" 
      data-dock={dock}
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
            <div className="launcher-section">
              <div className="launcher-section-header">
                <span>Disponíveis</span>
                <span className="launcher-section-action">{availableApps.length} apps</span>
              </div>

              {availableApps.length === 0 ? (
                <div className="launcher-empty-state launcher-empty-state--catalog">
                  <div className="launcher-empty-icon" aria-hidden>
                    <SearchX size={28} strokeWidth={1.75} />
                  </div>
                  <p className="launcher-empty-title">Nenhum aplicativo disponível</p>
                  <p className="launcher-empty-message">
                    Sua conta ainda não tem apps liberados. Peça acesso ao administrador
                    ou tente novamente mais tarde.
                  </p>
                </div>
              ) : (
                <div className="launcher-pinned-grid">
                  {availableApps.map((app) => {
                    const isPinned = favorites.some(f => f.id === app.id);
                    const isOpen = openAppId === app.id;
                    const appRoutes = routesByApp[app.id] ?? [];

                    return (
                      <AppLauncherCard
                        key={app.id}
                        app={app}
                        routes={appRoutes}
                        isOpen={isOpen}
                        isPinned={isPinned}
                        onToggleOpen={(id) => {
                          setOpenAppId(prev => (prev === id ? null : id));
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
          ) : (
            <div className="launcher-section">
              <div className="launcher-section-header">
                <span>Resultados</span>
                <span className="launcher-section-action">{searchResults.length} itens</span>
              </div>

              <div className="launcher-results">
                {searchResults.length === 0 ? (
                  <div className="launcher-empty-state">
                    <div className="launcher-empty-icon" aria-hidden>
                      <SearchX size={28} strokeWidth={1.75} />
                    </div>
                    <p className="launcher-empty-title">Nenhum resultado encontrado</p>
                    <p className="launcher-empty-message">
                      Não encontramos apps ou rotas para{" "}
                      <span className="launcher-empty-query">“{query.trim()}”</span>.
                      Tente outro termo ou verifique a ortografia.
                    </p>
                    <button
                      type="button"
                      className="launcher-empty-clear"
                      onClick={() => {
                        setQuery("");
                        inputRef.current?.focus();
                      }}
                    >
                      Limpar busca
                    </button>
                  </div>
                ) : (
                <div className="launcher-pinned-grid">
                    {searchResults.map((r, idx) => {

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
                            isOpen={openSearchAppId === r.app.id}
                            onToggleOpen={(id) =>
                              setOpenSearchAppId(prev => (prev === id ? null : id))
                            }
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
                          onOpenSingle={() => goTo(r.route.path)}
                          onGoToRoute={goTo}
                          onTogglePin={togglePin}
                        />
                      );
                    })}
                </div>
                )}
              </div>

              {searchResults.length > 0 && (
              <div className="launcher-hint">
                Dica: pressione <kbd>Enter</kbd> para abrir o primeiro resultado,{" "}
                <kbd>Esc</kbd> para fechar.
              </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
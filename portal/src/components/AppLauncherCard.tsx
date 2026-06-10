import "./AppLauncherCard.css";
import { Package, ChevronDown, ChevronUp, Pin } from "lucide-react";
import { resolveIcon } from "../utils/iconResolver";
import { useLocation } from "react-router-dom";
import { useAppLauncherReorder } from "./AppLauncherReorderList";
import {
  launcherMotionIndexStyle,
  markAppRouteNavigationIntent,
  normalizeLauncherPath,
  isLauncherPathActive,
  isLauncherRouteSelected,
  isLauncherAppContextActive,
  useAppLauncherAppearance,
  useAppLauncherRouteNavigation,
  type AppLauncherAppearanceScope,
} from "./appLauncherAppearance";

type RouteItem = {
  path: string;
  label?: string | null;
  icon?: string | null;
  showInMenu?: boolean;
};

type AppItem = {
  id: string;
  name: string;
  icon?: string | null;
  base_path?: string | null;
  basePath?: string | null;
  type?: "iframe" | "microfrontend" | "backend-only";
};

type Variant = "launcher" | "home" | "sidebar";

function resolveAppLauncherNameTier(name: string): "short" | "medium" | "long" {
  const trimmed = name.trim();
  const length = trimmed.length;
  const longestWord = trimmed
    .split(/\s+/)
    .reduce((max, word) => Math.max(max, word.length), 0);

  if (length > 18 || longestWord > 13) {
    return "long";
  }

  if (length > 12 || longestWord > 10) {
    return "medium";
  }

  return "short";
}

interface Props {
  app: AppItem;
  routes: RouteItem[];
  variant?: Variant;

  isOpen?: boolean;
  isPinned?: boolean;

  searchKind?: "app" | "route";

  /** Habilita arrastar para reordenar (requer `AppLauncherReorderList` ancestral). */
  reorderable?: boolean;

  /** Animações de aparecimento e mudanças (nome, rotas, favorito). */
  appearanceEnabled?: boolean;
  appearanceScope?: AppLauncherAppearanceScope;
  motionIndex?: number;

  onToggleOpen?: (appId: string) => void;
  onOpenSingle: (appId: string) => void;
  onGoToRoute: (path: string) => void;
  onTogglePin?: (appId: string) => void;
}

export const AppLauncherCard = ({
  app,
  routes,
  variant = "launcher",
  isOpen = false,
  isPinned = false,
  searchKind,
  reorderable = false,
  appearanceEnabled = true,
  appearanceScope = "full",
  motionIndex,
  onToggleOpen,
  onOpenSingle,
  onGoToRoute,
  onTogglePin,
}: Props) => {
  const reorder = useAppLauncherReorder();
  const isReorderable = reorderable && !!reorder;

  const AppIcon = resolveIcon(app.icon) || Package;

  const isHome = variant === "home";
  const isSidebar = variant === "sidebar";

  const appearance = useAppLauncherAppearance(app.id, {
    name: app.name,
    routes,
    isPinned,
    enabled: appearanceEnabled && !isSidebar,
    scope: appearanceScope,
  });

  const location = useLocation();

  const visibleRoutes = routes.filter((route) => route.showInMenu !== false);
  const hasMultipleRoutes = visibleRoutes.length > 1 || searchKind === "route";

  const normalizePath = (value: string) => normalizeLauncherPath(value);
  const currentPath = normalizePath(location.pathname);

  const resolveAppBasePath = () => app.base_path ?? app.basePath ?? null;

  const defaultPath =
    visibleRoutes[0]?.path ||
    routes[0]?.path ||
    resolveAppBasePath();

  const isMainRouteActive =
    !!defaultPath && isLauncherPathActive(currentPath, defaultPath);
  const isAnyChildRouteActive = visibleRoutes.some((route) =>
    isLauncherPathActive(currentPath, route.path),
  );

  const isAppActive =
    app.type !== "backend-only" &&
    (isSidebar && hasMultipleRoutes
      ? isLauncherAppContextActive(currentPath, {
          routes: visibleRoutes,
          basePath: resolveAppBasePath(),
        })
      : isMainRouteActive || isAnyChildRouteActive);

  const sidebarRouteContext =
    isSidebar && hasMultipleRoutes && isAppActive;
  const showSidebarExpanded = isOpen || sidebarRouteContext;

  const routeNavigation = useAppLauncherRouteNavigation(app.id, {
    routes: visibleRoutes,
    currentPath,
    isRoutesOpen:
      isOpen || sidebarRouteContext || searchKind === "route",
    enabled: Boolean(app.id) && !isSidebar,
  });

  const prettifyLabel = (route: RouteItem) => {
    if (route.label) return route.label;
    return (
      route.path
        .split("/")
        .filter(Boolean)
        .pop()
        ?.replace(/-/g, " ")
        .replace(/\b\w/g, (c: string) => c.toUpperCase()) ?? route.path
    );
  };

  const isModifiedEvent = (
    event: React.MouseEvent<HTMLAnchorElement>,
  ) => {
    return (
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    );
  };

  const isDragging = isReorderable && reorder!.draggingId === app.id;
  const isHolding = isReorderable && reorder!.holdingId === app.id;
  const isDropTarget =
    isReorderable &&
    reorder!.dropTargetId === app.id &&
    reorder!.draggingId !== app.id;

  const activateMain = () => {
    if (isSidebar && hasMultipleRoutes) {
      const path =
        defaultPath ??
        visibleRoutes[0]?.path ??
        routes[0]?.path ??
        null;

      if (path) {
        if (!isOpen) {
          onToggleOpen?.(app.id);
        }
        markAppRouteNavigationIntent(app.id, path);
        onGoToRoute(path);
      }

      return;
    }

    if (!hasMultipleRoutes) {
      if (visibleRoutes[0]) {
        markAppRouteNavigationIntent(app.id, visibleRoutes[0].path);
        onGoToRoute(visibleRoutes[0].path);
        return;
      }

      if (routes[0]) {
        markAppRouteNavigationIntent(app.id, routes[0].path);
        onGoToRoute(routes[0].path);
        return;
      }

      onOpenSingle(app.id);
      return;
    }

    onToggleOpen?.(app.id);
  };

  const handleMainClick = (event: React.MouseEvent<HTMLAnchorElement>) => {
    if (isModifiedEvent(event)) {
      return;
    }

    event.preventDefault();
    activateMain();
  };

  const handleRouteClick = (
    event: React.MouseEvent<HTMLAnchorElement>,
    path: string,
  ) => {
    event.stopPropagation();

    if (isModifiedEvent(event)) {
      return;
    }

    event.preventDefault();
    markAppRouteNavigationIntent(app.id, path);
    onGoToRoute(path);
  };

  const handleRoutePointerDown = (
    event: React.PointerEvent<HTMLAnchorElement>,
  ) => {
    event.stopPropagation();
  };

  const handleToggleRoutes = (
    event: React.MouseEvent<HTMLButtonElement>,
  ) => {
    event.preventDefault();
    event.stopPropagation();

    if (sidebarRouteContext && isOpen) {
      return;
    }

    onToggleOpen?.(app.id);
  };

  const reorderPointerProps = isReorderable
    ? {
        onPointerDown: reorder!.onPointerDown(app.id),
        onPointerMove: reorder!.onPointerMove,
        onPointerUp: (event: React.PointerEvent<HTMLAnchorElement>) =>
          void reorder!.onPointerFinish(event),
        onPointerCancel: (event: React.PointerEvent<HTMLAnchorElement>) =>
          void reorder!.onPointerFinish(event),
        onClickCapture: reorder!.onClickCapture,
        onDragStart: (event: React.DragEvent<HTMLAnchorElement>) => {
          event.preventDefault();
          event.stopPropagation();
        },
        onMouseDown: (event: React.MouseEvent<HTMLAnchorElement>) => {
          if (event.button !== 0) return;
          if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
            return;
          }
          // Evita arraste nativo do link (prévia do Firefox) sem bloquear clique rápido.
          event.preventDefault();
        },
      }
    : {};

  const nameTier = resolveAppLauncherNameTier(app.name);

  const showSidebarInlineRoutes =
    isSidebar &&
    hasMultipleRoutes &&
    (showSidebarExpanded || searchKind === "route");

  const showLauncherInlineRoutes =
    !isSidebar && (isOpen || searchKind === "route");

  const routesPanelExpanded = showSidebarInlineRoutes || showLauncherInlineRoutes;
  const routesPanelMounted =
    hasMultipleRoutes && visibleRoutes.length > 0;

  const mainClassName = `launcher-app-main ${isAppActive ? "active" : ""}`;

  const mainContent = (
    <>
      <span className="launcher-app-icon">
        <AppIcon size={isSidebar ? 18 : isHome ? 22 : 26} />
      </span>

      <div className="launcher-app-container-name">
        <span
          className={["launcher-app-name", appearance.nameClass]
            .filter(Boolean)
            .join(" ")}
          data-name-tier={nameTier}
          lang="pt-BR"
          title={app.name}
        >
          {app.name}
        </span>

        {hasMultipleRoutes &&
          (isSidebar ? (
            <button
              type="button"
              className="launcher-chevron-toggle"
              onClick={handleToggleRoutes}
              aria-expanded={showSidebarExpanded}
              aria-label={isOpen ? "Recolher rotas" : "Expandir rotas"}
            >
              <ChevronUp
                size={16}
                className={`launcher-chevron ${showSidebarExpanded ? "rotated" : ""}`}
              />
            </button>
          ) : (
            <ChevronDown
              size={16}
              className={`launcher-chevron ${isOpen ? "rotated" : ""}`}
            />
          ))}
      </div>
    </>
  );

  return (
    <div
      data-app-id={isReorderable ? app.id : undefined}
      className={[
        "launcher-app-tile",
        (isSidebar ? hasMultipleRoutes && showSidebarExpanded : isOpen)
          ? "expanded"
          : "",
        sidebarRouteContext ? "route-active" : "",
        isAppActive && !(isSidebar && sidebarRouteContext) ? "active" : "",
        isHome ? "home-variant" : "",
        isSidebar ? "sidebar-variant" : "",
        isReorderable ? "reorderable app-launcher-reorder-item" : "",
        isHolding ? "is-reorder-holding" : "",
        isDragging ? "is-reorder-dragging" : "",
        isDropTarget ? "is-reorder-drop-target" : "",
        appearance.tileClass,
        !isSidebar ? routeNavigation.tileRouteClass : "",
      ]
        .filter(Boolean)
        .join(" ")}
      style={launcherMotionIndexStyle(motionIndex)}
    >
      {onTogglePin && !isSidebar && (
        <button
          type="button"
          className={[
            "launcher-pin",
            isPinned ? "pinned" : "",
            appearance.pinClass,
          ]
            .filter(Boolean)
            .join(" ")}
          onClick={(e) => {
            e.stopPropagation();
            onTogglePin(app.id);
          }}
          aria-label={isPinned ? "Desafixar aplicativo" : "Fixar aplicativo"}
        >
          <Pin size={13} strokeWidth={1.85} aria-hidden />
        </button>
      )}

      <a
        href={defaultPath ?? "#"}
        className={mainClassName}
        draggable={isReorderable ? false : undefined}
        onClick={handleMainClick}
        aria-expanded={isSidebar && hasMultipleRoutes ? showSidebarExpanded : isOpen}
        aria-current={isAppActive ? "page" : undefined}
        {...reorderPointerProps}
      >
        {(isHolding || isDragging) && (
          <span className="launcher-reorder-hint" aria-live="polite">
            {isDragging
              ? "Solte para reordenar"
              : "Arraste para reordenar os favoritos"}
          </span>
        )}
        {mainContent}
      </a>

      {routesPanelMounted && (
        <div
          className={[
            "launcher-inline-routes-panel",
            routesPanelExpanded ? "is-expanded" : "",
            isSidebar
              ? "launcher-inline-routes-panel--sidebar"
              : "launcher-inline-routes-panel--launcher",
          ]
            .filter(Boolean)
            .join(" ")}
          aria-hidden={!routesPanelExpanded}
        >
          <div className="launcher-inline-routes-panel__inner">
            <div
              className={[
                isSidebar ? "sidebar-inline-routes" : "launcher-inline-routes",
                !isSidebar ? appearance.routesClass : "",
                !isSidebar ? routeNavigation.routesPanelClass : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {visibleRoutes.map((route) => {
                const Icon = resolveIcon(route.icon) || Package;
                const routePath = normalizePath(route.path);
                const isActive = isLauncherRouteSelected(
                  currentPath,
                  route.path,
                  visibleRoutes,
                );
                const isNavigated =
                  routeNavigation.activatedRoutePath === routePath;

                return (
                  <a
                    key={route.path}
                    href={route.path}
                    className={[
                      isSidebar
                        ? "sidebar-inline-route"
                        : "launcher-inline-route",
                      isActive ? "active" : "",
                      !isSidebar && isNavigated
                        ? "launcher-inline-route--navigated"
                        : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    onClick={(event) => handleRouteClick(event, route.path)}
                    onPointerDown={handleRoutePointerDown}
                    aria-current={isActive ? "page" : undefined}
                    tabIndex={routesPanelExpanded ? undefined : -1}
                  >
                    <Icon size={16} />
                    <span>{prettifyLabel(route)}</span>
                  </a>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

import "./AppLauncherCard.css";
import { Package, ChevronDown, ChevronUp, Pin } from "lucide-react";
import { resolveIcon } from "../utils/iconResolver";
import { useLocation } from "react-router-dom";
import { useAppLauncherReorder } from "./AppLauncherReorderList";

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

interface Props {
  app: AppItem;
  routes: RouteItem[];
  variant?: Variant;

  isOpen?: boolean;
  isPinned?: boolean;

  searchKind?: "app" | "route";

  /** Habilita arrastar para reordenar (requer `AppLauncherReorderList` ancestral). */
  reorderable?: boolean;

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

  const location = useLocation();

  const visibleRoutes = routes.filter((route) => route.showInMenu !== false);
  const hasMultipleRoutes = visibleRoutes.length > 1 || searchKind === "route";

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

  const resolveAppBasePath = () => app.base_path ?? app.basePath ?? null;

  const defaultPath =
    visibleRoutes[0]?.path ||
    routes[0]?.path ||
    resolveAppBasePath();

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

  const normalizePath = (value: string) => value.replace(/\/+$/, "") || "/";

  const currentPath = normalizePath(location.pathname);

  const isMainRouteActive =
    !!defaultPath && currentPath === normalizePath(defaultPath);
  const isAnyChildRouteActive = visibleRoutes.some(
    (route) => normalizePath(route.path) === currentPath,
  );

  const isAppActive =
    app.type !== "backend-only" &&
    (isMainRouteActive || isAnyChildRouteActive);

  const isDragging = isReorderable && reorder!.draggingId === app.id;
  const isHolding = isReorderable && reorder!.holdingId === app.id;
  const isDropTarget =
    isReorderable &&
    reorder!.dropTargetId === app.id &&
    reorder!.draggingId !== app.id;

  const activateMain = () => {
    if (!hasMultipleRoutes) {
      if (visibleRoutes[0]) {
        onGoToRoute(visibleRoutes[0].path);
        return;
      }

      if (routes[0]) {
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
    if (isModifiedEvent(event)) {
      return;
    }

    event.preventDefault();
    onGoToRoute(path);
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

  const mainClassName = `launcher-app-main ${isAppActive ? "active" : ""}`;
  const mainContent = (
    <>
      <span className="launcher-app-icon">
        <AppIcon size={isSidebar ? 18 : isHome ? 22 : 26} />
      </span>

      <div className="launcher-app-container-name">
        <span className="launcher-app-name">{app.name}</span>

        {hasMultipleRoutes &&
          (isSidebar ? (
            <ChevronUp
              size={16}
              className={`launcher-chevron ${isOpen ? "rotated" : ""}`}
            />
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
        isOpen ? "expanded" : "",
        isAppActive ? "active" : "",
        isHome ? "home-variant" : "",
        isSidebar ? "sidebar-variant" : "",
        isReorderable ? "reorderable app-launcher-reorder-item" : "",
        isHolding ? "is-reorder-holding" : "",
        isDragging ? "is-reorder-dragging" : "",
        isDropTarget ? "is-reorder-drop-target" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {onTogglePin && !isSidebar && (
        <button
          type="button"
          className={`launcher-pin ${isPinned ? "pinned" : ""}`}
          onClick={(e) => {
            e.stopPropagation();
            onTogglePin(app.id);
          }}
          aria-label={isPinned ? "Desafixar aplicativo" : "Fixar aplicativo"}
        >
          <Pin size={14} />
        </button>
      )}

      <a
        href={defaultPath ?? "#"}
        className={mainClassName}
        draggable={isReorderable ? false : undefined}
        onClick={handleMainClick}
        aria-expanded={hasMultipleRoutes ? isOpen : undefined}
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

      {(isOpen || searchKind === "route") && visibleRoutes.length > 0 && (
        <div
          className={
            isSidebar
              ? "sidebar-inline-routes"
              : "launcher-inline-routes"
          }
        >
          {visibleRoutes.map((route) => {
            const Icon = resolveIcon(route.icon) || Package;
            const isActive = normalizePath(route.path) === currentPath;

            return (
              <a
                key={route.path}
                href={route.path}
                className={
                  isSidebar
                    ? `sidebar-inline-route ${isActive ? "active" : ""}`
                    : `launcher-inline-route ${isActive ? "active" : ""}`
                }
                onClick={(event) => handleRouteClick(event, route.path)}
                aria-current={isActive ? "page" : undefined}
              >
                <Icon size={16} />
                <span>{prettifyLabel(route)}</span>
              </a>
            );
          })}
        </div>
      )}
    </div>
  );
};

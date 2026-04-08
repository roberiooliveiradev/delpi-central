// src/components/AppLauncherCard.tsx
import "./AppLauncherCard.css";
import { Package, ChevronDown, ChevronUp, Pin } from "lucide-react";
import { resolveIcon } from "../utils/iconResolver";
import { useLocation } from "react-router-dom";
type RouteItem = {
  path: string;
  label?: string | null;
  icon?: string | null;
};

type AppItem = {
  id: string;
  name: string;
  icon?: string | null;
};

type Variant = "launcher" | "home" | "sidebar";

interface Props {
  app: AppItem;
  routes: RouteItem[];
  variant?: Variant;

  isOpen?: boolean;
  isPinned?: boolean;

  searchKind?: "app" | "route";

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
  onToggleOpen,
  onOpenSingle,
  onGoToRoute,
  onTogglePin,
}: Props) => {
  const AppIcon = resolveIcon(app.icon) || Package;

  const isLauncher = variant === "launcher";
  const isHome = variant === "home";
  const isSidebar = variant === "sidebar";
  const location = useLocation();
  const hasMultipleRoutes = routes.length > 1 || searchKind === "route";

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

const handleMainClick = () => {
  if (!hasMultipleRoutes) {
    if (routes[0]) onGoToRoute(routes[0].path);
    else onOpenSingle(app.id);
    return;
  }

  onToggleOpen?.(app.id);
};

  return (
    <div
      className={`
        launcher-app-tile
        ${isOpen ? "expanded" : ""}
        ${isHome ? "home-variant" : ""}
        ${isSidebar ? "sidebar-variant" : ""}
      `}
    >
      {/* PIN só no launcher */}
      {isLauncher && onTogglePin && (
        <span
          className={`launcher-pin ${isPinned ? "pinned" : ""}`}
          onClick={(e) => {
            e.stopPropagation();
            onTogglePin(app.id);
          }}
        >
          <Pin size={14} />
        </span>
      )}

      {/* HEADER */}
      <div className="launcher-app-main" onClick={handleMainClick}>
        <span className="launcher-app-icon">
          <AppIcon size={isSidebar ? 18 : isHome ? 22 : 26} />
        </span>
        <div className="launcher-app-container-name">

          <span className="launcher-app-name">{app.name}</span>

          {hasMultipleRoutes && (
            isSidebar ? (
              <ChevronUp
                size={16}
                className={`launcher-chevron ${isOpen ? "rotated" : ""}`}
              />
            ) : (
              <ChevronDown
                size={16}
                className={`launcher-chevron ${isOpen ? "rotated" : ""}`}
              />
            )
          )}
        </div>
      </div>

      {/* ROUTES */}
      {(isOpen || searchKind === "route") && routes.length > 0 && (
        <div
          className={
            isSidebar
              ? "sidebar-inline-routes"
              : "launcher-inline-routes"
          }
        >
          {routes
            .filter((route: any) => route.showInMenu !== false)
            .map((route) => {
            const Icon = resolveIcon(route.icon) || Package;

            const isActive = location.pathname === route.path;

            return (
              <button
                key={route.path}
                className={
                  isSidebar
                    ? `sidebar-inline-route ${isActive ? "active" : ""}`
                    : `launcher-inline-route ${isActive ? "active" : ""}`
                }
                onClick={() => onGoToRoute(route.path)}
              >
                <Icon size={16} />
                <span>{prettifyLabel(route)}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
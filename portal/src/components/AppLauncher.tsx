import { useContext, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import { resolveIcon } from "../utils/iconResolver";
import { Package, ChevronDown, ChevronUp } from "lucide-react";
import "./AppLauncher.css"

interface Props {
  onClose: () => void;
}

type RouteItem = {
  app: string;
  path: string;
  label?: string | null;
  icon?: string | null;
  order?: number;
};

export const AppLauncher = ({ onClose }: Props) => {
  const { apps, routes } = useContext(AuthContext);
  const navigate = useNavigate();

  const [openAppId, setOpenAppId] = useState<string | null>(null);

  const routesByApp = useMemo(() => {
    const map: Record<string, RouteItem[]> = {};

    (apps ?? []).forEach((app: any) => {
      map[app.id] = [];
    });

    (routes ?? []).forEach((r: RouteItem) => {
      if (!r?.app || !map[r.app]) return;
      map[r.app].push(r);
    });

    // ordena por order (se existir) e depois por label/path
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

  const handleOpenApp = (appId: string) => {
    setOpenAppId((prev) => (prev === appId ? null : appId));
  };

  const goTo = (path: string) => {
    navigate(path);
    onClose();
  };

  return (
    <div className="launcher-overlay" onClick={onClose}>
      <div className="launcher-modal" onClick={(e) => e.stopPropagation()}>
        <h3 style={{ marginBottom: 20 }}>Aplicações</h3>

        <div className="launcher-grid">
          {(apps ?? []).map((app: any) => {
            const AppIcon = resolveIcon(app.icon) || Package;

            const appRoutes = routesByApp[app.id] ?? [];
            const isOpen = openAppId === app.id;

            const hasNoRoutes = appRoutes.length === 0;
            const hasSingleRoute = appRoutes.length === 1;
            const hasMultipleRoutes = appRoutes.length > 1;

            return (
              <div
                key={app.id}
                className={`launcher-card ${isOpen ? "open" : ""}`}
                onClick={() => {
                  // comportamento alinhado com a Sidebar:
                  // - sem rotas => volta pra /
                  // - 1 rota => navega direto
                  // - +1 rotas => expande para escolher
                  if (hasNoRoutes) {
                    goTo("/");
                    return;
                  }

                  if (hasSingleRoute) {
                    goTo(appRoutes[0].path);
                    return;
                  }

                  handleOpenApp(app.id);
                }}
                role="button"
                tabIndex={0}
              >
                <div className="launcher-card-header">
                  <div className="launcher-icon">
                    <AppIcon size={28} />
                  </div>

                  <div className="launcher-card-title">
                    <span>{app.name}</span>
                    {hasMultipleRoutes && (
                      <span className="launcher-card-subtitle">
                        Selecione uma rota
                      </span>
                    )}
                  </div>

                  {hasMultipleRoutes && (
                    <div className="launcher-card-chevron">
                      {isOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                    </div>
                  )}
                </div>

                {hasMultipleRoutes && isOpen && (
                  <div
                    className="launcher-routes"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {appRoutes.map((route) => {
                      const Icon = resolveIcon(route.icon) || Package;

                      return (
                        <button
                          key={route.path}
                          type="button"
                          className="launcher-route-item"
                          onClick={() => goTo(route.path)}
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
          })}
        </div>
      </div>
    </div>
  );
};
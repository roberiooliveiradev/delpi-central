import "./Sidebar.css";
import {
  useContext,
  useMemo,
  useState,
  useEffect,
  useRef,
  useCallback,
} from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import { useTheme } from "../hooks/useTheme";
import { AppLauncher } from "../components/AppLauncher";

import {
  Bell,
  Sun,
  Moon,
  Grid,
  Shield,
  ShieldCheck,
  ChevronDown,
  ChevronRight,
  CircleDashed,
  User,
  LogOut,
  ChevronLeft,
  FileText,
} from "lucide-react";

import { AppLauncherCard } from "../components/AppLauncherCard";
import { NotificationCard } from "../components/notifications/NotificationCard";
import { useNotificationActions } from "../components/notifications/useNotificationActions";
import { DELPI_OPEN_APP_LAUNCHER_EVENT } from "../utils/appLauncher";
import { isLaunchableApp } from "../utils/launchableApps";

type GroupedRoutes = Record<
  string,
  {
    appName: string;
    appIcon?: string | null;
    routes: any[];
  }
>;

export const Sidebar = () => {
  const {
    routes,
    apps,
    user,
    logout,
    notifications,
    favorites,
    markAllNotificationsRead,
    reloadNotifications,
  } = useContext(AuthContext);

  const { markNotificationRead, handleDelete, handleToggleImportant } = useNotificationActions();

  const navigate = useNavigate();
  const { theme, setTheme } = useTheme();

  const containerRef = useRef<HTMLDivElement>(null);
  const userDropdownRef = useRef<HTMLDivElement>(null);
  const notifDropdownRef = useRef<HTMLDivElement>(null);
  const themeDropdownRef = useRef<HTMLDivElement>(null);

  /* ===============================
     ESTADOS
  =============================== */

  const [collapsed, setCollapsed] = useState(() => {
    return localStorage.getItem("sidebar-collapsed") === "true";
  });

  const [openApps, setOpenApps] = useState<Record<string, boolean>>({});
  const [userOpen, setUserOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [launcherOpen, setLauncherOpen] = useState(false);
  const [themeOpen, setThemeOpen] = useState(false);
  const [showEdgeExpand, setShowEdgeExpand] = useState(false);

  useEffect(() => {
    localStorage.setItem("sidebar-collapsed", String(collapsed));
  }, [collapsed]);

  useEffect(() => {
    const openLauncher = () => setLauncherOpen(true);
    window.addEventListener(DELPI_OPEN_APP_LAUNCHER_EVENT, openLauncher);
    return () => window.removeEventListener(DELPI_OPEN_APP_LAUNCHER_EVENT, openLauncher);
  }, []);

  const openSidebarFromEdge = useCallback(() => {
    setCollapsed(false);
    setShowEdgeExpand(false);
  }, []);

  const hideEdgeExpand = useCallback(() => {
    setShowEdgeExpand(false);
  }, []);

  const showEdgeExpandHint = useCallback(() => {
    if (!collapsed) return;
    setShowEdgeExpand(true);
  }, [collapsed]);

  const handleEdgePointerMove = useCallback(
    (event: PointerEvent) => {
      if (!collapsed) {
        setShowEdgeExpand(false);
        return;
      }

      const edgeWidth = event.pointerType === "touch" ? 34 : 24;

      if (event.clientX <= edgeWidth) {
        setShowEdgeExpand(true);
        return;
      }

      setShowEdgeExpand(false);
    },
    [collapsed],
  );

  const handleEdgeTouchStart = useCallback(
    (event: TouchEvent) => {
      if (!collapsed) return;

      const touch = event.touches[0];
      if (!touch) return;

      if (touch.clientX <= 36) {
        setShowEdgeExpand(true);
      }
    },
    [collapsed],
  );

  useEffect(() => {
    if (!collapsed) {
      setShowEdgeExpand(false);
      return;
    }

    window.addEventListener("pointermove", handleEdgePointerMove, {
      passive: true,
    });

    window.addEventListener("touchstart", handleEdgeTouchStart, {
      passive: true,
    });

    window.addEventListener("scroll", hideEdgeExpand, {
      passive: true,
    });

    return () => {
      window.removeEventListener("pointermove", handleEdgePointerMove);
      window.removeEventListener("touchstart", handleEdgeTouchStart);
      window.removeEventListener("scroll", hideEdgeExpand);
    };
  }, [
    collapsed,
    handleEdgePointerMove,
    handleEdgeTouchStart,
    hideEdgeExpand,
  ]);

  useEffect(() => {
    if (!collapsed) {
      setShowEdgeExpand(false);
    }
  }, [collapsed]);

  // Fecha dropdown ao clicar fora
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;

      if (
        themeOpen &&
        themeDropdownRef.current &&
        !themeDropdownRef.current.contains(target)
      ) {
        setThemeOpen(false);
      }

      if (
        notifOpen &&
        notifDropdownRef.current &&
        !notifDropdownRef.current.contains(target)
      ) {
        setNotifOpen(false);
      }

      if (
        userOpen &&
        userDropdownRef.current &&
        !userDropdownRef.current.contains(target)
      ) {
        setUserOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [userOpen, notifOpen, themeOpen]);

  /* ===============================
     AGRUPAMENTO DE ROTAS
  =============================== */

  const grouped: GroupedRoutes = useMemo(() => {
    const map: GroupedRoutes = {};

    apps?.forEach((app: any) => {
      map[app.id] = {
        appName: app.name,
        appIcon: app.icon ?? null,
        routes: [],
      };
    });

    routes.forEach((route: any) => {
      if (!map[route.app]) return;
      if (route.showInMenu === false) return;

      map[route.app].routes.push(route);
    });

    return map;
  }, [apps, routes]);

  const pinnedGroupedEntries = useMemo(() => {
    if (!favorites?.length) return [];

    return favorites
      .filter((fav) => isLaunchableApp(apps.find((app) => app.id === fav.id)))
      .map((fav) => [fav.id, grouped[fav.id]] as const)
      .filter(([, group]) => !!group);
  }, [favorites, grouped, apps]);

  /* ===============================
     DADOS GERAIS
  =============================== */

  const unreadCount = notifications.filter((n) => !n.read).length;

  const initials = (() => {
    if (!user?.name) return "?";
    const parts = user.name.trim().split(" ").filter(Boolean);
    const first = parts[0]?.[0] ?? "";
    const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
    return (first + last).toUpperCase() || "?";
  })();

  /* ========================================
     ADMINISTRADOR
  ======================================== */
  const canAccessAdmin =
    user?.is_superadmin || user?.permissions?.includes("rbac.manage");

  /* ========================================
     RENDER
  ======================================== */

  return (
    <>
      {collapsed && (
        <>
          <button
            className={`sidebar-expand-btn ${showEdgeExpand ? "is-visible" : ""}`}
            onClick={openSidebarFromEdge}
            onMouseEnter={showEdgeExpandHint}
            aria-label="Expandir menu lateral"
            type="button"
          >
            <span className="sidebar-expand-btn__icon">
              <ChevronRight size={18} />
            </span>
          </button>

          <button
            className="sidebar-edge-hotspot"
            type="button"
            aria-label="Abrir menu lateral"
            onMouseEnter={showEdgeExpandHint}
            onTouchStart={showEdgeExpandHint}
            onFocus={showEdgeExpandHint}
            onClick={openSidebarFromEdge}
          />
        </>
      )}

      <div
        className={`sidebar ${collapsed ? "collapsed" : ""}`}
        ref={containerRef}
      >
        {!collapsed && (
          <>
            <div className="sidebar-header">
              <div
                className="sidebar-logo"
                onClick={() => navigate("/")}
                style={{ cursor: "pointer" }}
              >
                <img
                  src="/logoMinhaDelpi.svg"
                  alt="Transforma mais DELPI"
                />
              </div>

              <button
                className="collapse-btn"
                onClick={() => setCollapsed(true)}
                type="button"
              >
                <ChevronLeft size={18} />
              </button>
            </div>

            <div className="sidebar-content">
              {pinnedGroupedEntries.map(([appId, group]) => {
                const isOpen = openApps[appId] ?? false;
                const catalogApp = apps.find((app) => app.id === appId);

                return (
                  <AppLauncherCard
                    key={appId}
                    variant="sidebar"
                    app={
                      catalogApp ?? {
                        id: appId,
                        name: group.appName,
                        icon: group.appIcon,
                      }
                    }
                    routes={group.routes}
                    isOpen={isOpen}
                    onToggleOpen={(id) =>
                      setOpenApps((prev) => ({
                        ...prev,
                        [id]: !prev[id],
                      }))
                    }
                    onOpenSingle={() => {
                      const route = group.routes[0];
                      if (route) {
                        navigate(route.path);
                        return;
                      }
                      if (catalogApp?.basePath) navigate(catalogApp.basePath);
                    }}
                    onGoToRoute={(path) => navigate(path)}
                  />
                );
              })}
            </div>

            <div className="sidebar-footer">
              {canAccessAdmin && (
                <NavLink to="/admin" className="sidebar-footer-item">
                  <Shield size={18} />
                  <span>Admin</span>
                </NavLink>
              )}

              <div
                className="sidebar-footer-item"
                onClick={() => {
                  setNotifOpen((open) => {
                    if (!open) void reloadNotifications();
                    return !open;
                  });
                }}
              >
                <Bell size={18} />
                <span>Notificações</span>
                {unreadCount > 0 && (
                  <span className="notif-badge">{unreadCount}</span>
                )}
              </div>

              {notifOpen && (
                <div
                  className="notif-dropdown sidebar-notif"
                  ref={notifDropdownRef}
                >
                  {notifications.length === 0 && (
                    <div className="notif-item">Sem notificações</div>
                  )}

                  <div
                    className="notif-item notif-item--link"
                    onClick={() => {
                      setNotifOpen(false);
                      navigate("/notifications");
                    }}
                  >
                    Ver todas
                  </div>

                  {notifications.length > 0 && (
                    <div
                      className="notif-item mark-all"
                      onClick={markAllNotificationsRead}
                    >
                      Marcar todas como lidas
                    </div>
                  )}

                  <div className="sidebar-notif__list">
                    {notifications.map((n) => (
                      <NotificationCard
                        key={n.id}
                        notification={n}
                        compact
                        onMarkRead={markNotificationRead}
                        onDelete={(id) => void handleDelete(id)}
                        onToggleImportant={(id, isImportant) =>
                          void handleToggleImportant(id, isImportant)
                        }
                        onNavigate={() => setNotifOpen(false)}
                      />
                    ))}
                  </div>
                </div>
              )}

              <div
                className="sidebar-footer-item"
                onClick={() => setLauncherOpen(true)}
              >
                <Grid size={18} />
                <span>Apps</span>
              </div>

              <div
                className="sidebar-footer-item"
                onClick={() => setThemeOpen(!themeOpen)}
              >
                {theme === "dark" ? (
                  <Moon size={18} />
                ) : theme === "light" ? (
                  <Sun size={18} />
                ) : (
                  <CircleDashed size={18} />
                )}
                <span>Tema</span>
                <ChevronDown size={16} />
              </div>

              {themeOpen && (
                <div
                  className="dropdown sidebar-user"
                  ref={themeDropdownRef}
                >
                  <div
                    className={`dropdown-item ${theme === "light" ? "active" : ""}`}
                    onClick={() => {
                      setTheme("light");
                      setThemeOpen(false);
                    }}
                  >
                    <Sun size={18} /> Claro
                  </div>

                  <div
                    className={`dropdown-item ${theme === "dark" ? "active" : ""}`}
                    onClick={() => {
                      setTheme("dark");
                      setThemeOpen(false);
                    }}
                  >
                    <Moon size={18} /> Escuro
                  </div>

                  <div
                    className={`dropdown-item ${theme === "system" ? "active" : ""}`}
                    onClick={() => {
                      setTheme("system");
                      setThemeOpen(false);
                    }}
                  >
                    <CircleDashed size={18} /> Sistema
                  </div>
                </div>
              )}

              <div
                className="sidebar-footer-item"
                onClick={() => setUserOpen(!userOpen)}
              >
                <div className="avatar small">{initials}</div>
                <span>{user?.name}</span>
                <ChevronDown size={16} />
              </div>

              {userOpen && (
                <div
                  className="dropdown sidebar-user"
                  ref={userDropdownRef}
                >
                  <div
                    className="dropdown-item"
                    onClick={() => {
                      navigate("/profile");
                      setUserOpen(false);
                    }}
                  >
                    <User size={16} />
                    Meu Perfil
                  </div>

                  <div
                    className="dropdown-item"
                    onClick={() => {
                      navigate("/privacy");
                      setUserOpen(false);
                    }}
                  >
                    <ShieldCheck size={16} />
                    Privacidade e Dados
                  </div>

                  <div
                    className="dropdown-item"
                    onClick={() => {
                      navigate("/privacy-policy");
                      setUserOpen(false);
                    }}
                  >
                    <FileText size={16} />
                    Política de Privacidade
                  </div>

                  <div
                    className="dropdown-item danger"
                    onClick={logout}
                  >
                    <LogOut />
                    Sair
                  </div>
                </div>
              )}

              <NavLink
                to="/privacy-policy"
                className="sidebar-footer__privacy-link"
              >
                Política de Privacidade
              </NavLink>
            </div>
          </>
        )}
      </div>

      {launcherOpen && (
        <AppLauncher
          dock="sidebar"
          onClose={() => setLauncherOpen(false)}
        />
      )}
    </>
  );
};
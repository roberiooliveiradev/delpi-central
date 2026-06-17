import "./Sidebar.css";
import {
  useContext,
  useMemo,
  useState,
  useEffect,
  useRef,
  useCallback,
} from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import { useTheme } from "../hooks/useTheme";
import { AppLauncher } from "../components/AppLauncher";
import { SidebarFavoritesList } from "./SidebarFavoritesList";

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

import { NotificationCard } from "../components/notifications/NotificationCard";
import { useNotificationActions } from "../components/notifications/useNotificationActions";
import {
  DELPI_CLOSE_APP_LAUNCHER_EVENT,
  DELPI_OPEN_APP_LAUNCHER_EVENT,
} from "../utils/appLauncher";
import { DELPI_SIDEBAR_EXPAND_EVENT, resolvePortalSidebarEdgeWidth } from "../utils/sidebar";
import {
  DELPI_PORTAL_TOUR_SIDEBAR_PANEL_EVENT,
  type PortalTourSidebarPanel,
} from "../tour/portalTourSidebar";
import { isLaunchableApp } from "../utils/launchableApps";
import { isLauncherAppContextActive } from "../components/appLauncherAppearance";

function sidebarFooterItemClass(options?: { active?: boolean; open?: boolean }) {
  return [
    "sidebar-footer-item",
    options?.active ? "active" : "",
    options?.open ? "is-open" : "",
  ]
    .filter(Boolean)
    .join(" ");
}

function isProfileFooterRoute(pathname: string) {
  return (
    pathname === "/profile" ||
    pathname.startsWith("/profile/") ||
    pathname === "/privacy"
  );
}

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
    reorderFavorites,
    markAllNotificationsRead,
    reloadNotifications,
  } = useContext(AuthContext);

  const { markNotificationRead, handleDelete, handleToggleImportant } = useNotificationActions();

  const navigate = useNavigate();
  const location = useLocation();
  const { theme, setTheme } = useTheme();

  const containerRef = useRef<HTMLDivElement>(null);
  const userDropdownRef = useRef<HTMLDivElement>(null);
  const notifDropdownRef = useRef<HTMLDivElement>(null);
  const notifTriggerRef = useRef<HTMLDivElement>(null);
  const themeDropdownRef = useRef<HTMLDivElement>(null);
  const themeTriggerRef = useRef<HTMLDivElement>(null);
  const userTriggerRef = useRef<HTMLDivElement>(null);

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
    document.documentElement.dataset.sidebarCollapsed = collapsed ? "true" : "false";
    document.documentElement.style.setProperty(
      "--portal-sidebar-width",
      collapsed
        ? "0px"
        : window.matchMedia("(max-width: 1024px)").matches
          ? "280px"
          : "300px",
    );
  }, [collapsed]);

  useEffect(() => {
    const openLauncher = () => setLauncherOpen(true);
    const closeLauncher = () => setLauncherOpen(false);
    window.addEventListener(DELPI_OPEN_APP_LAUNCHER_EVENT, openLauncher);
    window.addEventListener(DELPI_CLOSE_APP_LAUNCHER_EVENT, closeLauncher);
    return () => {
      window.removeEventListener(DELPI_OPEN_APP_LAUNCHER_EVENT, openLauncher);
      window.removeEventListener(DELPI_CLOSE_APP_LAUNCHER_EVENT, closeLauncher);
    };
  }, []);

  useEffect(() => {
    const onTourPanel = (event: Event) => {
      const panel = (event as CustomEvent<{ panel?: PortalTourSidebarPanel }>)
        .detail?.panel;

      if (
        panel === "notifications" ||
        panel === "theme" ||
        panel === "profile"
      ) {
        setLauncherOpen(false);
      }

      setNotifOpen(panel === "notifications");
      setThemeOpen(panel === "theme");
      setUserOpen(panel === "profile");

      if (panel === "none" || !panel) {
        setNotifOpen(false);
        setThemeOpen(false);
        setUserOpen(false);
      }
    };

    window.addEventListener(DELPI_PORTAL_TOUR_SIDEBAR_PANEL_EVENT, onTourPanel);
    return () =>
      window.removeEventListener(
        DELPI_PORTAL_TOUR_SIDEBAR_PANEL_EVENT,
        onTourPanel,
      );
  }, []);

  const openSidebarFromEdge = useCallback(() => {
    setCollapsed(false);
    setShowEdgeExpand(false);
  }, []);

  useEffect(() => {
    const expandFromPlugin = () => openSidebarFromEdge();
    window.addEventListener(DELPI_SIDEBAR_EXPAND_EVENT, expandFromPlugin);
    return () => window.removeEventListener(DELPI_SIDEBAR_EXPAND_EVENT, expandFromPlugin);
  }, [openSidebarFromEdge]);

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

      const edgeWidth = resolvePortalSidebarEdgeWidth();

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

      if (touch.clientX <= resolvePortalSidebarEdgeWidth()) {
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

  // Fecha dropdown ao clicar fora (mantém aberto ao clicar no gatilho — o toggle trata)
  useEffect(() => {
    const containsNode = (root: HTMLElement | null, target: Node) =>
      Boolean(root?.contains(target));

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;

      if (
        themeOpen &&
        !containsNode(themeDropdownRef.current, target) &&
        !containsNode(themeTriggerRef.current, target)
      ) {
        setThemeOpen(false);
      }

      if (
        notifOpen &&
        !containsNode(notifDropdownRef.current, target) &&
        !containsNode(notifTriggerRef.current, target)
      ) {
        setNotifOpen(false);
      }

      if (
        userOpen &&
        !containsNode(userDropdownRef.current, target) &&
        !containsNode(userTriggerRef.current, target)
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

  useEffect(() => {
    const normalize = (path: string) => path.replace(/\/+$/, "") || "/";
    const currentPath = normalize(location.pathname);

    setOpenApps((prev) => {
      let changed = false;
      const next = { ...prev };

      for (const [appId, group] of pinnedGroupedEntries) {
        const visibleRoutes = group.routes.filter(
          (route: { showInMenu?: boolean }) => route.showInMenu !== false,
        );
        const catalogApp = apps.find((app) => app.id === appId);
        const isActiveApp = isLauncherAppContextActive(currentPath, {
          routes: visibleRoutes,
          basePath: catalogApp?.basePath ?? null,
        });

        if (visibleRoutes.length <= 1) {
          if (next[appId]) {
            delete next[appId];
            changed = true;
          }
          continue;
        }

        if (isActiveApp) {
          if (!next[appId]) {
            changed = true;
          }
          next[appId] = true;
        } else if (next[appId]) {
          delete next[appId];
          changed = true;
        }
      }

      return changed ? next : prev;
    });
  }, [location.pathname, pinnedGroupedEntries, apps]);

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
      {!collapsed ? (
        <button
          type="button"
          className="sidebar-mobile-backdrop"
          aria-label="Fechar menu lateral"
          onClick={() => setCollapsed(true)}
        />
      ) : null}

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
                id="sidebar-logo"
                role="button"
                tabIndex={0}
                className="sidebar-logo"
                data-tour="sidebar-logo"
                onClick={() => navigate("/")}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    navigate("/");
                  }
                }}
                aria-label="Ir para a página inicial"
              >
                <img src="/logoMinhaDelpi.svg" alt="" draggable={false} />
              </div>

              <button
                className="collapse-btn"
                onClick={() => setCollapsed(true)}
                type="button"
              >
                <ChevronLeft size={18} />
              </button>
            </div>

            <div className="sidebar-content" data-tour="sidebar-favorites">
              <SidebarFavoritesList
                entries={pinnedGroupedEntries}
                favorites={favorites}
                apps={apps}
                openApps={openApps}
                onToggleOpen={(id) =>
                  setOpenApps((prev) => ({
                    ...prev,
                    [id]: !prev[id],
                  }))
                }
                onNavigate={(path) => navigate(path)}
                onReorder={reorderFavorites}
              />
            </div>

            <div className="sidebar-footer">
              {canAccessAdmin && (
                <NavLink
                  to="/admin"
                  className={({ isActive }) =>
                    sidebarFooterItemClass({ active: isActive })
                  }
                  data-tour="sidebar-admin"
                >
                  <Shield size={18} />
                  <span>Admin</span>
                </NavLink>
              )}

              <div
                className={sidebarFooterItemClass({
                  active: location.pathname.startsWith("/notifications"),
                  open: notifOpen,
                })}
                data-tour="sidebar-notifications"
                ref={notifTriggerRef}
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
                  data-tour="sidebar-notifications-panel"
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
                className={sidebarFooterItemClass({ open: launcherOpen })}
                data-tour="sidebar-apps"
                onClick={() => setLauncherOpen(true)}
              >
                <Grid size={18} />
                <span>Apps</span>
              </div>

              <div
                className={sidebarFooterItemClass({ open: themeOpen })}
                data-tour="sidebar-theme"
                ref={themeTriggerRef}
                onClick={() => setThemeOpen((open) => !open)}
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
                  data-tour="sidebar-theme-menu"
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
                className={sidebarFooterItemClass({
                  active: isProfileFooterRoute(location.pathname),
                  open: userOpen,
                })}
                data-tour="sidebar-profile"
                ref={userTriggerRef}
                onClick={() => setUserOpen((open) => !open)}
              >
                <div className="avatar small">{initials}</div>
                <span>{user?.name}</span>
                <ChevronDown size={16} />
              </div>

              {userOpen && (
                <div
                  className="dropdown sidebar-user"
                  data-tour="sidebar-profile-menu"
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
                className={({ isActive }) =>
                  `sidebar-footer__privacy-link${isActive ? " active" : ""}`
                }
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
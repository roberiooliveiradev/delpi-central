import "./Sidebar.css";
import {
  useContext,
  useMemo,
  useState,
  useEffect,
  useRef,
  useCallback,
  type CSSProperties,
} from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import { useTheme } from "../hooks/useTheme";
import { AppLauncher } from "../components/AppLauncher";
import { SidebarFavoritesList } from "./SidebarFavoritesList";
import { usePortalMobileChrome } from "../hooks/usePortalMobileChrome";

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
import { DELPI_SIDEBAR_EXPAND_EVENT, isPortalSidebarEdgeHoldPoint, PORTAL_SIDEBAR_EDGE_AUTO_HIDE_MS, PORTAL_SIDEBAR_EDGE_HOLD_MS, resolvePortalSidebarEdgeHoldWidth, resolvePortalSidebarEdgeWidth } from "../utils/sidebar";
import {
  DELPI_PORTAL_TOUR_SIDEBAR_PANEL_EVENT,
  type PortalTourSidebarPanel,
} from "../tour/portalTourSidebar";
import { isLaunchableApp } from "../utils/launchableApps";
import { isLauncherAppContextActive } from "../components/appLauncherAppearance";
import { useSidebarMobileSwipeOpen } from "./useSidebarMobileSwipeOpen";

const SIDEBAR_EDGE_LABEL_DESKTOP = "Abrir menu lateral";
const SIDEBAR_EDGE_LABEL_MOBILE = "Abrir menu";

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
  const expandControlRef = useRef<HTMLButtonElement>(null);
  const userDropdownRef = useRef<HTMLDivElement>(null);
  const notifDropdownRef = useRef<HTMLDivElement>(null);
  const notifTriggerRef = useRef<HTMLDivElement>(null);
  const themeDropdownRef = useRef<HTMLDivElement>(null);
  const themeTriggerRef = useRef<HTMLDivElement>(null);
  const userTriggerRef = useRef<HTMLDivElement>(null);
  const edgeAutoHideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const edgeHoldTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const edgeHoldPointerRef = useRef<{
    pointerId: number;
    startX: number;
    startY: number;
  } | null>(null);

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
  const { isNarrowViewport, isLandscapeMobile } = usePortalMobileChrome();

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
    if (edgeAutoHideTimerRef.current) {
      clearTimeout(edgeAutoHideTimerRef.current);
      edgeAutoHideTimerRef.current = null;
    }
    setCollapsed(false);
    setShowEdgeExpand(false);
  }, []);

  const clearEdgeAutoHideTimer = useCallback(() => {
    if (edgeAutoHideTimerRef.current) {
      clearTimeout(edgeAutoHideTimerRef.current);
      edgeAutoHideTimerRef.current = null;
    }
  }, []);

  const scheduleEdgeAutoHide = useCallback(() => {
    clearEdgeAutoHideTimer();
    edgeAutoHideTimerRef.current = setTimeout(() => {
      setShowEdgeExpand(false);
      edgeAutoHideTimerRef.current = null;
    }, PORTAL_SIDEBAR_EDGE_AUTO_HIDE_MS);
  }, [clearEdgeAutoHideTimer]);

  const clearEdgeHold = useCallback(() => {
    if (edgeHoldTimerRef.current) {
      clearTimeout(edgeHoldTimerRef.current);
      edgeHoldTimerRef.current = null;
    }
    edgeHoldPointerRef.current = null;
  }, []);

  const {
    swipeOffsetPx,
    isSwipeDragging,
    swipeBackdropOpacity,
  } = useSidebarMobileSwipeOpen({
    enabled: collapsed && isNarrowViewport && !isLandscapeMobile,
    sidebarRef: containerRef,
    onOpen: openSidebarFromEdge,
    onSwipeStart: clearEdgeHold,
  });

  useEffect(() => {
    const expandFromPlugin = () => openSidebarFromEdge();
    window.addEventListener(DELPI_SIDEBAR_EXPAND_EVENT, expandFromPlugin);
    return () => window.removeEventListener(DELPI_SIDEBAR_EXPAND_EVENT, expandFromPlugin);
  }, [openSidebarFromEdge]);

  const hideEdgeExpand = useCallback(() => {
    clearEdgeAutoHideTimer();
    setShowEdgeExpand(false);
  }, [clearEdgeAutoHideTimer]);

  const showEdgeExpandHint = useCallback(() => {
    if (!collapsed) return;
    setShowEdgeExpand(true);
    if (isNarrowViewport) {
      scheduleEdgeAutoHide();
    }
  }, [collapsed, isNarrowViewport, scheduleEdgeAutoHide]);

  const handleEdgePointerMove = useCallback(
    (event: PointerEvent) => {
      if (!collapsed || isNarrowViewport) {
        if (!collapsed) {
          setShowEdgeExpand(false);
        }
        return;
      }

      const edgeWidth = resolvePortalSidebarEdgeWidth();

      if (event.clientX <= edgeWidth) {
        setShowEdgeExpand(true);
        return;
      }

      const control = expandControlRef.current;
      if (control) {
        const rects = [
          control.getBoundingClientRect(),
        ].filter((rect): rect is DOMRect => rect != null);

        const withinControl = rects.some(
          (rect) =>
            event.clientX >= rect.left &&
            event.clientX <= rect.right &&
            event.clientY >= rect.top &&
            event.clientY <= rect.bottom,
        );

        if (withinControl) {
          setShowEdgeExpand(true);
          return;
        }
      }

      setShowEdgeExpand(false);
    },
    [collapsed, isNarrowViewport],
  );

  const handleEdgeTouchStart = useCallback(
    (event: TouchEvent) => {
      if (!collapsed || isNarrowViewport) return;

      const touch = event.touches[0];
      if (!touch) return;

      if (touch.clientX <= resolvePortalSidebarEdgeWidth()) {
        showEdgeExpandHint();
      }
    },
    [collapsed, showEdgeExpandHint, isNarrowViewport],
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

  useEffect(() => {
    if (!collapsed || !isNarrowViewport || isLandscapeMobile) {
      clearEdgeHold();
      return;
    }

    const EDGE_HOLD_MOVE_CANCEL_PX = 12;

    const onPointerDown = (event: PointerEvent) => {
      if (event.pointerType === "mouse" && event.button !== 0) return;
      if (!isPortalSidebarEdgeHoldPoint(event.clientX, event.clientY)) return;

      clearEdgeHold();
      edgeHoldPointerRef.current = {
        pointerId: event.pointerId,
        startX: event.clientX,
        startY: event.clientY,
      };

      edgeHoldTimerRef.current = setTimeout(() => {
        edgeHoldTimerRef.current = null;
        setShowEdgeExpand(true);
        scheduleEdgeAutoHide();
        if (typeof navigator !== "undefined" && "vibrate" in navigator) {
          navigator.vibrate(12);
        }
      }, PORTAL_SIDEBAR_EDGE_HOLD_MS);
    };

    const onPointerMove = (event: PointerEvent) => {
      const hold = edgeHoldPointerRef.current;
      if (!hold || hold.pointerId !== event.pointerId) return;

      const edgeWidth = resolvePortalSidebarEdgeHoldWidth();
      if (event.clientX > edgeWidth + EDGE_HOLD_MOVE_CANCEL_PX) {
        clearEdgeHold();
      }
    };

    const onPointerEnd = (event: PointerEvent) => {
      const hold = edgeHoldPointerRef.current;
      if (!hold || hold.pointerId !== event.pointerId) return;
      clearEdgeHold();
    };

    const onContextMenu = (event: MouseEvent) => {
      if (isPortalSidebarEdgeHoldPoint(event.clientX, event.clientY)) {
        event.preventDefault();
      }
    };

    window.addEventListener("pointerdown", onPointerDown, { passive: true });
    window.addEventListener("pointermove", onPointerMove, { passive: true });
    window.addEventListener("pointerup", onPointerEnd, { passive: true });
    window.addEventListener("pointercancel", onPointerEnd, { passive: true });
    window.addEventListener("contextmenu", onContextMenu);

    return () => {
      clearEdgeHold();
      window.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerEnd);
      window.removeEventListener("pointercancel", onPointerEnd);
      window.removeEventListener("contextmenu", onContextMenu);
    };
  }, [
    collapsed,
    isNarrowViewport,
    isLandscapeMobile,
    clearEdgeHold,
    scheduleEdgeAutoHide,
  ]);

  useEffect(() => {
    return () => {
      clearEdgeAutoHideTimer();
      clearEdgeHold();
    };
  }, [clearEdgeAutoHideTimer, clearEdgeHold]);

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

      {collapsed && swipeOffsetPx > 0 ? (
        <div
          className="sidebar-mobile-backdrop sidebar-mobile-backdrop--swipe-preview"
          style={{ opacity: swipeBackdropOpacity }}
          aria-hidden="true"
        />
      ) : null}

      {collapsed ? (
        <button
          ref={expandControlRef}
          type="button"
          className={`sidebar-edge-hotspot ${showEdgeExpand ? "is-visible" : ""}`}
          aria-label="Expandir menu lateral"
          onClick={openSidebarFromEdge}
          onMouseEnter={isNarrowViewport ? undefined : showEdgeExpandHint}
          onTouchStart={isNarrowViewport ? undefined : showEdgeExpandHint}
          onFocus={showEdgeExpandHint}
        >
          <ChevronRight
            className="sidebar-edge-hotspot__icon"
            size={16}
            strokeWidth={2.25}
            aria-hidden="true"
          />
          <span className="sidebar-edge-hotspot__label" aria-hidden="true">
            {isNarrowViewport ? SIDEBAR_EDGE_LABEL_MOBILE : SIDEBAR_EDGE_LABEL_DESKTOP}
          </span>
        </button>
      ) : null}

      <div
        id="portal-sidebar"
        className={[
          "sidebar",
          collapsed ? "collapsed" : "",
          isSwipeDragging ? "is-swipe-dragging" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        ref={containerRef}
        style={
          swipeOffsetPx > 0
            ? ({
                "--portal-sidebar-swipe-offset": `${swipeOffsetPx}px`,
              } as CSSProperties)
            : undefined
        }
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
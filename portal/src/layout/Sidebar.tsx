// src/layout/Sidebar.tsx

import "./Sidebar.css"
import {
  useContext,
  useMemo,
  useState,
  useEffect,
  useRef,
} from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import { useTheme } from "../hooks/useTheme";
import { AppLauncher } from "../components/AppLauncher";
import { resolveIcon } from "../utils/iconResolver";

import {
  Package,
  PanelLeftClose,
  PanelLeftOpen,
  Bell,
  Sun,
  Moon,
  Grid,
  Shield,
  ChevronDown,
  ChevronUp,
} from "lucide-react";


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
    markNotificationRead,
    markAllNotificationsRead,
  } = useContext(AuthContext);

  const location = useLocation();
  const navigate = useNavigate();
  const { theme, setTheme } = useTheme();

  const containerRef = useRef<HTMLDivElement>(null);
  const userDropdownRef = useRef<HTMLDivElement>(null);
  const notifDropdownRef = useRef<HTMLDivElement>(null);

  /* ===============================
     ESTADO
  =============================== */

  const [collapsed, setCollapsed] = useState(() => {
    return localStorage.getItem("sidebar-collapsed") === "true";
  });

  const [openApps, setOpenApps] = useState<Record<string, boolean>>({});
  const [userOpen, setUserOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [launcherOpen, setLauncherOpen] = useState(false);

  useEffect(() => {
    localStorage.setItem("sidebar-collapsed", String(collapsed));
  }, [collapsed]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;

      if (
        userOpen &&
        userDropdownRef.current &&
        !userDropdownRef.current.contains(target)
      ) {
        setUserOpen(false);
      }

      if (
        notifOpen &&
        notifDropdownRef.current &&
        !notifDropdownRef.current.contains(target)
      ) {
        setNotifOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [userOpen, notifOpen]);

  /* ===============================
     AGRUPAMENTO DE ROTAS
  =============================== */

  const grouped: GroupedRoutes = useMemo(() => {
    const map: GroupedRoutes = {};

    // 1️⃣ Cria todos os apps primeiro
    apps?.forEach((app: any) => {
      map[app.id] = {
        appName: app.name,
        appIcon: app.icon ?? null,
        routes: [],
      };
    });

    // 2️⃣ Adiciona apenas rotas visíveis
    routes.forEach((route: any) => {
      if (!map[route.app]) return;

      map[route.app].routes.push(route);
    });

    return map;
  }, [apps, routes]);

  const toggleApp = (appId: string) => {
    setOpenApps((prev) => ({
      ...prev,
      [appId]: !prev[appId],
    }));
  };

  /* ===============================
     DADOS GLOBAIS
  =============================== */

  const unreadCount = notifications.filter((n) => !n.read).length;

  const initials = (() => {
    if (!user?.name) return "?";

    const parts = user.name.trim().split(" ").filter(Boolean);

    const first = parts[0]?.[0] ?? "";
    const last = parts.length > 1 ? parts[parts.length - 1][0] : "";

    return (first + last).toUpperCase() || "?";
  })();

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark");
  };

  /* ========================================
     RENDER
  ======================================== */

  return (
    <>
      {collapsed && (
        <button
          className="sidebar-expand-btn"
          onClick={() => setCollapsed(false)}
        >
          <PanelLeftOpen size={18} />
        </button>
      )}

      <div
        className={`sidebar ${collapsed ? "collapsed" : ""}`}
        ref={containerRef}
      >
        {!collapsed && (
          <>
            {/* ================= HEADER ================= */}
            <div className="sidebar-header">
              <div
                className="sidebar-logo"
                onClick={() => navigate("/")}
                style={{ cursor: "pointer" }}
              >
                <img
                  src="/logoTransformaMaisDelpi.svg"
                  alt="Transforma mais DELPI"
                />
              </div>

              <button
                className="collapse-btn"
                onClick={() => setCollapsed(true)}
              >
                <PanelLeftClose size={18} />
              </button>
            </div>

            {/* ================= APPS ================= */}
            <div className="sidebar-content">
              {Object.entries(grouped).map(([appId, group]) => {
                const isOpen = openApps[appId] ?? false;
                const AppIcon =
                  resolveIcon(group.appIcon) || Package;

                return (
                  <div key={appId} className="sidebar-app">
                    <div
                      className="sidebar-app-title"
                      onClick={() => {
                        if (group.routes.length === 0) {
                          navigate("/");
                          return;
                        }

                        toggleApp(appId);
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 8,
                        }}
                      >
                        <AppIcon size={16} />
                        <span>{group.appName}</span>
                      </div>

                      {isOpen ? (
                        <ChevronDown size={16} />
                      ) : (
                        <ChevronUp size={16} />
                      )}
                    </div>

                    {isOpen &&
                      group.routes.map((route) => {
                        const label =
                          route.label ||
                          route.path
                            .split("/")
                            .filter(Boolean)
                            .pop()
                            ?.replace(/-/g, " ")
                            .replace(/\b\w/g, (c: string) =>
                              c.toUpperCase()
                            ) ||
                          route.path;

                        const Icon =
                          resolveIcon(route.icon) || Package;

                        const isActive =
                          location.pathname === route.path;

                        return (
                          <NavLink
                            key={route.path}
                            to={route.path}
                            className={`sidebar-link ${
                              isActive ? "active" : ""
                            }`}
                          >
                            <Icon size={18} />
                            <span>{label}</span>
                          </NavLink>
                        );
                      })}
                  </div>
                );
              })}
            </div>

            {/* ================= FOOTER ================= */}
            <div className="sidebar-footer">
              {user?.is_superadmin && (
                <NavLink
                  to="/admin"
                  className="sidebar-footer-item"
                >
                  <Shield size={18} />
                  <span>Admin</span>
                </NavLink>
              )}

              <div
                className="sidebar-footer-item"
                onClick={() => setNotifOpen(!notifOpen)}
              >
                <Bell size={18} />
                <span>Notificações</span>
                {unreadCount > 0 && (
                  <span className="notif-badge">
                    {unreadCount}
                  </span>
                )}
              </div>

              {notifOpen && (
                <div
                  className="notif-dropdown sidebar-notif"
                  ref={notifDropdownRef}
                >
                  {notifications.length === 0 && (
                    <div className="notif-item">
                      Sem notificações
                    </div>
                  )}

                  {notifications.length > 0 && (
                    <div
                      className="notif-item mark-all"
                      onClick={markAllNotificationsRead}
                    >
                      Marcar todas como lidas
                    </div>
                  )}

                  {notifications.map((n) => (
                    <div
                      key={n.id}
                      className={`notif-item ${
                        !n.read ? "unread" : ""
                      }`}
                      onClick={() =>
                        markNotificationRead(n.id)
                      }
                    >
                      {n.message}
                    </div>
                  ))}
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
                onClick={toggleTheme}
              >
                {theme === "dark" ? (
                  <Sun size={18} />
                ) : (
                  <Moon size={18} />
                )}
                <span>Tema</span>
              </div>

              <div
                className="sidebar-footer-item"
                onClick={() => setUserOpen(!userOpen)}
              >
                <div className="avatar small">
                  {initials}
                </div>
                <span>{user?.name}</span>
                <ChevronDown size={16} />
              </div>

              {userOpen && (
                <div
                  className="dropdown sidebar-user"
                  ref={userDropdownRef}
                >
                  <div className="dropdown-item">
                    Meu Perfil
                  </div>
                  <div className="dropdown-item">
                    Configurações
                  </div>
                  <div
                    className="dropdown-item danger"
                    onClick={logout}
                  >
                    Logout
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {launcherOpen && (
        <AppLauncher
          onClose={() => setLauncherOpen(false)}
        />
      )}
    </>
  );
};
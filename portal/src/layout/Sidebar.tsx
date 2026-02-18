// src/layout/Sidebar.tsx

import {
  useContext,
  useMemo,
  useState,
  useEffect,
  useRef
} from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import { useTheme } from "../hooks/useTheme";
import { AppLauncher } from "../components/AppLauncher";

import {
  LayoutDashboard,
  Users,
  Package,
  PanelLeftClose,
  PanelLeftOpen,
  Bell,
  Sun,
  Moon,
  Grid,
  Shield,
  ChevronDown,
  ChevronUp
} from "lucide-react";

type IconType = React.ComponentType<{ size?: number }>;

/* ========================================
   MAPEAMENTO DE ÍCONES
======================================== */

const iconMap: Record<string, IconType> = {
  dashboard: LayoutDashboard,
  leads: Users,
  default: Package,
};

/* ========================================
   COMPONENTE
======================================== */

export const Sidebar = () => {
  const { routes, user, logout, notifications, markNotificationRead, markAllNotificationsRead } =
    useContext(AuthContext);

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

      // Fecha dropdown usuário
      if (
        userOpen &&
        userDropdownRef.current &&
        !userDropdownRef.current.contains(target)
      ) {
        setUserOpen(false);
      }

      // Fecha notificações
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

  const grouped = useMemo(() => {
    const map: Record<string, typeof routes> = {};
    routes.forEach((route) => {
      if (!map[route.app]) map[route.app] = [];
      map[route.app].push(route);
    });
    return map;
  }, [routes]);

  const toggleApp = (app: string) => {
    setOpenApps((prev) => ({
      ...prev,
      [app]: !prev[app],
    }));
  };

  /* ===============================
     DADOS GLOBAIS
  =============================== */

  const unreadCount = notifications.filter((n) => !n.read).length;

  const initials =
    user?.name
      ?.split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase() || "?";

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark");
  };

  /* ========================================
     RENDER
  ======================================== */

  return (
    <>
      {/* Botão flutuante quando colapsada */}
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
              {Object.entries(grouped).map(([app, appRoutes]) => {
                const isOpen = openApps[app] ?? true;

                return (
                  <div key={app} className="sidebar-app">
                    <div
                      className="sidebar-app-title"
                      onClick={() => toggleApp(app)}
                    >
                      {app} {isOpen ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
                    </div>

                    {isOpen &&
                      appRoutes.map((route) => {
                        const rawLabel =
                          route.path.split("/").filter(Boolean).pop() ?? "";

                        const label = rawLabel
                          .replace(/-/g, " ")
                          .replace(/\b\w/g, (c) => c.toUpperCase());

                        const Icon =
                          iconMap[rawLabel.toLowerCase()] ||
                          iconMap.default;

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
              {/* Admin */}
              {user?.is_superadmin && (
                <NavLink
                  to="/admin"
                  className="sidebar-footer-item"
                >
                  <Shield size={18} />
                  <span>Admin</span>
                </NavLink>
              )}

              {/* Notificações */}
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

              {/* Launcher */}
              <div
                className="sidebar-footer-item"
                onClick={() => setLauncherOpen(true)}
              >
                <Grid size={18} />
                <span>Apps</span>
              </div>

              {/* Tema */}
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

              {/* Usuário */}
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

      {/* ================= MODAL APPS ================= */}
      {launcherOpen && (
        <AppLauncher
          onClose={() => setLauncherOpen(false)}
        />
      )}
    </>
  );
};

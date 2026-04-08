// src/layout/Sidebar.tsx

import "./Sidebar.css";
import {
  useContext,
  useMemo,
  useState,
  useEffect,
  useRef,
} from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import { useTheme } from "../hooks/useTheme";
import { AppLauncher } from "../components/AppLauncher";

import {
  PanelLeftClose,
  PanelLeftOpen,
  Bell,
  Sun,
  Moon,
  Grid,
  Shield,
  ChevronDown,
  CircleDashed,
  User,
  LogOut,
} from "lucide-react";

import { AppLauncherCard } from "../components/AppLauncherCard";

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
    markNotificationRead,
    markAllNotificationsRead,
  } = useContext(AuthContext);

  // const location = useLocation();
  const navigate = useNavigate();
  const { theme, setTheme } = useTheme();

  const containerRef = useRef<HTMLDivElement>(null);
  const userDropdownRef = useRef<HTMLDivElement>(null);
  const notifDropdownRef = useRef<HTMLDivElement>(null);

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
  const themeDropdownRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    localStorage.setItem("sidebar-collapsed", String(collapsed));
  }, [collapsed]);

  // 🔹 Fecha dropdown ao clicar fora
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

  // 🔹 Apenas apps pinados, mantendo ordem do pin
  const pinnedGroupedEntries = useMemo(() => {
    if (!favorites?.length) return [];

    return favorites
      .map((fav) => [fav.id, grouped[fav.id]] as const)
      .filter(([, group]) => !!group);
  }, [favorites, grouped]);

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
    user?.is_superadmin ||
    user?.permissions?.includes("rbac.manage");  


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
                  src="/logoMinhaDelpi.svg"
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

            {/* ================= APPS PINADOS ================= */}
            <div className="sidebar-content">
              {pinnedGroupedEntries.map(([appId, group]) => {
                const isOpen = openApps[appId] ?? false;

                return (
                  <AppLauncherCard
                    key={appId}
                    variant="sidebar"
                    app={{
                      id: appId,
                      name: group.appName,
                      icon: group.appIcon,
                    }}
                    routes={group.routes}
                    isOpen={isOpen}
                    onToggleOpen={(id) =>
                      setOpenApps((prev) => ({
                        ...prev,
                        [id]: !prev[id],
                      }))
                    }
                    onOpenSingle={() => navigate("/")}
                    onGoToRoute={(path) => navigate(path)}
                  />
                );
              })}
            </div>

            {/* ================= FOOTER ================= */}
            <div className="sidebar-footer">
            {canAccessAdmin && (
              <NavLink to="/admin" className="sidebar-footer-item">
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
                <div
                  className="dropdown-item"
                  onClick={() => {
                    navigate("/profile");
                    setUserOpen(false);
                  }}
                >
                  <User size={16}/>
                  Meu Perfil
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
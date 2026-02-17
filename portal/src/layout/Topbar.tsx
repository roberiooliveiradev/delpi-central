// src/layout/Topbar.tsx

import { useContext, useState, useRef, useEffect, useMemo } from "react";
import { useLocation } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import { useTheme } from "../hooks/useTheme";
import { AppLauncher } from "../components/AppLauncher";

import {
  ChevronDown,
  Bell,
  Sun,
  Moon,
  Grid,
} from "lucide-react";

export const Topbar = () => {
  const { user, logout, notifications } = useContext(AuthContext);
  const location = useLocation();
  const { theme, setTheme } = useTheme();

  const [userOpen, setUserOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [launcherOpen, setLauncherOpen] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);

  // Breadcrumb
  const breadcrumb = useMemo(() => {
    const parts = location.pathname
      .split("/")
      .filter(Boolean)
      .map((p) => p.charAt(0).toUpperCase() + p.slice(1));

    return parts.length > 0 ? parts.join(" / ") : "Home";
  }, [location.pathname]);

  // Inicial do usuário
  const initials = useMemo(() => {
    return (
      user?.name
        ?.split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase() || "?"
    );
  }, [user?.name]);

  // Contador de não lidas
  const unreadCount = useMemo(() => {
    return notifications.filter((n) => !n.read).length;
  }, [notifications]);

  // Fechar dropdowns ao clicar fora
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setUserOpen(false);
        setNotifOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () =>
      document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark");
  };

  return (
    <>
      <div className="topbar">
        {/* Breadcrumb */}
        <div className="breadcrumb">{breadcrumb}</div>

        <div className="topbar-actions" ref={containerRef}>
          {/* Notificações */}
          <div className="notification-wrapper">
            <button
              className="icon-button"
              onClick={() => {
                setNotifOpen((prev) => !prev);
                setUserOpen(false);
              }}
            >
              <Bell size={18} />
              {unreadCount > 0 && (
                <span className="notif-badge">{unreadCount}</span>
              )}
            </button>

            {notifOpen && (
              <div className="notif-dropdown">
                {notifications.length === 0 && (
                  <div className="notif-item">
                    Sem notificações
                  </div>
                )}

                {notifications.map((n) => (
                  <div
                    key={n.id}
                    className={`notif-item ${
                      !n.read ? "unread" : ""
                    }`}
                  >
                    {n.message}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* App Launcher */}
          <button
            className="icon-button"
            onClick={() => setLauncherOpen(true)}
          >
            <Grid size={18} />
          </button>

          {/* Toggle Tema */}
          <button
            className="icon-button"
            onClick={toggleTheme}
          >
            {theme === "dark" ? (
              <Sun size={18} />
            ) : (
              <Moon size={18} />
            )}
          </button>

          {/* Usuário */}
          <div
            className="user-trigger"
            onClick={() => {
              setUserOpen((prev) => !prev);
              setNotifOpen(false);
            }}
          >
            <div className="avatar">{initials}</div>
            <span className="user-name">{user?.name}</span>
            <ChevronDown size={16} />
          </div>

          {userOpen && (
            <div className="dropdown">
              <div className="dropdown-item">Meu Perfil</div>
              <div className="dropdown-item">Configurações</div>
              <div
                className="dropdown-item danger"
                onClick={logout}
              >
                Logout
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Modal Launcher */}
      {launcherOpen && (
        <AppLauncher onClose={() => setLauncherOpen(false)} />
      )}
    </>
  );
};

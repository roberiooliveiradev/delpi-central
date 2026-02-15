// src/layout/Topbar.tsx

import { useContext, useState, useRef, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import { ChevronDown } from "lucide-react";

import { Sun, Moon } from "lucide-react";
import { useTheme } from "../hooks/useTheme";

import { Grid } from "lucide-react";
import { AppLauncher } from "../components/AppLauncher";

export const Topbar = () => {
  const { user, logout } = useContext(AuthContext);
  const location = useLocation();

  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const { theme, setTheme } = useTheme();

  const toggleTheme = () => {
    if (theme === "dark") setTheme("light");
    else setTheme("dark");
  };

  const [launcherOpen, setLauncherOpen] = useState(false);

  const parts = location.pathname
    .split("/")
    .filter(Boolean)
    .map((p) => p.charAt(0).toUpperCase() + p.slice(1));

  // Fechar dropdown ao clicar fora
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const initials =
    user?.name
      ?.split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase() || "?";

  return (
    <div className="topbar">
      <div>{parts.join(" / ") || "Home"}</div>


      <div className="user-section" ref={dropdownRef}>
        <button
          className="theme-toggle"
          onClick={() => setLauncherOpen(true)}
        >
          <Grid size={18} />
        </button>

        <button
          onClick={toggleTheme}
          className="theme-toggle"
        >
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>
        <div
          className="user-trigger"
          onClick={() => setOpen(!open)}
        >

          <div className="avatar">{initials}</div>
          <span>{user?.name}</span>
          <ChevronDown size={16} />
        </div>

        {open && (
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
      {launcherOpen && (
        <AppLauncher onClose={() => setLauncherOpen(false)} />
      )}
    </div>
  );
};

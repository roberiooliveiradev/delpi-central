import "./PortalMobileNavBar.css";

import { useEffect, useRef, useState } from "react";
import { LayoutGrid, Menu, Monitor, Moon, Sun } from "lucide-react";

import { usePortalMobileChrome } from "../hooks/usePortalMobileChrome";
import { useTheme, type Theme } from "../hooks/useTheme";
import { openAppLauncher } from "../utils/appLauncher";
import { expandPortalSidebar } from "../utils/sidebar";

const THEME_OPTIONS: Array<{ value: Theme; label: string; icon: typeof Sun }> = [
  { value: "light", label: "Claro", icon: Sun },
  { value: "dark", label: "Escuro", icon: Moon },
  { value: "system", label: "Sistema", icon: Monitor },
];

function ThemeTriggerIcon({ theme }: { theme: Theme }) {
  if (theme === "dark") return <Moon size={20} strokeWidth={2.1} aria-hidden="true" />;
  if (theme === "light") return <Sun size={20} strokeWidth={2.1} aria-hidden="true" />;
  return <Monitor size={20} strokeWidth={2.1} aria-hidden="true" />;
}

export function PortalMobileNavBar() {
  const { showMobileNav } = usePortalMobileChrome();
  const { theme, setTheme } = useTheme();
  const [themeOpen, setThemeOpen] = useState(false);
  const themeWrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!themeOpen) return;

    const onPointerDown = (event: PointerEvent) => {
      const target = event.target as Node;
      if (themeWrapRef.current?.contains(target)) return;
      setThemeOpen(false);
    };

    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [themeOpen]);

  if (!showMobileNav) return null;

  return (
    <nav
      className="portal-mobile-nav"
      aria-label="Navegação rápida do portal"
      data-portal-sidebar-swipe-ignore
    >
      <button
        type="button"
        className="portal-mobile-nav__button"
        aria-label="Abrir menu lateral"
        data-tour="portal-mobile-nav-menu"
        onClick={() => expandPortalSidebar()}
      >
        <Menu size={22} strokeWidth={2.15} aria-hidden="true" />
      </button>

      <button
        type="button"
        className="portal-mobile-nav__button"
        aria-label="Abrir aplicativos"
        data-tour="portal-mobile-nav-apps"
        onClick={() => openAppLauncher()}
      >
        <LayoutGrid size={20} strokeWidth={2.1} aria-hidden="true" />
      </button>

      <div className="portal-mobile-nav__theme-wrap" ref={themeWrapRef}>
        <button
          type="button"
          className={`portal-mobile-nav__button ${themeOpen ? "is-active" : ""}`}
          aria-label="Alterar tema"
          aria-expanded={themeOpen}
          data-tour="portal-mobile-nav-theme"
          onClick={() => setThemeOpen((open) => !open)}
        >
          <ThemeTriggerIcon theme={theme} />
        </button>

        {themeOpen ? (
          <div className="portal-mobile-nav__theme-menu" role="menu" aria-label="Tema">
            {THEME_OPTIONS.map((option) => {
              const Icon = option.icon;
              const isActive = theme === option.value;

              return (
                <button
                  key={option.value}
                  type="button"
                  role="menuitemradio"
                  aria-checked={isActive}
                  className={isActive ? "is-active" : ""}
                  onClick={() => {
                    setTheme(option.value);
                    setThemeOpen(false);
                  }}
                >
                  <Icon size={16} strokeWidth={2} aria-hidden="true" />
                  {option.label}
                </button>
              );
            })}
          </div>
        ) : null}
      </div>
    </nav>
  );
}

import { useEffect, useState, type ReactNode } from "react";
import { CONSOLE_BASE } from "../constants/routes";
import { isPortalSidebarCollapsed } from "../lib/portalShell";
import { PortalSidebarTrigger } from "./PortalSidebarTrigger";

type NavItem = {
  id: string;
  label: string;
  segment: string;
};

const NAV_ITEMS: NavItem[] = [
  { id: "home", label: "Início", segment: "" },
  { id: "documentacao", label: "Documentação", segment: "documentacao" },
  { id: "verificacoes", label: "Verificações", segment: "verificacoes" },
  { id: "explorer", label: "Explorador", segment: "explorer" },
  { id: "spec", label: "OpenAPI", segment: "spec" },
  { id: "history", label: "Histórico", segment: "history" },
];

type Props = {
  activeSegment: string;
  onNavigate: (segment: string) => void;
  children: ReactNode;
};

export function ConsoleShell({ activeSegment, onNavigate, children }: Props) {
  const [portalSidebarCollapsed, setPortalSidebarCollapsed] = useState(() =>
    isPortalSidebarCollapsed(),
  );

  useEffect(() => {
    const sync = () => setPortalSidebarCollapsed(isPortalSidebarCollapsed());
    sync();

    const observer = new MutationObserver(sync);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-sidebar-collapsed"],
    });

    window.addEventListener("resize", sync);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", sync);
    };
  }, []);

  return (
    <div className="api-delpi-console adc-app-shell">
      <PortalSidebarTrigger
        visible={portalSidebarCollapsed}
        onExpanded={() => setPortalSidebarCollapsed(false)}
      />

      <nav className="adc-nav" aria-label="Navegação do console">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={
              activeSegment === item.segment
                ? "adc-nav__item adc-nav__item--active"
                : "adc-nav__item"
            }
            onClick={() => onNavigate(item.segment)}
          >
            {item.label}
          </button>
        ))}
      </nav>
      <div className="adc-app-body">{children}</div>
    </div>
  );
}

export function segmentFromPathname(pathname: string): string {
  const normalized =
    pathname.length > 1 && pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;
  if (normalized === CONSOLE_BASE) return "";
  if (normalized.startsWith(`${CONSOLE_BASE}/`)) {
    return normalized.slice(CONSOLE_BASE.length + 1);
  }
  return "";
}

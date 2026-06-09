import { type ReactNode } from "react";
import { CONSOLE_BASE } from "../constants/routes";

type NavItem = {
  id: string;
  label: string;
  segment: string;
};

const NAV_ITEMS: NavItem[] = [
  { id: "home", label: "Início", segment: "" },
  { id: "documentacao", label: "Documentação", segment: "documentacao" },
  { id: "verificacoes", label: "Verificações", segment: "verificacoes" },
  { id: "sql", label: "SQL", segment: "sql" },
  { id: "cache", label: "Cache", segment: "cache" },
  { id: "alertas", label: "Alertas", segment: "alertas" },
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
  return (
    <div className="api-delpi-console adc-app-shell">
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

export function segmentFromPathname(pathname: string, basePath: string = CONSOLE_BASE): string {
  const base = basePath.replace(/\/+$/, "") || CONSOLE_BASE;
  const normalized =
    pathname.length > 1 && pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;
  if (normalized === base) return "";
  if (normalized.startsWith(`${base}/`)) {
    return normalized.slice(base.length + 1);
  }
  return "";
}

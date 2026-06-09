import type { ReactNode } from "react";
import { CONSOLE_BASE } from "../constants/routes";

type NavItem = {
  id: string;
  label: string;
  segment: string;
};

const NAV_ITEMS: NavItem[] = [
  { id: "home", label: "Início", segment: "" },
  { id: "swagger", label: "Swagger", segment: "swagger" },
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
    <div className="adc-root">
      <nav className="adc-nav">
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
      {children}
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

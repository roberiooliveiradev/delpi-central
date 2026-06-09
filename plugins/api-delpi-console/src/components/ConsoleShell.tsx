import { type ReactNode, useCallback, useState } from "react";
import { CONSOLE_BASE } from "../constants/routes";
import { MONITOR_REFRESH_MS } from "../constants/monitoring";
import { fetchConsoleHealth } from "../lib/consoleAlerts";
import { usePolling } from "../lib/usePolling";

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
  onNavigate: (
    segment: string,
    searchParams?: Record<string, string | null | undefined>,
  ) => void;
  children: ReactNode;
};

export function ConsoleShell({ activeSegment, onNavigate, children }: Props) {
  const [openAlertCount, setOpenAlertCount] = useState(0);

  const refreshAlertBadge = useCallback(async () => {
    const health = await fetchConsoleHealth();
    setOpenAlertCount(health?.open_alert_count ?? 0);
  }, []);

  usePolling(refreshAlertBadge, MONITOR_REFRESH_MS, { immediate: true });

  return (
    <div className="api-delpi-console adc-app-shell">
      <nav className="adc-nav" aria-label="Navegação do console">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={
              activeSegment === item.segment.split("?")[0]
                ? "adc-nav__item adc-nav__item--active"
                : "adc-nav__item"
            }
            onClick={() => onNavigate(item.segment)}
          >
            {item.label}
            {item.id === "alertas" && openAlertCount > 0 ? (
              <span className="adc-nav__badge" aria-label={`${openAlertCount} alertas`}>
                {openAlertCount}
              </span>
            ) : null}
          </button>
        ))}
      </nav>
      <div className="adc-app-body">{children}</div>
    </div>
  );
}

export function segmentFromPathname(pathname: string, basePath: string = CONSOLE_BASE): string {
  const base = basePath.replace(/\/+$/, "") || CONSOLE_BASE;
  const pathOnly = pathname.split("?")[0];
  const normalized =
    pathOnly.length > 1 && pathOnly.endsWith("/") ? pathOnly.slice(0, -1) : pathOnly;
  if (normalized === base) return "";
  if (normalized.startsWith(`${base}/`)) {
    return normalized.slice(base.length + 1);
  }
  return "";
}

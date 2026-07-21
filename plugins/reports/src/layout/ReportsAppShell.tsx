import { Menu, X } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";

import type { ReportsNavSection } from "../utils/route";
import { ReportsSidebar } from "./ReportsSidebar";

type Props = {
  nav: ReportsNavSection;
  children: ReactNode;
};

export function ReportsAppShell({ nav, children }: Props) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    setMobileOpen(false);
  }, [nav]);

  return (
    <div className="dashboard-reports dashboard-page dashboard-page--app-shell dashboard-reports--shell">
      <div
        className={[
          "rp-shell",
          collapsed ? "rp-shell--collapsed" : "",
          mobileOpen ? "rp-shell--mobile-open" : "",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        <div className="rp-shell__mobile-bar">
          <button
            type="button"
            className="rp-btn rp-btn--ghost"
            aria-expanded={mobileOpen}
            onClick={() => setMobileOpen((open) => !open)}
          >
            {mobileOpen ? <X size={16} aria-hidden /> : <Menu size={16} aria-hidden />}
            Menu
          </button>
        </div>

        {mobileOpen ? (
          <button
            type="button"
            className="rp-shell__backdrop"
            aria-label="Fechar menu"
            onClick={() => setMobileOpen(false)}
          />
        ) : null}

        <ReportsSidebar
          active={nav}
          collapsed={collapsed}
          mobileOpen={mobileOpen}
          onToggleCollapsed={() => setCollapsed((value) => !value)}
          onCloseMobile={() => setMobileOpen(false)}
        />

        <main className="rp-main">{children}</main>
      </div>
    </div>
  );
}

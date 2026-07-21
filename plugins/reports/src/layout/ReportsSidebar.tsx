import { FileText, LayoutDashboard, PanelLeftClose, PanelLeftOpen } from "lucide-react";

import {
  DELPI_LOGO_URL,
  REPORTS_BASE,
  REPORTS_LIST_PATH,
  type ReportsNavSection,
} from "../utils/route";

type Props = {
  active: ReportsNavSection;
  collapsed: boolean;
  mobileOpen: boolean;
  onToggleCollapsed: () => void;
  onCloseMobile: () => void;
};

const NAV_ITEMS: Array<{
  id: ReportsNavSection;
  label: string;
  href: string;
  icon: typeof LayoutDashboard;
}> = [
  {
    id: "overview",
    label: "Visão geral",
    href: REPORTS_BASE,
    icon: LayoutDashboard,
  },
  {
    id: "reports",
    label: "Relatórios",
    href: REPORTS_LIST_PATH,
    icon: FileText,
  },
];

export function ReportsSidebar({
  active,
  collapsed,
  mobileOpen,
  onToggleCollapsed,
  onCloseMobile,
}: Props) {
  return (
    <aside
      className={[
        "rp-sidebar",
        collapsed ? "rp-sidebar--collapsed" : "",
        mobileOpen ? "rp-sidebar--mobile-open" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      aria-label="Navegação Delpi Reports"
    >
      <div className="rp-sidebar__brand">
        <a className="rp-sidebar__brand-link" href={REPORTS_BASE} onClick={onCloseMobile}>
          <img
            className="rp-sidebar__logo"
            src={DELPI_LOGO_URL}
            alt="DELPI Conexões Elétricas"
          />
          {!collapsed ? (
            <span className="rp-sidebar__brand-text">
              <strong>Delpi Reports</strong>
              <em>Envio por e-mail</em>
            </span>
          ) : null}
        </a>
        <div className="rp-page-header__brand-bar" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
        </div>
      </div>

      <nav className="rp-sidebar__nav">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = active === item.id;
          return (
            <a
              key={item.id}
              href={item.href}
              className={[
                "rp-sidebar__link",
                isActive ? "rp-sidebar__link--active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              aria-current={isActive ? "page" : undefined}
              title={item.label}
              onClick={onCloseMobile}
            >
              <Icon size={18} aria-hidden />
              {!collapsed ? <span>{item.label}</span> : null}
            </a>
          );
        })}
      </nav>

      <div className="rp-sidebar__footer">
        <button
          type="button"
          className="rp-sidebar__collapse"
          onClick={onToggleCollapsed}
          aria-pressed={collapsed}
        >
          {collapsed ? (
            <PanelLeftOpen size={16} aria-hidden />
          ) : (
            <PanelLeftClose size={16} aria-hidden />
          )}
          {!collapsed ? <span>Recolher menu</span> : null}
        </button>
      </div>
    </aside>
  );
}

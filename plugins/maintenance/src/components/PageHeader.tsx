import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

import { MaintenanceNav } from "./MaintenanceNav";
import "./PageHeader.css";

type PageHeaderProps = {
  title: string;
  subtitle: string;
  icon: LucideIcon;
  eyebrow?: string;
  currentPath?: string;
  filialScope?: string;
  onNavigate: (path: string) => void;
  actions?: ReactNode;
  showNav?: boolean;
  compact?: boolean;
};

/** Header brand no mesmo estilo da home (shell + barra Delpi). */
export function PageHeader({
  title,
  subtitle,
  icon: Icon,
  eyebrow = "Delpi • Manutenção",
  filialScope,
  onNavigate,
  actions,
  showNav = true,
  compact = false,
}: PageHeaderProps) {
  return (
    <header
      className={["dm-home-header", compact ? "dm-home-header--compact" : null]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="dm-home-header__shell">
        <div className="dm-home-header__main">
          <div className="dm-home-header__brand">
            <span className="dm-home-header__icon" aria-hidden>
              <Icon size={28} strokeWidth={1.75} />
            </span>
            <div className="dm-home-header__titles">
              <p className="dm-home-header__eyebrow">{eyebrow}</p>
              <div className="dm-home-header__title-row">
                <h1>{title}</h1>
              </div>
              <p className="dm-home-header__subtitle">{subtitle}</p>
              {showNav ? (
                <div className="dm-home-header__nav">
                  <MaintenanceNav filialScope={filialScope} onNavigate={onNavigate} />
                </div>
              ) : null}
            </div>
          </div>
          {actions ? <div className="dm-home-header__actions">{actions}</div> : null}
        </div>
        <div className="dm-home-header__brand-bar" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
        </div>
      </div>
    </header>
  );
}

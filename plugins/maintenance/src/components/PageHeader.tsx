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
  onNavigate: (path: string) => void;
  actions?: ReactNode;
};

export function PageHeader({
  title,
  subtitle,
  icon: Icon,
  eyebrow = "DELPI • Manutenção",
  currentPath,
  onNavigate,
  actions,
}: PageHeaderProps) {
  return (
    <header className="dm-page-header">
      <div className="dm-page-header__brand">
        <div className="dm-header__icon" aria-hidden="true">
          <Icon size={28} strokeWidth={1.75} />
        </div>
        <div className="dm-page-header__content">
          <p className="dm-eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
          <span className="dm-page-subtitle">{subtitle}</span>
          <MaintenanceNav currentPath={currentPath} onNavigate={onNavigate} />
        </div>
      </div>
      {actions ? <div className="dm-header-actions">{actions}</div> : null}
    </header>
  );
}

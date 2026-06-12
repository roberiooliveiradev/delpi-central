import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

import { FilialBadge } from "./data/FilialBadge";
import { MiniAplicadoresNav } from "./MiniAplicadoresNav";
import "./PageHeader.css";

type MiniAplicadoresPageHeaderProps = {
  title: string;
  subtitle: string;
  icon: LucideIcon;
  filial: string;
  filialDisplayName?: string;
  moduleHomePath: string;
  showConfiguration?: boolean;
  currentPath?: string;
  onNavigate: (path: string) => void;
  actions?: ReactNode;
};

export function MiniAplicadoresPageHeader({
  title,
  subtitle,
  icon: Icon,
  filial,
  filialDisplayName,
  moduleHomePath,
  showConfiguration = false,
  currentPath,
  onNavigate,
  actions,
}: MiniAplicadoresPageHeaderProps) {
  return (
    <header className="dm-page-header">
      <div className="dm-page-header__brand">
        <div className="dm-header__icon" aria-hidden="true">
          <Icon size={28} strokeWidth={1.75} />
        </div>
        <div className="dm-page-header__content">
          <div className="dm-page-header__context">
            <FilialBadge filial={filial} displayName={filialDisplayName} />
          </div>
          <p className="dm-eyebrow">DELPI • Manutenção • Mini-aplicadores</p>
          <h1>{title}</h1>
          <span className="dm-page-subtitle">{subtitle}</span>
          <MiniAplicadoresNav
            currentPath={currentPath}
            moduleHomePath={moduleHomePath}
            showConfiguration={showConfiguration}
            onNavigate={onNavigate}
          />
        </div>
      </div>
      {actions ? <div className="dm-header-actions">{actions}</div> : null}
    </header>
  );
}

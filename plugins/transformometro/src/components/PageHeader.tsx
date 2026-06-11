import type { ReactNode } from "react";
import { Gauge, RefreshCw } from "lucide-react";
import { TransformometroNav } from "./TransformometroNav";
import "./PageHeader.css";

type PageHeaderProps = {
  title: string;
  subtitle: string;
  currentPath?: string;
  onNavigate: (path: string) => void;
  onRefresh?: () => void;
  refreshing?: boolean;
  actions?: ReactNode;
};

export function PageHeader({
  title,
  subtitle,
  currentPath,
  onNavigate,
  onRefresh,
  refreshing = false,
  actions,
}: PageHeaderProps) {
  return (
    <header className="ds-page-header">
      <div className="ds-page-header__brand">
        <div className="ds-header__icon" aria-hidden="true">
          <Gauge size={28} strokeWidth={1.75} />
        </div>
        <div className="ds-page-header__content">
          <p className="ds-eyebrow">DELPI • Transformômetro</p>
          <h1>{title}</h1>
          <span className="ds-page-subtitle">{subtitle}</span>
          <TransformometroNav currentPath={currentPath} onNavigate={onNavigate} />
        </div>
      </div>

      <div className="ds-header-actions">
        {actions}
        {onRefresh ? (
          <button
            className="ds-primary-btn"
            type="button"
            onClick={onRefresh}
            disabled={refreshing}
          >
            <RefreshCw size={16} />
            {refreshing ? "Atualizando…" : "Atualizar"}
          </button>
        ) : null}
      </div>
    </header>
  );
}

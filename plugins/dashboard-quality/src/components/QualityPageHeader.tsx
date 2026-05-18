import type { ReactNode } from "react";
import { ListFilter, ShieldCheck } from "lucide-react";
import { QualityNav } from "./QualityNav";

type QualityPageHeaderProps = {
  title: string;
  subtitle: string;
  currentPath?: string;
  onRefresh?: () => void;
  refreshing?: boolean;
  actions?: ReactNode;
};

export function QualityPageHeader({
  title,
  subtitle,
  currentPath,
  onRefresh,
  refreshing = false,
  actions,
}: QualityPageHeaderProps) {
  return (
    <header className="dq-page-header">
      <div className="dq-page-header__brand">
        <div className="dq-header__icon" aria-hidden="true">
          <ShieldCheck size={28} strokeWidth={1.75} />
        </div>
        <div>
          <p className="dq-eyebrow">DELPI • Qualidade</p>
          <h1>{title}</h1>
          <span className="dq-page-subtitle">{subtitle}</span>
          <QualityNav currentPath={currentPath} />
        </div>
      </div>

      <div className="dq-header-actions">
        {actions}
        {onRefresh ? (
          <button
            className="dq-primary-btn"
            type="button"
            onClick={onRefresh}
            disabled={refreshing}
          >
            <ListFilter size={16} />
            {refreshing ? "Atualizando…" : "Atualizar"}
          </button>
        ) : null}
      </div>
    </header>
  );
}

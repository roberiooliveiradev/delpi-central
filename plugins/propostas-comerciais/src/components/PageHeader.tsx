import type { ReactNode } from "react";
import { FileText, RefreshCw } from "lucide-react";

type PageHeaderProps = {
  title: string;
  subtitle: string;
  loading?: boolean;
  onRefresh?: () => void;
  actions?: ReactNode;
};

export function PageHeader({
  title,
  subtitle,
  loading = false,
  onRefresh,
  actions,
}: PageHeaderProps) {
  return (
    <header className="pc-page-header">
      <div className="pc-page-header__title">
        <span className="pc-page-header__icon" aria-hidden="true">
          <FileText size={28} strokeWidth={1.75} />
        </span>
        <div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
      </div>
      <div className="pc-page-header__actions">
        {actions}
        {onRefresh ? (
          <button
            type="button"
            className="pc-btn pc-btn--primary"
            onClick={onRefresh}
            disabled={loading}
          >
            <RefreshCw size={16} aria-hidden="true" className={loading ? "pc-spin" : undefined} />
            Atualizar
          </button>
        ) : null}
      </div>
    </header>
  );
}

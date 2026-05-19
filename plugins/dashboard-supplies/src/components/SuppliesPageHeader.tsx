import type { ReactNode } from "react";
import { ListFilter, Package } from "lucide-react";
import type { SuppliesFilterUrlState } from "../utils/filterUrl";
import { SuppliesNav } from "./SuppliesNav";

type SuppliesPageHeaderProps = {
  title: string;
  subtitle: string;
  currentPath?: string;
  filterState?: SuppliesFilterUrlState;
  onRefresh?: () => void;
  refreshing?: boolean;
  actions?: ReactNode;
};

export function SuppliesPageHeader({
  title,
  subtitle,
  currentPath,
  filterState,
  onRefresh,
  refreshing = false,
  actions,
}: SuppliesPageHeaderProps) {
  return (
    <header className="ds-page-header">
      <div className="ds-page-header__brand">
        <div className="ds-header__icon" aria-hidden="true">
          <Package size={28} strokeWidth={1.75} />
        </div>
        <div>
          <p className="ds-eyebrow">DELPI • Suprimentos</p>
          <h1>{title}</h1>
          <span className="ds-page-subtitle">{subtitle}</span>
          <SuppliesNav currentPath={currentPath} filterState={filterState} />
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
            <ListFilter size={16} />
            {refreshing ? "Atualizando…" : "Atualizar"}
          </button>
        ) : null}
      </div>
    </header>
  );
}

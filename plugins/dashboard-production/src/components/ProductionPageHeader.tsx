import type { ReactNode } from "react";
import { Factory, ListFilter } from "lucide-react";

import { PRODUCTION_ROUTES } from "../constants/routes";
import type { ProductionFilterUrlState } from "../utils/filterUrl";
import { ProductionNav } from "./ProductionNav";

type ProductionPageHeaderProps = {
  title?: string;
  subtitle?: string;
  currentPath?: string;
  filterState?: ProductionFilterUrlState;
  onRefresh: () => void;
  refreshing?: boolean;
  actions?: ReactNode;
};

export function ProductionPageHeader({
  title = "Dashboard Produção",
  subtitle = "Custos sobre ROL, OEE e entrega no prazo",
  currentPath,
  filterState,
  onRefresh,
  refreshing = false,
  actions,
}: ProductionPageHeaderProps) {
  return (
    <header className="dp-page-header">
      <div className="dp-page-header__brand">
        <div className="dp-header__icon" aria-hidden="true">
          <Factory size={28} strokeWidth={1.75} />
        </div>
        <div>
          <p className="dp-eyebrow">DELPI • Produção</p>
          <h1>{title}</h1>
          <span className="dp-page-subtitle">{subtitle}</span>
          <ProductionNav
            currentPath={currentPath ?? PRODUCTION_ROUTES.home}
            filterState={filterState}
          />
        </div>
      </div>

      <div className="dp-header-actions">
        {actions}
        <button
          className="dp-primary-btn"
          type="button"
          onClick={onRefresh}
          disabled={refreshing}
        >
          <ListFilter size={16} />
          {refreshing ? "Atualizando…" : "Atualizar"}
        </button>
      </div>
    </header>
  );
}

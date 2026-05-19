import { ListFilter, Package } from "lucide-react";

type SuppliesPageHeaderProps = {
  onRefresh: () => void;
  refreshing?: boolean;
};

export function SuppliesPageHeader({
  onRefresh,
  refreshing = false,
}: SuppliesPageHeaderProps) {
  return (
    <header className="ds-page-header">
      <div className="ds-page-header__brand">
        <div className="ds-header__icon" aria-hidden="true">
          <Package size={28} strokeWidth={1.75} />
        </div>
        <div>
          <p className="ds-eyebrow">DELPI • Suprimentos</p>
          <h1>Dashboard Suprimentos</h1>
          <span className="ds-page-subtitle">
            CPV, OTD de compras, estoque e giro (IDD)
          </span>
        </div>
      </div>

      <div className="ds-header-actions">
        <button
          className="ds-primary-btn"
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

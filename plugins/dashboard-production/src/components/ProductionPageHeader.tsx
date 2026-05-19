import { Factory, ListFilter } from "lucide-react";

type ProductionPageHeaderProps = {
  onRefresh: () => void;
  refreshing?: boolean;
};

export function ProductionPageHeader({
  onRefresh,
  refreshing = false,
}: ProductionPageHeaderProps) {
  return (
    <header className="dp-page-header">
      <div className="dp-page-header__brand">
        <div className="dp-header__icon" aria-hidden="true">
          <Factory size={28} strokeWidth={1.75} />
        </div>
        <div>
          <p className="dp-eyebrow">DELPI • Produção</p>
          <h1>Dashboard Produção</h1>
          <span className="dp-page-subtitle">
            Custos sobre ROL, OEE e entrega no prazo
          </span>
        </div>
      </div>

      <div className="dp-header-actions">
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

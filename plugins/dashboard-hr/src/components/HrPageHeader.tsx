import { ListFilter, Users } from "lucide-react";

type HrPageHeaderProps = {
  title: string;
  subtitle: string;
  onRefresh?: () => void;
  refreshing?: boolean;
};

export function HrPageHeader({
  title,
  subtitle,
  onRefresh,
  refreshing = false,
}: HrPageHeaderProps) {
  return (
    <header className="dh-page-header">
      <div className="dh-page-header__brand">
        <div className="dh-header__icon" aria-hidden="true">
          <Users size={28} strokeWidth={1.75} />
        </div>
        <div>
          <p className="dh-eyebrow">DELPI • Recursos Humanos</p>
          <h1>{title}</h1>
          <span className="dh-page-subtitle">{subtitle}</span>
        </div>
      </div>

      {onRefresh ? (
        <div className="dh-header-actions">
          <button
            className="dh-primary-btn"
            type="button"
            onClick={onRefresh}
            disabled={refreshing}
          >
            <ListFilter size={16} />
            {refreshing ? "Atualizando…" : "Atualizar"}
          </button>
        </div>
      ) : null}
    </header>
  );
}

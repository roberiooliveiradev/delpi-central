import { ClipboardList, RefreshCw } from "lucide-react";

type PageHeaderProps = {
  loading: boolean;
  onRefresh: () => void;
  totalLoaded: number;
};

export function PageHeader({ loading, onRefresh, totalLoaded }: PageHeaderProps) {
  return (
    <header className="pva-page-header">
      <div className="pva-page-header__title">
        <span className="pva-page-header__icon" aria-hidden="true">
          <ClipboardList size={28} strokeWidth={1.75} />
        </span>
        <div>
          <h1>Pedidos de Venda em Aberto</h1>
          <p>
            Consulta operacional de carteira em aberto
            {totalLoaded > 0 ? ` · ${totalLoaded.toLocaleString("pt-BR")} linha(s) carregadas` : ""}
          </p>
        </div>
      </div>
      <button
        type="button"
        className="pva-btn pva-btn--primary"
        onClick={onRefresh}
        disabled={loading}
      >
        <RefreshCw size={16} aria-hidden="true" className={loading ? "pva-spin" : undefined} />
        Atualizar
      </button>
    </header>
  );
}

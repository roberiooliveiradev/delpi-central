import { ClipboardCheck, RefreshCw } from "lucide-react";

type PageHeaderProps = {
  loading: boolean;
  branch: string;
  total: number;
  onRefresh: () => void;
};

export function PageHeader({ loading, branch, total, onRefresh }: PageHeaderProps) {
  return (
    <header className="ie-page-header">
      <div className="ie-page-header__title">
        <span className="ie-page-header__icon" aria-hidden="true">
          <ClipboardCheck size={28} strokeWidth={1.75} />
        </span>
        <div>
          <h1>Histórico de Inspeções</h1>
          <p>
            Inspeções de entrada — filial {branch}
            {total > 0 ? ` · ${total.toLocaleString("pt-BR")} registro(s)` : ""}
          </p>
        </div>
      </div>
      <button
        type="button"
        className="ie-btn ie-btn--primary"
        onClick={onRefresh}
        disabled={loading}
      >
        <RefreshCw size={16} aria-hidden="true" className={loading ? "ie-spin" : undefined} />
        Atualizar
      </button>
    </header>
  );
}

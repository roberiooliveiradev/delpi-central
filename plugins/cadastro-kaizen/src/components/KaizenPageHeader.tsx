import type { ReactNode } from "react";
import { ArrowLeft, Sparkles } from "lucide-react";

type KaizenPageHeaderProps = {
  title: string;
  subtitle: string;
  actions?: ReactNode;
  showBack?: boolean;
  onBack?: () => void;
};

export function KaizenPageHeader({
  title,
  subtitle,
  actions,
  showBack,
  onBack,
}: KaizenPageHeaderProps) {
  return (
    <header className="kz-page-header">
      <div className="kz-page-header__brand">
        <div className="kz-header__icon" aria-hidden="true">
          <Sparkles size={28} strokeWidth={1.75} />
        </div>
        <div>
          <p className="kz-eyebrow">DELPI • Qualidade • Cadastro</p>
          <h1>{title}</h1>
          <span className="kz-page-subtitle">{subtitle}</span>
        </div>
      </div>

      <div className="kz-header-actions">
        {showBack && onBack ? (
          <button type="button" className="kz-ghost-btn" onClick={onBack}>
            <ArrowLeft size={16} aria-hidden="true" />
            Voltar
          </button>
        ) : null}
        {actions}
      </div>
    </header>
  );
}

type ListHeaderActionsProps = {
  onNew: () => void;
  onRefresh: () => void;
  loading?: boolean;
};

export function KaizenListHeaderActions({ onNew, onRefresh, loading }: ListHeaderActionsProps) {
  return (
    <>
      <button type="button" className="kz-primary-btn" onClick={onNew}>
        Novo kaizen
      </button>
      <button
        type="button"
        className="kz-ghost-btn"
        onClick={onRefresh}
        disabled={loading}
      >
        {loading ? "Atualizando…" : "Atualizar"}
      </button>
    </>
  );
}

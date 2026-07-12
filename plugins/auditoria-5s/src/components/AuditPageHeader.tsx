import { ArrowLeft, ClipboardCheck, Plus, RefreshCw } from "lucide-react";
import type { ReactNode } from "react";

type Props = {
  branch: string;
  subtitle: string;
  title?: string;
  showBack?: boolean;
  onBack?: () => void;
  actions?: ReactNode;
};

export function AuditPageHeader({ branch, subtitle, title, showBack, onBack, actions }: Props) {
  return (
    <header className="a5s-hero">
      <div className="a5s-hero__glow a5s-hero__glow--primary" aria-hidden />
      <div className="a5s-hero__glow a5s-hero__glow--secondary" aria-hidden />
      <div className="a5s-hero__inner">
        <div className="a5s-hero__brand">
          <div className="a5s-hero__icon" aria-hidden>
            <ClipboardCheck size={28} strokeWidth={1.75} />
          </div>
          <div className="a5s-hero__copy">
            <p className="a5s-hero__eyebrow">Filial {branch} · Qualidade</p>
            <h1 className="a5s-hero__title">{title ?? "Auditoria 5S"}</h1>
            <p className="a5s-hero__subtitle">{subtitle}</p>
          </div>
        </div>
        <div className="a5s-hero__actions">
          {showBack && onBack ? (
            <button type="button" className="a5s-btn a5s-btn--ghost a5s-btn--header" onClick={onBack}>
              <ArrowLeft size={16} aria-hidden />
              Voltar
            </button>
          ) : null}
          {actions}
        </div>
      </div>
    </header>
  );
}

type ListActionsProps = {
  onNew: () => void;
  onRefresh: () => void;
  loading?: boolean;
};

export function AuditListHeaderActions({ onNew, onRefresh, loading }: ListActionsProps) {
  return (
    <>
      <button type="button" className="a5s-btn a5s-btn--header" onClick={onNew}>
        <Plus size={16} aria-hidden />
        Nova auditoria
      </button>
      <button
        type="button"
        className="a5s-btn a5s-btn--ghost a5s-btn--header"
        onClick={onRefresh}
        disabled={loading}
      >
        <RefreshCw size={16} className={loading ? "a5s-spin" : undefined} aria-hidden />
        Atualizar
      </button>
    </>
  );
}

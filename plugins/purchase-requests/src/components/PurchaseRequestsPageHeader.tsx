import { CalendarDays, MapPin, RefreshCw, ShoppingCart } from "lucide-react";

import { formatDatePtBr } from "../utils/formatters";

type PurchaseRequestsPageHeaderProps = {
  branchLabel: string;
  branchCode: string;
  dateFrom: string;
  dateTo: string;
  onRefresh: () => void;
  refreshing?: boolean;
};

export function PurchaseRequestsPageHeader({
  branchLabel,
  branchCode,
  dateFrom,
  dateTo,
  onRefresh,
  refreshing = false,
}: PurchaseRequestsPageHeaderProps) {
  const periodLabel =
    dateFrom && dateTo
      ? `${formatDatePtBr(dateFrom)} — ${formatDatePtBr(dateTo)}`
      : "Período não definido";

  return (
    <header className="pr-hero" aria-label="Solicitações de compras">
      <div className="pr-hero__glow pr-hero__glow--primary" aria-hidden />
      <div className="pr-hero__glow pr-hero__glow--secondary" aria-hidden />

      <div className="pr-hero__inner">
        <div className="pr-hero__brand">
          <div className="pr-hero__icon" aria-hidden>
            <ShoppingCart size={28} strokeWidth={1.75} />
          </div>
          <div className="pr-hero__copy">
            <p className="pr-hero__eyebrow">{branchLabel} · Suprimentos</p>
            <h1 className="pr-hero__title">Solicitações de Compras</h1>
            <p className="pr-hero__subtitle">
              Acompanhe solicitações, pedidos de compra e recebimentos em um único lugar.
            </p>
          </div>
        </div>

        <div className="pr-hero__actions">
          <button
            type="button"
            className="pr-btn pr-btn--ghost pr-btn--header"
            onClick={onRefresh}
            disabled={refreshing}
          >
            <RefreshCw size={16} className={refreshing ? "pr-spin" : undefined} aria-hidden />
            {refreshing ? "Atualizando…" : "Atualizar"}
          </button>
        </div>
      </div>

      <div className="pr-hero__meta">
        <span className="pr-meta-chip">
          <MapPin size={15} aria-hidden />
          Filial {branchCode}
        </span>
        <span className="pr-meta-chip">
          <CalendarDays size={15} aria-hidden />
          {periodLabel}
        </span>
      </div>
    </header>
  );
}

import { ArrowUpRight, CalendarClock, PackageX } from "lucide-react";

import { HostContainedFitDialog } from "./PpcConfirmModal";
import { copy } from "../content/copy";
import type { PpcBranch, StockRupturePendencyItem } from "../types";
import { formatIsoDate } from "../utils/formatIsoDate";
import { safetyStockHref } from "../utils/finishedProductShortageQuery";

type Props = {
  item: StockRupturePendencyItem | null;
  branch: PpcBranch;
  asOf: string | null;
  onClose: () => void;
};

/** Mantém MT/KG/UN/MI da origem; matéria-prima não vira 'peças' automaticamente. */
export function formatMaterialQuantity(quantity: number | null, unit: string): string {
  if (quantity === null || !Number.isFinite(quantity)) return "—";
  const formatted = new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 4,
  }).format(quantity);
  return `${formatted}${unit ? ` ${unit}` : ""}`;
}

export function StockRuptureDetailModal({ item, branch, asOf, onClose }: Props) {
  if (!item || item.branch !== branch) return null;
  const labels = copy.home.opPendencies.stockRupture;
  const overdue = Boolean(asOf && item.first_shortage_date < asOf);

  return (
    <HostContainedFitDialog
      open
      title={labels.detailTitle}
      className="ppc-op-pendency-modal"
      onClose={onClose}
    >
      <div className="ppc-op-detail ppc-stock-rupture-detail">
        <header className="ppc-op-detail__hero">
          <div className="ppc-op-detail__identity">
            <span className="ppc-op-detail__eyebrow">{labels.material}</span>
            <h3>{item.product_code}</h3>
            {item.product_description ? (
              <p className="ppc-stock-rupture-detail__description">{item.product_description}</p>
            ) : null}
            <span className="ppc-op-detail__type">
              <PackageX size={14} aria-hidden="true" /> {labels.type}
            </span>
          </div>
          <div className="ppc-op-detail__date">
            <span>{overdue ? labels.overdueDate : labels.projectedDate}</span>
            <strong>
              <CalendarClock size={18} aria-hidden="true" />
              {formatIsoDate(item.first_shortage_date)}
            </strong>
            <small>{labels.branch} {item.branch}</small>
          </div>
        </header>

        <section className="ppc-op-detail__summary" aria-label={labels.summary}>
          <div>
            <span>{labels.availableStock}</span>
            <strong>{formatMaterialQuantity(item.available_stock, item.unit)}</strong>
          </div>
          <div className="ppc-stock-rupture-detail__balance">
            <span>{labels.projectedBalance}</span>
            <strong>{formatMaterialQuantity(item.shortage_balance, item.unit)}</strong>
          </div>
          <div>
            <span>{labels.lastInventory}</span>
            <strong>{formatIsoDate(item.last_inventory_date)}</strong>
          </div>
        </section>

        <section className="ppc-stock-rupture-detail__section" aria-label={labels.purchaseTitle}>
          <h3>{labels.purchaseTitle}</h3>
          <p>{item.next_purchase || labels.noPurchase}</p>
        </section>

        {item.observation ? (
          <section className="ppc-stock-rupture-detail__section" aria-label={labels.observation}>
            <h3>{labels.observation}</h3>
            <p>{item.observation}</p>
          </section>
        ) : null}

        <p className="ppc-stock-rupture-detail__method">{labels.method}</p>
        <footer className="ppc-op-detail__footer">
          <a
            className="ppc-op-detail__link"
            href={safetyStockHref(item.product_code)}
            onClick={onClose}
          >
            {labels.openSafetyStock} <ArrowUpRight size={15} aria-hidden="true" />
          </a>
          <button type="button" className="ppc-op-detail__close" onClick={onClose}>
            {labels.close}
          </button>
        </footer>
      </div>
    </HostContainedFitDialog>
  );
}

import { ArrowUpRight, CalendarClock, ClipboardList } from "lucide-react";

import { HostContainedFitDialog } from "./PpcConfirmModal";
import { copy } from "../content/copy";
import type { DemandLine, OpPendencyItem, PpcBranch } from "../types";
import { formatIsoDate } from "../utils/formatIsoDate";
import { formatOpQuantity } from "../utils/formatOpQuantity";
import { buildPpcHref, navigatePpc } from "../utils/routeParser";

type Props = {
  item: OpPendencyItem | null;
  branch: PpcBranch;
  onClose: () => void;
};

const labels = copy.home.opPendencies;

export function formatOpPendencyQuantity(
  pieces: number | null,
  quantity: number,
  unit: string,
): string {
  if (pieces !== null) {
    return `${new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 }).format(pieces)} ${pieces === 1 ? "peça" : labels.pieces}`;
  }
  return `${formatOpQuantity(quantity)} ${unit === "UNSPECIFIED" ? "unidade ERP não confirmada" : unit}`;
}

function amountAsPieces(quantity: number, unit: string): number | null {
  if (unit === "MI") return Math.round(quantity * 1000);
  if (unit === "PC" || unit === "UN") return Math.round(quantity);
  return null;
}

function sourceLabel(line: DemandLine): string {
  return line.source === "myweg" ? labels.sourceMyweg : labels.sourceProtheus;
}

function demandIdentifier(line: DemandLine): string {
  return line.source === "myweg"
    ? line.line_item || line.customer_order || "—"
    : `${line.sales_order}/${line.line_item}`;
}

function DemandRow({ line, unit }: { line: DemandLine; unit: string }) {
  const quantity = formatOpPendencyQuantity(
    amountAsPieces(line.uncovered_quantity, unit), line.uncovered_quantity, unit,
  );
  const stock = formatOpPendencyQuantity(
    amountAsPieces(line.allocated_stock, unit), line.allocated_stock, unit,
  );
  const fromOrders = formatOpPendencyQuantity(
    amountAsPieces(line.covered_by_orders, unit), line.covered_by_orders, unit,
  );

  return (
    <li className="ppc-op-detail__demand">
      <div className="ppc-op-detail__demand-identity">
        <span className="ppc-op-detail__source">{sourceLabel(line)}</span>
        <strong>{line.customer_name || "—"}</strong>
        <small>{labels.order}: {demandIdentifier(line)}</small>
        {line.covering_orders.length > 0 ? (
          <small>
            {labels.existingOps}: {line.covering_orders.map((op) => op.production_order).join(", ")}
          </small>
        ) : null}
      </div>
      <div className="ppc-op-detail__demand-quantities">
        <span>{labels.stock}: {stock} · {labels.fromOps}: {fromOrders}</span>
        <strong>{labels.missing}: {quantity}</strong>
      </div>
    </li>
  );
}

/** Modal operacional, leitura da necessidade antes de abrir uma OP no ERP. */
export function OpPendencyDetailModal({ item, branch, onClose }: Props) {
  if (!item) return null;

  const openDemand = () => {
    onClose();
    navigatePpc(
      buildPpcHref({ subpluginId: "demand", branch, demandSearch: item.product_code }),
    );
  };
  const nextQty = formatOpPendencyQuantity(
    item.next_uncovered_pieces, item.next_uncovered_quantity, item.unit,
  );
  const totalQty = formatOpPendencyQuantity(
    item.total_uncovered_pieces, item.total_uncovered_quantity, item.unit,
  );

  return (
    <HostContainedFitDialog open title={labels.detailTitle} className="ppc-op-pendency-modal" onClose={onClose}>
      <div className="ppc-op-detail">
        <header className="ppc-op-detail__hero">
          <div className="ppc-op-detail__identity">
            <span className="ppc-op-detail__eyebrow">{labels.forProduct}</span>
            <h3>{item.product_code}</h3>
            <span className="ppc-op-detail__type"><ClipboardList size={14} aria-hidden="true" />{labels.type}</span>
          </div>
          <div className="ppc-op-detail__date">
            <span>{labels.recommended}</span>
            <strong><CalendarClock size={18} aria-hidden="true" /> {item.suggested_op_date ? formatIsoDate(item.suggested_op_date) : labels.noDueDate}</strong>
            <small>{labels.required}: {formatIsoDate(item.required_date)}</small>
          </div>
        </header>

        <section className="ppc-op-detail__summary" aria-label={labels.total}>
          <div>
            <span>{labels.firstQty}</span>
            <strong>{nextQty}</strong>
          </div>
          <div>
            <span>{labels.total}</span>
            <strong>{totalQty}</strong>
          </div>
          <div>
            <span>{labels.demandCount}</span>
            <strong>{item.demand_count}</strong>
          </div>
        </section>

        <section className="ppc-op-detail__schedule" aria-label={labels.scheduleTitle}>
          <h3>{labels.scheduleTitle}</h3>
          <p>{labels.scheduleHint}</p>
          <ol className="ppc-op-detail__dates">
            {item.schedule.map((day, index) => (
              <li key={day.required_date ?? `no-date-${index}`} className="ppc-op-detail__date-group">
                <header className="ppc-op-detail__date-head">
                  <span className="ppc-op-detail__timeline-dot" aria-hidden="true" />
                  <div>
                    <span>{labels.required}: <strong>{formatIsoDate(day.required_date)}</strong></span>
                    <small>{labels.needOp} {day.suggested_op_date ? formatIsoDate(day.suggested_op_date) : labels.noDueDate}</small>
                  </div>
                  <strong className="ppc-op-detail__date-qty">
                    {formatOpPendencyQuantity(day.uncovered_pieces, day.uncovered_quantity, item.unit)}
                  </strong>
                </header>
                <ul className="ppc-op-detail__demands">
                  {day.lines.map((line) => (
                    <DemandRow key={line.id} line={line} unit={item.unit} />
                  ))}
                </ul>
              </li>
            ))}
          </ol>
        </section>

        <footer className="ppc-op-detail__footer">
          <button type="button" className="ppc-op-detail__link" onClick={openDemand}>
            {labels.openDemand}<ArrowUpRight size={15} aria-hidden="true" />
          </button>
          <button type="button" className="ppc-op-detail__close" onClick={onClose}>
            {labels.close}
          </button>
        </footer>
      </div>
    </HostContainedFitDialog>
  );
}

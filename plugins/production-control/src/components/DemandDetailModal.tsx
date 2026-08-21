import { createDashboardStatusBadge } from "@delpi/plugin-ui/index";

import { HostContainedWideDialog } from "./PpcConfirmModal";
import { copy } from "../content/copy";
import type { DemandLine, PpcBranch } from "../types";
import { demandStatusBadge } from "../utils/demandStatus";
import { formatIsoDate } from "../utils/formatIsoDate";
import { formatOpQuantity } from "../utils/formatOpQuantity";
import { buildPpcHref, navigatePpc } from "../utils/routeParser";

const StatusBadge = createDashboardStatusBadge({ prefix: "ppc" });

type DemandDetailModalProps = {
  line: DemandLine | null;
  branch: PpcBranch;
  onClose: () => void;
};

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="ppc-demand-detail__field">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function Metric({ label, value, tone }: { label: string; value: string; tone?: "warn" | "ok" }) {
  return (
    <div
      className={
        tone ? `ppc-demand-detail__metric ppc-demand-detail__metric--${tone}` : "ppc-demand-detail__metric"
      }
    >
      <span className="ppc-demand-detail__metric-label">{label}</span>
      <strong className="ppc-demand-detail__metric-value">{value}</strong>
    </div>
  );
}

function statusReason(line: DemandLine): string {
  const detail = copy.demand.detail;
  if (line.status === "late") {
    return detail.reasonLate(line.days_late);
  }
  if (line.status === "covered_by_stock") {
    return detail.reasonStock;
  }
  if (line.status === "covered_by_order") {
    return detail.reasonOrder(formatIsoDate(line.coverage_date));
  }
  // at_risk — distinguir buraco de quantidade vs OP depois da entrega
  if (line.uncovered_quantity > 0) {
    return detail.reasonUncovered(formatOpQuantity(line.uncovered_quantity));
  }
  if (line.covering_orders.length > 0 && line.coverage_date && line.due_date) {
    return detail.reasonLateOp(formatIsoDate(line.coverage_date), formatIsoDate(line.due_date));
  }
  return detail.reasonAtRisk;
}

/** Cobertura da linha: quanto veio do estoque, quais OPs cobrem o resto e o que sobrou. */
export function DemandDetailModal({ line, branch, onClose }: DemandDetailModalProps) {
  if (!line) return null;

  const detail = copy.demand.detail;
  const badge = demandStatusBadge(line.status);
  const coveredByOrders = line.covered_by_orders;

  const openMachineLoad = () => {
    onClose();
    navigatePpc(
      buildPpcHref({ subpluginId: "machine-load", branch, locateQuery: line.product_code }),
    );
  };

  return (
    <HostContainedWideDialog open title={detail.title} onClose={onClose}>
      <div className="ppc-demand-detail">
        <header className="ppc-demand-detail__header">
          <div className="ppc-demand-detail__identity">
            <p className="ppc-demand-detail__product">{line.product_code}</p>
            <p className="ppc-demand-detail__customer">{line.customer_name || "—"}</p>
          </div>
          <div className="ppc-demand-detail__status">
            <StatusBadge label={badge.label} variant={badge.variant} />
            <p className="ppc-demand-detail__reason">{statusReason(line)}</p>
          </div>
        </header>

        <section className="ppc-demand-detail__block" aria-label={detail.orderSection}>
          <h3 className="ppc-demand-detail__block-title">{detail.orderSection}</h3>
          <dl className="ppc-demand-detail__grid">
            <Field label={detail.order} value={`${line.sales_order}/${line.line_item}`} />
            <Field label={detail.customerOrder} value={line.customer_order || "—"} />
            <Field label={detail.due} value={formatIsoDate(line.due_date)} />
            <Field label={detail.dispatch} value={formatIsoDate(line.dispatch_date)} />
          </dl>
        </section>

        <section className="ppc-demand-detail__block" aria-label={detail.qtySection}>
          <h3 className="ppc-demand-detail__block-title">{detail.qtySection}</h3>
          <div className="ppc-demand-detail__metrics">
            <Metric label={detail.ordered} value={formatOpQuantity(line.ordered_quantity)} />
            <Metric label={detail.delivered} value={formatOpQuantity(line.delivered_quantity)} />
            <Metric label={detail.open} value={formatOpQuantity(line.open_quantity)} />
          </div>
        </section>

        <section className="ppc-demand-detail__block" aria-label={detail.coverageSection}>
          <h3 className="ppc-demand-detail__block-title">{detail.coverageSection}</h3>
          <div className="ppc-demand-detail__metrics">
            <Metric
              label={detail.stock}
              value={formatOpQuantity(line.allocated_stock)}
              tone={line.allocated_stock > 0 ? "ok" : undefined}
            />
            <Metric
              label={detail.coveredByOrders}
              value={formatOpQuantity(coveredByOrders)}
              tone={coveredByOrders > 0 ? "ok" : undefined}
            />
            <Metric
              label={detail.uncovered}
              value={formatOpQuantity(line.uncovered_quantity)}
              tone={line.uncovered_quantity > 0 ? "warn" : "ok"}
            />
          </div>

          <div className="ppc-demand-detail__ops">
            <div className="ppc-demand-detail__ops-head">
              <span>{detail.coverageOrder}</span>
              <span>{detail.coverageQuantity}</span>
              <span>{detail.coverageDate}</span>
            </div>
            {line.covering_orders.length === 0 ? (
              <p className="ppc-demand-detail__empty">{detail.coverageEmpty}</p>
            ) : (
              <ul className="ppc-demand-detail__ops-list">
                {line.covering_orders.map((order) => {
                  const lateVsDue =
                    line.due_date &&
                    order.expected_date &&
                    order.expected_date > line.due_date;
                  return (
                    <li
                      key={`${order.production_order}-${order.quantity}-${order.expected_date ?? ""}`}
                      className={
                        lateVsDue
                          ? "ppc-demand-detail__ops-row ppc-demand-detail__ops-row--late"
                          : "ppc-demand-detail__ops-row"
                      }
                    >
                      <span className="ppc-demand-detail__coverage-order">
                        {order.production_order}
                      </span>
                      <span>{formatOpQuantity(order.quantity)}</span>
                      <span className="ppc-demand-detail__coverage-date">
                        {formatIsoDate(order.expected_date)}
                        {lateVsDue ? ` · ${detail.opAfterDue}` : ""}
                      </span>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </section>

        <footer className="ppc-demand-detail__actions">
          <button type="button" className="ppc-demand-detail__link" onClick={openMachineLoad}>
            {detail.machineLoadLink}
          </button>
          <button type="button" className="ppc-demand-detail__close" onClick={onClose}>
            {detail.close}
          </button>
        </footer>
      </div>
    </HostContainedWideDialog>
  );
}

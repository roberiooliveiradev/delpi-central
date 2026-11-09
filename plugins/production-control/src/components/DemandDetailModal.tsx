import { createDashboardStatusBadge } from "@delpi/plugin-ui/index";
import { ArrowUpRight } from "lucide-react";
import { useState } from "react";

import { HostContainedFitDialog } from "./PpcConfirmModal";
import { copy } from "../content/copy";
import type { DemandLine, PpcBranch } from "../types";
import { demandMywegRecordId, isMywegDemandLine } from "../utils/demandOrderLabel";
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

function Fact({
  label,
  value,
  compact = false,
}: {
  label: string;
  value: string;
  compact?: boolean;
}) {
  return (
    <div className={compact ? "ppc-demand-line__fact ppc-demand-line__fact--compact" : "ppc-demand-line__fact"}>
      <dt>{label}</dt>
      <dd title={value}>{value}</dd>
    </div>
  );
}

function Metric({
  label,
  value,
  tone = "neutral",
  prominent = false,
}: {
  label: string;
  value: string;
  tone?: "neutral" | "positive" | "attention";
  prominent?: boolean;
}) {
  const className = [
    "ppc-demand-line__metric",
    "ppc-demand-line__metric--" + tone,
    prominent ? "ppc-demand-line__metric--prominent" : "",
  ].filter(Boolean).join(" ");
  return (
    <div className={className}>
      <span className="ppc-demand-line__metric-label">{label}</span>
      <strong className="ppc-demand-line__metric-value">{value}</strong>
    </div>
  );
}

/** Exibe a observação da OP por padrão; textos longos podem ser expandidos. */
function OpObservation({ text }: { text: string | null | undefined }) {
  const [expanded, setExpanded] = useState(false);
  const note = (text ?? "").trim();
  if (!note) return null;

  const expandable = note.length > 180 || note.includes("\n");
  return (
    <div className="ppc-demand-line__op-note">
      <span className="ppc-demand-line__op-note-label">{copy.demand.detail.opObservation}</span>
      <p
        className={[
          "ppc-demand-line__op-note-text",
          expandable && !expanded ? "ppc-demand-line__op-note-text--collapsed" : "",
        ].filter(Boolean).join(" ")}
      >
        {note}
      </p>
      {expandable ? (
        <button
          type="button"
          className="ppc-demand-line__op-note-toggle"
          aria-expanded={expanded}
          onClick={() => setExpanded((current) => !current)}
        >
          {expanded ? copy.demand.detail.opObservationLess : copy.demand.detail.opObservationMore}
        </button>
      ) : null}
    </div>
  );
}

function fiscalPieces(quantityMi: number): string {
  return new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 }).format(
    Math.round(quantityMi * 1000),
  );
}

function statusReason(line: DemandLine): string {
  const detail = copy.demand.detail;
  if (line.status === "late") return detail.reasonLate(line.days_late);
  if (line.status === "covered_by_stock") return detail.reasonStock;
  if (line.status === "covered_by_order") {
    return detail.reasonOrder(formatIsoDate(line.coverage_date));
  }
  if (line.uncovered_quantity > 0) {
    return detail.reasonUncovered(formatOpQuantity(line.uncovered_quantity));
  }
  if (line.covering_orders.length > 0 && line.coverage_date && line.due_date) {
    return detail.reasonLateOp(formatIsoDate(line.coverage_date), formatIsoDate(line.due_date));
  }
  return detail.reasonAtRisk;
}

/** Leitura executiva da demanda, da cobertura e das observações das OPs. */
export function DemandDetailModal({ line, branch, onClose }: DemandDetailModalProps) {
  if (!line) return null;

  const detail = copy.demand.detail;
  const badge = demandStatusBadge(line.status);
  const orders = line.covering_orders;
  const orderIsMyweg = isMywegDemandLine(line);

  const openMachineLoad = () => {
    onClose();
    navigatePpc(
      buildPpcHref({ subpluginId: "machine-load", branch, locateQuery: line.product_code }),
    );
  };

  return (
    <HostContainedFitDialog
      open
      title={detail.title}
      className="ppc-demand-line-dialog ppc-modal--demand-line"
      onClose={onClose}
    >
      <div className="ppc-demand-line">
        <header className="ppc-demand-line__hero">
          <div className="ppc-demand-line__identity">
            <span className="ppc-demand-line__eyebrow">{detail.product}</span>
            <h3 className="ppc-demand-line__product">{line.product_code}</h3>
            <p className="ppc-demand-line__customer">{line.customer_name || "—"}</p>
          </div>
          <div className="ppc-demand-line__status">
            <StatusBadge label={badge.label} variant={badge.variant} />
            <p className="ppc-demand-line__reason">{statusReason(line)}</p>
          </div>
        </header>

        <section className="ppc-demand-line__section ppc-demand-line__section--details" aria-label={detail.orderSection}>
          <h3 className="ppc-demand-line__section-title">{detail.orderSection}</h3>
          <dl className="ppc-demand-line__facts">
            {orderIsMyweg ? (
              <>
                <Fact label={detail.mywegNeed} value={copy.demand.mywegNeedLabel} />
                <Fact label={detail.mywegRecordId} value={demandMywegRecordId(line) || "—"} />
              </>
            ) : (
              <Fact label={detail.order} value={line.sales_order + "/" + line.line_item} />
            )}
            <Fact label={detail.customerOrder} value={line.customer_order || "—"} />
            <Fact label={detail.due} value={formatIsoDate(line.due_date)} compact />
            <Fact label={detail.dispatch} value={formatIsoDate(line.dispatch_date)} compact />
          </dl>
        </section>

        {orderIsMyweg && ((line.fiscal_offset_mi ?? 0) > 0 || line.fiscal_coverage_incomplete) ? (
          <section className="ppc-demand-line__fiscal" aria-label={detail.fiscalTitle}>
            <div className="ppc-demand-line__section-heading">
              <h3 className="ppc-demand-line__section-title">{detail.fiscalTitle}</h3>
            </div>
            {line.fiscal_coverage_incomplete ? (
              <p className="ppc-demand-line__warning" role="status">{detail.fiscalPending}</p>
            ) : null}
            {(line.fiscal_offset_mi ?? 0) > 0 ? (
              <>
                <dl className="ppc-demand-line__fiscal-facts">
                  <Fact
                    label={detail.rawMywegQuantity}
                    value={`${fiscalPieces(line.raw_myweg_quantity_mi ?? 0)} peças`}
                  />
                  <Fact
                    label={detail.fiscalOffset}
                    value={`${fiscalPieces(line.fiscal_offset_mi ?? 0)} peças`}
                  />
                  <Fact
                    label={detail.effectiveMyweg}
                    value={`${fiscalPieces(line.open_quantity)} peças`}
                  />
                </dl>
                <p className="ppc-demand-line__fiscal-disclaimer">{detail.fiscalDisclaimer}</p>
                {line.fiscal_invoice_refs && line.fiscal_invoice_refs.length > 0 ? (
                  <div className="ppc-demand-line__fiscal-documents">
                    <span>{detail.invoiceReference}</span>
                    <ul>
                      {line.fiscal_invoice_refs.map((ref) => (
                        <li key={ref.fiscal_key}>
                          NF {ref.invoice}/{ref.series} · item {ref.item} · {ref.quantity_un} peças
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </>
            ) : null}
          </section>
        ) : null}

        <div className="ppc-demand-line__summary">
          <section className="ppc-demand-line__section ppc-demand-line__section--summary" aria-label={detail.qtySection}>
            <h3 className="ppc-demand-line__section-title">{detail.qtySection}</h3>
            <div className="ppc-demand-line__metrics">
              <Metric label={detail.ordered} value={formatOpQuantity(line.ordered_quantity)} />
              <Metric label={detail.delivered} value={formatOpQuantity(line.delivered_quantity)} />
              <Metric label={detail.open} value={formatOpQuantity(line.open_quantity)} prominent />
            </div>
          </section>
          <section className="ppc-demand-line__section ppc-demand-line__section--summary" aria-label={detail.coverageSection}>
            <h3 className="ppc-demand-line__section-title">{detail.coverageSection}</h3>
            <div className="ppc-demand-line__metrics">
              <Metric label={detail.stock} value={formatOpQuantity(line.allocated_stock)} />
              <Metric
                label={detail.coveredByOrders}
                value={formatOpQuantity(line.covered_by_orders)}
                tone={line.covered_by_orders > 0 ? "positive" : "neutral"}
                prominent
              />
              <Metric
                label={detail.uncovered}
                value={formatOpQuantity(line.uncovered_quantity)}
                tone={line.uncovered_quantity > 0 ? "attention" : "neutral"}
              />
            </div>
          </section>
        </div>

        <section className="ppc-demand-line__section ppc-demand-line__section--orders" aria-label={detail.coverageTitle}>
          <div className="ppc-demand-line__section-heading">
            <h3 className="ppc-demand-line__section-title">{detail.coverageTitle}</h3>
            {orders.length > 0 ? (
              <span className="ppc-demand-line__count">{detail.opCount(orders.length)}</span>
            ) : null}
          </div>

          {line.op_coverage_incomplete ? (
            <div className="ppc-demand-line__warning" role="status">
              {detail.opCoverageIncomplete}
            </div>
          ) : null}

          {orders.length === 0 ? (
            <div className="ppc-demand-line__empty">{detail.coverageEmpty}</div>
          ) : (
            <ul className="ppc-demand-line__op-list">
              {orders.map((order, index) => {
                const lateVsDue = Boolean(
                  line.due_date && order.expected_date && order.expected_date > line.due_date,
                );
                return (
                  <li className="ppc-demand-line__op" key={order.production_order + ":" + index}>
                    <div className="ppc-demand-line__op-row">
                      <div className="ppc-demand-line__op-cell ppc-demand-line__op-cell--number">
                        <span>{detail.coverageOrder}</span>
                        <strong>{order.production_order}</strong>
                      </div>
                      <div className="ppc-demand-line__op-cell">
                        <span>{detail.coverageQuantity}</span>
                        <strong>{formatOpQuantity(order.quantity)}</strong>
                      </div>
                      <div className="ppc-demand-line__op-cell">
                        <span>{detail.coverageDate}</span>
                        <strong>{formatIsoDate(order.expected_date)}</strong>
                        {lateVsDue ? (
                          <small className="ppc-demand-line__op-late">{detail.opAfterDue}</small>
                        ) : null}
                      </div>
                    </div>
                    <OpObservation text={order.observation} />
                  </li>
                );
              })}
            </ul>
          )}
        </section>

        <footer className="ppc-demand-line__footer">
          <button type="button" className="ppc-demand-line__navigate" onClick={openMachineLoad}>
            {detail.machineLoadLink}
            <ArrowUpRight size={15} aria-hidden="true" />
          </button>
          <button type="button" className="ppc-demand-line__close" onClick={onClose}>
            {detail.close}
          </button>
        </footer>
      </div>
    </HostContainedFitDialog>
  );
}

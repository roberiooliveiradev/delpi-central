import { HostContainedWideDialog } from "./PpcConfirmModal";
import { copy } from "../content/copy";
import type { BillingDueTodayCheck, BillingDueTodayLine, PpcBranch } from "../types";
import { formatIsoDate } from "../utils/formatIsoDate";
import { formatOpQuantity } from "../utils/formatOpQuantity";
import { buildPpcHref, navigatePpc } from "../utils/routeParser";

type BillingDueDetailModalProps = {
  line: BillingDueTodayLine | null;
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

function checkLabel(check: BillingDueTodayCheck): string {
  if (check === "stock") return copy.home.billingDueCheckStock;
  if (check === "invoiced") return copy.home.billingDueCheckInvoiced;
  return copy.home.billingDueCheckPending;
}

function checkBadgeClass(check: BillingDueTodayCheck): string {
  return `ppc-billing-status ppc-billing-status--${check}`;
}

/** Detalhe da linha «a faturar até hoje» — permanece na gestão à vista. */
export function BillingDueDetailModal({ line, branch, onClose }: BillingDueDetailModalProps) {
  if (!line) return null;

  const detail = copy.home.billingDueDetail;

  const openMachineLoad = () => {
    onClose();
    navigatePpc(
      buildPpcHref({
        subpluginId: "machine-load",
        branch,
        locateQuery: line.product_code,
      }),
    );
  };

  const openDemand = () => {
    onClose();
    navigatePpc(
      buildPpcHref({
        subpluginId: "demand",
        branch,
        demandSearch: line.product_code || line.sales_order,
      }),
    );
  };

  return (
    <HostContainedWideDialog open title={detail.title} onClose={onClose}>
      <div className="ppc-demand-detail">
        <header className="ppc-demand-detail__header">
          <div>
            <p className="ppc-demand-detail__product">{line.product_code}</p>
            <p className="ppc-demand-detail__customer">{line.customer_name}</p>
          </div>
          <div className="ppc-demand-detail__badges">
            <span className={checkBadgeClass(line.check)}>{checkLabel(line.check)}</span>
            {line.days_late > 0 ? (
              <span className="ppc-demand-detail__late">
                {copy.demand.lateBadge(line.days_late)}
              </span>
            ) : null}
          </div>
        </header>

        <dl className="ppc-demand-detail__grid">
          <Field label={detail.order} value={`${line.sales_order}/${line.line_item}`} />
          <Field label={detail.customerOrder} value={line.customer_order || "—"} />
          <Field label={detail.due} value={formatIsoDate(line.due_date)} />
          <Field label={detail.dispatch} value={formatIsoDate(line.dispatch_date ?? null)} />
          <Field label={detail.invoice} value={formatIsoDate(line.invoice_date)} />
          <Field
            label={detail.ordered}
            value={formatOpQuantity(line.ordered_quantity ?? 0)}
          />
          <Field
            label={detail.delivered}
            value={formatOpQuantity(line.delivered_quantity ?? 0)}
          />
          <Field label={detail.open} value={formatOpQuantity(line.open_quantity)} />
          <Field
            label={detail.productStock}
            value={formatOpQuantity(line.product_stock ?? 0)}
          />
          <Field
            label={detail.stock}
            value={formatOpQuantity(line.allocated_stock ?? 0)}
          />
          <Field
            label={detail.uncovered}
            value={formatOpQuantity(line.uncovered_quantity ?? 0)}
          />
        </dl>

        <footer className="ppc-demand-detail__actions">
          <div className="ppc-demand-detail__links">
            {line.check !== "invoiced" ? (
              <button type="button" className="ppc-demand-detail__link" onClick={openDemand}>
                {detail.demandLink}
              </button>
            ) : null}
            <button type="button" className="ppc-demand-detail__link" onClick={openMachineLoad}>
              {detail.machineLoadLink}
            </button>
          </div>
          <button type="button" className="ppc-demand-detail__close" onClick={onClose}>
            {detail.close}
          </button>
        </footer>
      </div>
    </HostContainedWideDialog>
  );
}

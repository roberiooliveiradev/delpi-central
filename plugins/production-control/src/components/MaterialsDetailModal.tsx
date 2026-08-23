import { HostContainedWideDialog } from "./PpcConfirmModal";
import { copy } from "../content/copy";
import type { MaterialsLine, MaterialsShortageLine } from "../types";
import { formatIsoDate } from "../utils/formatIsoDate";
import { formatOpQuantity } from "../utils/formatOpQuantity";

type MaterialsDetailModalProps = {
  line: MaterialsLine | MaterialsShortageLine | null;
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

function isShortage(line: MaterialsLine | MaterialsShortageLine): line is MaterialsShortageLine {
  return line.kind === "shortage" || !("request_number" in line);
}

export function MaterialsDetailModal({ line, onClose }: MaterialsDetailModalProps) {
  if (!line) return null;

  const detail = copy.materials.detail;
  const shortage = isShortage(line);
  const title = shortage ? detail.shortageTitle : detail.title;
  const reason = shortage
    ? detail.shortageReason(formatOpQuantity(line.shortage_quantity))
    : line.needed_from_sc1 > 0
      ? detail.reasonNeeded(formatOpQuantity(line.needed_from_sc1))
      : detail.reason;

  return (
    <HostContainedWideDialog open title={title} onClose={onClose}>
      <div className="ppc-demand-detail">
        <header className="ppc-demand-detail__header">
          <div className="ppc-demand-detail__identity">
            <p className="ppc-demand-detail__product">
              {line.product_code} · {line.product_description || "—"}
            </p>
            {shortage ? null : (
              <p className="ppc-demand-detail__customer">
                {line.request_number}/{line.request_item}
              </p>
            )}
          </div>
        </header>
        <p className="ppc-demand-detail__reason">{reason}</p>
        <div className="ppc-demand-detail__metrics">
          <Metric label={detail.stock} value={formatOpQuantity(line.available_stock)} tone="ok" />
          <Metric label={detail.orders} value={formatOpQuantity(line.open_purchase_order_quantity)} />
          <Metric
            label={detail.commitments}
            value={formatOpQuantity(line.open_commitment_quantity)}
            tone="warn"
          />
          <Metric
            label={detail.safety}
            value={formatOpQuantity(line.safety_stock)}
            tone={line.safety_stock > 0 ? "warn" : undefined}
          />
          <Metric
            label={detail.projected}
            value={formatOpQuantity(line.projected_balance)}
            tone={line.projected_balance >= line.safety_stock ? "ok" : "warn"}
          />
        </div>
        <section className="ppc-demand-detail__block">
          <h3 className="ppc-demand-detail__block-title">{detail.formula}</h3>
          <dl className="ppc-demand-detail__grid">
            {shortage ? (
              <>
                <Field label={detail.product} value={line.product_code} />
                <Field label={detail.unit} value={line.unit || "—"} />
                <Field label={detail.openSc1} value={formatOpQuantity(line.open_sc1_quantity)} />
                <Field label={detail.needed} value={formatOpQuantity(line.needed_from_sc1)} />
                <Field label={detail.shortage} value={formatOpQuantity(line.shortage_quantity)} />
              </>
            ) : (
              <>
                <Field label={detail.request} value={`${line.request_number}/${line.request_item}`} />
                <Field label={detail.product} value={line.product_code} />
                <Field label={detail.supplier} value={line.supplier_name || "—"} />
                <Field label={detail.warehouse} value={line.warehouse || "—"} />
                <Field label={detail.unit} value={line.unit || "—"} />
                <Field label={detail.open} value={formatOpQuantity(line.open_quantity)} />
                <Field label={detail.needed} value={formatOpQuantity(line.needed_from_sc1)} />
                <Field
                  label={detail.required}
                  value={line.required_date ? formatIsoDate(line.required_date) : "—"}
                />
                <Field label={detail.issued} value={line.issue_date ? formatIsoDate(line.issue_date) : "—"} />
              </>
            )}
          </dl>
        </section>
      </div>
    </HostContainedWideDialog>
  );
}

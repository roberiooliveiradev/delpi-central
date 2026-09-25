import {
  createDashboardSegmentToggle,
  createDashboardStatusBadge,
} from "@delpi/plugin-ui/index";
import { useEffect, useMemo, useState } from "react";

import { HostContainedWideDialog } from "./PpcConfirmModal";
import { copy } from "../content/copy";
import type { LineFeederProductDetail, LineFeederStatusMeta } from "../types";
import { formatIsoDate } from "../utils/formatIsoDate";
import { formatOpQuantity } from "../utils/formatOpQuantity";
import {
  type LineFeederDetailTab,
  summarizeLineFeederProductDetail,
} from "../utils/lineFeederProductDetail";
import { requirementBadgeVariant } from "../utils/lineFeederStatus";

const StatusBadge = createDashboardStatusBadge({ prefix: "ppc" });
const DetailTabs = createDashboardSegmentToggle("ppc");

type LineFeederProductDetailModalProps = {
  open: boolean;
  loading: boolean;
  error: string | null;
  detail: LineFeederProductDetail | null;
  statuses: Record<string, LineFeederStatusMeta>;
  onClose: () => void;
};

function qtyLabel(value: number | null, unit: string): string {
  if (value == null) return "—";
  const amount = formatOpQuantity(value);
  return unit ? `${amount} ${unit}` : amount;
}

function warehouseLabel(value: string, empty: string): string {
  return value.trim() || empty;
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </>
  );
}

function NeedRow({
  label,
  value,
  hint,
  tone,
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: "collect" | "ok";
}) {
  const className = tone
    ? `ppc-feeder-detail__need ppc-feeder-detail__need--${tone}`
    : "ppc-feeder-detail__need";
  return (
    <div className={className}>
      <span className="ppc-feeder-detail__need-label">{label}</span>
      <strong className="ppc-feeder-detail__need-value">{value}</strong>
      {hint ? <p className="ppc-feeder-detail__need-hint">{hint}</p> : null}
    </div>
  );
}

export function LineFeederProductDetailModal({
  open,
  loading,
  error,
  detail,
  statuses,
  onClose,
}: LineFeederProductDetailModalProps) {
  const [tab, setTab] = useState<LineFeederDetailTab>("overview");
  const texts = copy.lineFeeder.detail;
  const product = detail?.product;
  const summary = useMemo(
    () => (detail ? summarizeLineFeederProductDetail(detail) : null),
    [detail],
  );

  useEffect(() => {
    setTab("overview");
  }, [open, product?.code]);

  if (!open) return null;

  const unit = product?.unit || "";
  const status = summary?.status ?? null;
  const statusMeta = status ? statuses[status] : undefined;
  const stock = detail?.stock;
  const transfers = detail?.transfers;
  const tabOptions = [
    { value: "overview" as const, label: texts.tabOverview },
    { value: "benches" as const, label: texts.tabBenches },
    { value: "movements" as const, label: texts.tabMovements },
  ];

  return (
    <HostContainedWideDialog open title={texts.title} onClose={onClose}>
      <div className="ppc-feeder-detail">
        {loading ? <p className="ppc-feeder-detail__empty">{texts.loading}</p> : null}
        {error ? <p className="ppc-state ppc-state--error">{error}</p> : null}

        {product && summary ? (
          <>
            <header className="ppc-feeder-detail__header">
              <div className="ppc-feeder-detail__identity">
                <div className="ppc-feeder-detail__title-row">
                  <p className="ppc-feeder-detail__code">{product.code}</p>
                  {status && statusMeta ? (
                    <StatusBadge
                      label={statusMeta.label}
                      variant={requirementBadgeVariant(status)}
                    />
                  ) : null}
                </div>
                {product.description ? (
                  <p className="ppc-feeder-detail__name">{product.description}</p>
                ) : null}
              </div>
            </header>

            <DetailTabs
              options={tabOptions}
              value={tab}
              onChange={setTab}
              ariaLabel={texts.tabsAria}
              size="sm"
              widthMode="content"
            />

            {tab === "overview" ? (
              <div className="ppc-feeder-detail__split">
                <section className="ppc-feeder-detail__panel" aria-label={texts.infoSection}>
                  <h3 className="ppc-feeder-detail__panel-title">{texts.infoSection}</h3>
                  <dl className="ppc-feeder-detail__facts">
                    <Fact label={texts.code} value={product.code} />
                    <Fact label={texts.description} value={product.description || "—"} />
                    <Fact label={texts.unit} value={product.unit || "—"} />
                    <Fact label={texts.kind} value={texts.kindValue} />
                    <Fact
                      label={texts.pickup}
                      value={
                        product.pickup_location.trim()
                          ? product.pickup_location
                          : texts.pickupEmpty
                      }
                    />
                    <Fact
                      label={texts.inventoryBlock}
                      value={
                        product.inventory_blocked
                          ? texts.inventoryBlocked
                          : texts.inventoryFree
                      }
                    />
                    <Fact
                      label={texts.destinations}
                      value={summary.destinations || texts.workCentersEmpty}
                    />
                  </dl>
                </section>

                <section className="ppc-feeder-detail__panel" aria-label={texts.needsSection}>
                  <h3 className="ppc-feeder-detail__panel-title">{texts.needsSection}</h3>
                  <div className="ppc-feeder-detail__needs">
                    <NeedRow
                      label={
                        detail.cutoff.time
                          ? texts.requiredUntil(detail.cutoff.time)
                          : texts.required
                      }
                      value={qtyLabel(summary.requiredQty, unit)}
                    />
                    <NeedRow
                      label={texts.stockLabel}
                      value={
                        stock?.available
                          ? qtyLabel(stock.quantity, unit)
                          : "—"
                      }
                      hint={
                        stock?.available
                          ? undefined
                          : stock?.message || texts.stockUnavailable
                      }
                      tone={
                        stock?.available && (stock.quantity ?? 0) > 0 ? "ok" : undefined
                      }
                    />
                    <NeedRow
                      label={texts.pointOfUse}
                      value={qtyLabel(summary.pointOfUseQty, unit)}
                    />
                    <NeedRow
                      label={texts.toCollect}
                      value={qtyLabel(summary.toDeliverQty, unit)}
                      tone={(summary.toDeliverQty ?? 0) > 0 ? "collect" : undefined}
                    />
                  </div>
                  {status === "at_risk" ? (
                    <p className="ppc-feeder-detail__alert" role="status">
                      {texts.atRiskBanner}
                    </p>
                  ) : null}
                </section>
              </div>
            ) : null}

            {tab === "benches" ? (
              <section className="ppc-feeder-detail__panel" aria-label={texts.workCentersSection}>
                <h3 className="ppc-feeder-detail__panel-title">{texts.workCentersSection}</h3>
                {detail.work_centers.length === 0 ? (
                  <p className="ppc-feeder-detail__empty">{texts.workCentersEmpty}</p>
                ) : (
                  <div className="ppc-demand-detail__ops">
                    <div className="ppc-demand-detail__ops-head">
                      <span>{texts.workCenter}</span>
                      <span>{texts.toDeliver}</span>
                      <span>{copy.lineFeeder.columns.status}</span>
                    </div>
                    <ul className="ppc-demand-detail__ops-list">
                      {detail.work_centers.map((row) => (
                        <li key={row.work_center} className="ppc-demand-detail__ops-row">
                          <span className="ppc-demand-detail__coverage-order">
                            {row.work_center_name || row.work_center}
                          </span>
                          <span>
                            {row.to_deliver_qty == null
                              ? "—"
                              : formatOpQuantity(row.to_deliver_qty)}
                          </span>
                          <span className="ppc-demand-detail__coverage-date">
                            {statuses[row.status]?.label ?? row.status}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </section>
            ) : null}

            {tab === "movements" ? (
              <section className="ppc-feeder-detail__panel" aria-label={texts.transfersSection}>
                <h3 className="ppc-feeder-detail__panel-title">{texts.transfersSection}</h3>
                <p className="ppc-feeder-detail__hint">{texts.transfersHint}</p>
                {!transfers?.available ? (
                  <p className="ppc-feeder-detail__empty">
                    {transfers?.message || texts.transfersUnavailable}
                  </p>
                ) : transfers.items.length === 0 ? (
                  <p className="ppc-feeder-detail__empty">{texts.transfersEmpty}</p>
                ) : (
                  <div className="ppc-demand-detail__ops">
                    <div className="ppc-demand-detail__ops-head ppc-feeder-detail__transfers-head">
                      <span>{texts.from}</span>
                      <span>{texts.to}</span>
                      <span>{texts.date}</span>
                      <span>{texts.quantity}</span>
                    </div>
                    <ul className="ppc-demand-detail__ops-list">
                      {transfers.items.map((row, index) => (
                        <li
                          key={`${row.document}|${row.issued_at}|${index}`}
                          className="ppc-demand-detail__ops-row ppc-feeder-detail__transfers-row"
                        >
                          <span>
                            {warehouseLabel(row.from_warehouse, texts.warehouseUnknown)}
                          </span>
                          <span>
                            {warehouseLabel(row.to_warehouse, texts.warehouseUnknown)}
                          </span>
                          <span className="ppc-demand-detail__coverage-date">
                            {formatIsoDate(row.issued_at)}
                          </span>
                          <span>
                            {row.quantity == null ? "—" : formatOpQuantity(row.quantity)}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </section>
            ) : null}
          </>
        ) : null}
      </div>
    </HostContainedWideDialog>
  );
}

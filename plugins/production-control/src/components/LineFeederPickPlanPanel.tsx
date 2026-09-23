import { createDashboardStatusBadge, HelpTooltip } from "@delpi/plugin-ui/index";
import { CheckCheck, ClipboardList, Lock } from "lucide-react";

import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import type {
  LineFeederItemStatus,
  LineFeederPickItem,
  LineFeederPickPlan,
  LineFeederStatusMeta,
} from "../types";
import { formatOpQuantity } from "../utils/formatOpQuantity";
import { formatRefreshedAt } from "../utils/formatRefreshedAt";
import { nextPickItemStatus, pickItemBadgeVariant } from "../utils/lineFeederStatus";

const StatusBadge = createDashboardStatusBadge({ prefix: "ppc" });

type LineFeederPickPlanPanelProps = {
  plans: LineFeederPickPlan[];
  selected: LineFeederPickPlan | null;
  items: LineFeederPickItem[];
  itemStatuses: Record<string, LineFeederStatusMeta>;
  busyItemId: string | null;
  closing: boolean;
  error: string | null;
  onSelect: (planId: string) => void;
  onItemStatusChange: (item: LineFeederPickItem, status: LineFeederItemStatus) => void;
  onClose: (planId: string) => void;
};

function statusLabel(
  statuses: Record<string, LineFeederStatusMeta>,
  status: string,
  fallback: string,
): string {
  return statuses[status]?.label ?? fallback;
}

export function LineFeederPickPlanPanel({
  plans,
  selected,
  items,
  itemStatuses,
  busyItemId,
  closing,
  error,
  onSelect,
  onItemStatusChange,
  onClose,
}: LineFeederPickPlanPanelProps) {
  const texts = copy.lineFeeder.pickPlan;
  const closed = selected?.status === "closed";

  return (
    <section className="ppc-pick" aria-label={texts.title}>
      <header className="ppc-pick__head">
        <h2 className="ppc-pick__title">
          <ClipboardList size={18} strokeWidth={1.75} aria-hidden />
          {texts.title}
          <HelpTooltip content={helpTooltips.lineFeederPickPlan} trigger="icon" />
        </h2>
        <p className="ppc-pick__hint">{texts.hint}</p>
      </header>

      {error ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {error}
        </div>
      ) : null}

      {plans.length === 0 ? (
        <p className="ppc-state">{texts.empty}</p>
      ) : (
        <>
          <div className="ppc-pick__plans" role="tablist" aria-label={texts.history}>
            {plans.map((plan) => (
              <button
                key={plan.id}
                type="button"
                role="tab"
                className="ppc-pick__plan"
                data-active={plan.id === selected?.id ? "true" : undefined}
                data-status={plan.status}
                aria-selected={plan.id === selected?.id}
                aria-label={`${texts.selectAria} — ${formatRefreshedAt(plan.cutoff_at)}`}
                onClick={() => onSelect(plan.id)}
              >
                <span className="ppc-pick__plan-cutoff">
                  {texts.cutoff(formatRefreshedAt(plan.cutoff_at))}
                </span>
                <span className="ppc-pick__plan-meta">
                  {plan.work_center ?? texts.workCenterAll} ·{" "}
                  {texts.progress(plan.delivered_count, plan.item_count)}
                </span>
                <StatusBadge
                  label={plan.status === "closed" ? texts.closedLabel : texts.openLabel}
                  variant={plan.status === "closed" ? "neutral" : "info"}
                />
              </button>
            ))}
          </div>

          {selected ? (
            <div className="ppc-pick__body">
              <div className="ppc-pick__toolbar">
                <span className="ppc-pick__progress">
                  {texts.progress(selected.delivered_count, selected.item_count)} ·{" "}
                  {formatOpQuantity(selected.to_deliver_qty)}
                </span>
                {closed ? (
                  <span className="ppc-pick__closed">
                    <Lock size={14} strokeWidth={1.75} aria-hidden />
                    {texts.closed}
                  </span>
                ) : (
                  <button
                    type="button"
                    className="ppc-icon-btn"
                    onClick={() => onClose(selected.id)}
                    disabled={closing}
                  >
                    <CheckCheck size={16} strokeWidth={1.75} aria-hidden />
                    <span>{closing ? texts.closing : texts.close}</span>
                  </button>
                )}
              </div>

              {items.length === 0 ? (
                <p className="ppc-state">{texts.itemsEmpty}</p>
              ) : (
                <ul className="ppc-pick__items">
                  {items.map((item) => (
                    <li key={item.id} className="ppc-pick__item" data-status={item.status}>
                      <div className="ppc-pick__item-identity">
                        <span className="ppc-pick__item-product">{item.product_code}</span>
                        <span className="ppc-pick__item-description">{item.description}</span>
                        <span className="ppc-pick__item-meta">
                          {texts.pickupLocation}:{" "}
                          {item.pickup_location.trim()
                            ? item.pickup_location
                            : texts.pickupLocationEmpty}
                        </span>
                      </div>
                      <span className="ppc-pick__item-qty">
                        {formatOpQuantity(item.to_deliver_qty)} {item.unit}
                      </span>
                      <button
                        type="button"
                        className="ppc-pick__item-action"
                        data-status={item.status}
                        disabled={closed || busyItemId === item.id}
                        aria-label={`${statusLabel(itemStatuses, item.status, item.status)} — ${item.product_code}`}
                        onClick={() =>
                          onItemStatusChange(item, nextPickItemStatus(item.status))
                        }
                      >
                        <StatusBadge
                          label={statusLabel(itemStatuses, item.status, item.status)}
                          variant={pickItemBadgeVariant(item.status)}
                        />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ) : null}
        </>
      )}
    </section>
  );
}

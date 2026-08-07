import { ActionButton, HelpTooltip, StatusBadge } from "@delpi/plugin-ui/index";

import { cmStatusBadgeClassNames } from "../app/commercialUi";
import { CM_HELP } from "../content/helpTooltips";
import type { ProductionOrderByOpData } from "../types/productionExtras";
import { formatDisplayDate } from "../utils/dates";
import { displayApiScalar } from "../utils/displayApiScalar";
import {
  buildProductionOtdOrderPath,
  formatOtdDaysDiff,
  formatOtdStatusLabel,
  linkedPiOrders,
  otdStatusBadgeVariant,
  parseProductionLinkSummary,
} from "../utils/productionOtdLink";

type OpenOrdersOtdPiPanelProps = {
  productionOrder: string;
  branch?: string | null;
  byOp?: ProductionOrderByOpData | null;
};

function openProductionOtd(
  productionOrder: string,
  options?: { branch?: string | null; productType?: string | null },
): void {
  const path = buildProductionOtdOrderPath(productionOrder, options);
  if (!path || typeof window === "undefined") return;
  window.location.assign(path);
}

/**
 * Bloco compacto: prazo OTD da OP + resumo/lista de PIs + deep link produção.
 */
export function OpenOrdersOtdPiPanel({
  productionOrder,
  branch,
  byOp,
}: OpenOrdersOtdPiPanelProps) {
  if (!byOp?.order) return null;

  const order = byOp.order;
  const summary = parseProductionLinkSummary(byOp.link_summary);
  const pis = linkedPiOrders(byOp.linked_orders, 5);
  const totalPi = summary?.total_pi_orders ?? pis.length;
  const onTime = summary?.on_time_ops ?? null;
  const late = summary?.late_ops ?? null;
  const open = summary?.open_ops ?? null;
  const help = CM_HELP.openOrders.detail;
  const resolvedBranch = order.branch || branch || null;
  const otdHref = buildProductionOtdOrderPath(productionOrder, {
    branch: resolvedBranch,
    productType: order.product_type,
  });

  const summaryLine = (() => {
    if (totalPi <= 0 && pis.length === 0) return null;
    const parts: string[] = [];
    if (onTime != null) parts.push(`${onTime} no prazo`);
    if (late != null) parts.push(`${late} atrasadas`);
    if (open != null) parts.push(`${open} em aberto`);
    if (summary?.order_number) parts.push(`Nº OP ${summary.order_number}`);
    if (parts.length === 0) return `${totalPi || pis.length} OP(s) vinculada(s)`;
    return parts.join(" · ");
  })();

  return (
    <div className="cm-open-orders-detail__otd-pi">
      <div className="cm-open-orders-detail__otd-pi-head">
        <div className="cm-open-orders-detail__otd-pi-title-row">
          <p className="cm-open-orders-detail__otd-pi-title">Prazo OTD</p>
          <HelpTooltip content={help.otdPrazo} ariaLabel="Ajuda: prazo OTD" />
        </div>
        {otdHref ? (
          <ActionButton
            variant="ghost"
            className="cm-open-orders-detail__otd-pi-cta"
            onClick={() =>
              openProductionOtd(productionOrder, {
                branch: resolvedBranch,
                productType: order.product_type,
              })
            }
          >
            Ver no OTD produção
          </ActionButton>
        ) : null}
      </div>

      <div className="cm-open-orders-detail__otd-pi-kpis">
        <div className="cm-open-orders-detail__otd-pi-kpi">
          <span className="cm-open-orders-detail__otd-pi-kpi-label">Status OTD</span>
          <StatusBadge
            classNames={cmStatusBadgeClassNames}
            label={formatOtdStatusLabel(order.otd_status)}
            variant={otdStatusBadgeVariant(order.otd_status)}
          />
        </div>
        <div className="cm-open-orders-detail__otd-pi-kpi">
          <span className="cm-open-orders-detail__otd-pi-kpi-label">Dias (previsto × real)</span>
          <strong className="cm-open-orders-detail__otd-pi-kpi-value">
            {formatOtdDaysDiff(order.days_diff)}
          </strong>
        </div>
        <div className="cm-open-orders-detail__otd-pi-kpi">
          <span className="cm-open-orders-detail__otd-pi-kpi-label">Entrega prevista</span>
          <strong className="cm-open-orders-detail__otd-pi-kpi-value">
            {formatDisplayDate(order.due_date)}
          </strong>
        </div>
        <div className="cm-open-orders-detail__otd-pi-kpi">
          <span className="cm-open-orders-detail__otd-pi-kpi-label">Finalização</span>
          <strong className="cm-open-orders-detail__otd-pi-kpi-value">
            {formatDisplayDate(order.finish_date)}
          </strong>
        </div>
      </div>

      {summaryLine || pis.length > 0 ? (
        <div className="cm-open-orders-detail__otd-pi-linked">
          <div className="cm-open-orders-detail__otd-pi-title-row">
            <p className="cm-open-orders-detail__otd-pi-title">OPs de PI vinculadas</p>
            <HelpTooltip content={help.otdLinkedPi} ariaLabel="Ajuda: OPs de PI" />
          </div>
          {summaryLine ? (
            <p className="cm-open-orders-detail__muted cm-open-orders-detail__otd-pi-summary">
              {summaryLine}
            </p>
          ) : null}
          {pis.length > 0 ? (
            <ul className="cm-open-orders-detail__otd-pi-list">
              {pis.map((row) => {
                const opId = String(row.production_order || "").trim();
                return (
                  <li key={opId} className="cm-open-orders-detail__otd-pi-row">
                    <StatusBadge
                      classNames={cmStatusBadgeClassNames}
                      label={formatOtdStatusLabel(row.otd_status)}
                      variant={otdStatusBadgeVariant(row.otd_status)}
                    />
                    <button
                      type="button"
                      className="cm-open-orders-detail__otd-pi-link"
                      onClick={() =>
                        openProductionOtd(opId, {
                          branch: row.branch || resolvedBranch,
                          productType: row.product_type || "PI",
                        })
                      }
                    >
                      {opId}
                    </button>
                    <span className="cm-open-orders-detail__otd-pi-code">
                      {displayApiScalar(row.product_code, "—")}
                    </span>
                    <span className="cm-open-orders-detail__muted">
                      Prev. {formatDisplayDate(row.due_date)} · Dias{" "}
                      {formatOtdDaysDiff(row.days_diff)}
                    </span>
                  </li>
                );
              })}
            </ul>
          ) : null}
          {totalPi != null && totalPi > pis.length ? (
            <p className="cm-open-orders-detail__muted">
              +{totalPi - pis.length} OP(s) — abra no OTD produção para a lista completa.
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

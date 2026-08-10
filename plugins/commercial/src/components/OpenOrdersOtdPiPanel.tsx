import { SectionHintLabel, StatusBadge } from "@delpi/plugin-ui/index";

import { cmStatusBadgeClassNames } from "../app/commercialUi";
import { CM_HELP } from "../content/helpTooltips";
import type { ProductionOrderByOpData } from "../types/productionExtras";
import { formatDisplayDate } from "../utils/dates";
import { displayApiScalar } from "../utils/displayApiScalar";
import { formatQuantity } from "../utils/format";
import {
  formatOtdDaysDiff,
  formatOtdStatusLabel,
  linkedPiOrders,
  otdStatusBadgeVariant,
  parseProductionLinkSummary,
} from "../utils/productionOtdLink";

type OpenOrdersOtdPiPanelProps = {
  byOp?: ProductionOrderByOpData | null;
};

/**
 * Bloco compacto: prazo OTD da OP + tabela densa de PIs.
 */
export function OpenOrdersOtdPiPanel({
  byOp,
}: OpenOrdersOtdPiPanelProps) {
  if (!byOp?.order) return null;

  const order = byOp.order;
  const summary = parseProductionLinkSummary(byOp.link_summary);
  const pis = linkedPiOrders(byOp.linked_orders, 8);
  const totalPi = summary?.total_pi_orders ?? pis.length;
  const onTime = summary?.on_time_ops ?? null;
  const late = summary?.late_ops ?? null;
  const open = summary?.open_ops ?? null;
  const help = CM_HELP.openOrders.detail;

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
        <SectionHintLabel
          label="Prazo OTD"
          hint={help.otdPrazo}
          className="cm-open-orders-detail__otd-pi-title"
        />
      </div>

      <div className="cm-open-orders-detail__otd-pi-kpis">
        <div className="cm-open-orders-detail__otd-pi-kpi">
          <SectionHintLabel
            label="Status OTD"
            hint={help.otdStatus}
            className="cm-open-orders-detail__otd-pi-kpi-label"
          />
          <StatusBadge
            classNames={cmStatusBadgeClassNames}
            label={formatOtdStatusLabel(order.otd_status)}
            variant={otdStatusBadgeVariant(order.otd_status)}
          />
        </div>
        <div className="cm-open-orders-detail__otd-pi-kpi">
          <SectionHintLabel
            label="Dias (previsto × real)"
            hint={help.otdDays}
            className="cm-open-orders-detail__otd-pi-kpi-label"
          />
          <strong className="cm-open-orders-detail__otd-pi-kpi-value">
            {formatOtdDaysDiff(order.days_diff)}
          </strong>
        </div>
        <div className="cm-open-orders-detail__otd-pi-kpi">
          <SectionHintLabel
            label="Entrega prevista"
            hint={help.otdDue}
            className="cm-open-orders-detail__otd-pi-kpi-label"
          />
          <strong className="cm-open-orders-detail__otd-pi-kpi-value">
            {formatDisplayDate(order.due_date)}
          </strong>
        </div>
        <div className="cm-open-orders-detail__otd-pi-kpi">
          <SectionHintLabel
            label="Finalização"
            hint={help.otdFinish}
            className="cm-open-orders-detail__otd-pi-kpi-label"
          />
          <strong className="cm-open-orders-detail__otd-pi-kpi-value">
            {formatDisplayDate(order.finish_date)}
          </strong>
        </div>
      </div>

      {summaryLine || pis.length > 0 ? (
        <div className="cm-open-orders-detail__otd-pi-linked">
          <SectionHintLabel
            label="OPs de PI vinculadas"
            hint={help.otdLinkedPi}
            className="cm-open-orders-detail__otd-pi-title"
          />
          {summaryLine ? (
            <p className="cm-open-orders-detail__muted cm-open-orders-detail__otd-pi-summary">
              {summaryLine}
            </p>
          ) : null}
          {pis.length > 0 ? (
            <div className="cm-open-orders-detail__otd-pi-table-wrap">
              <table className="cm-open-orders-detail__otd-pi-table">
                <thead>
                  <tr>
                    <th scope="col">
                      <SectionHintLabel label="Status" hint={help.otdStatus} />
                    </th>
                    <th scope="col">
                      <SectionHintLabel label="OP" hint={help.opNumero} />
                    </th>
                    <th scope="col">Código</th>
                    <th scope="col">
                      <SectionHintLabel label="Previsto" hint={help.otdDue} />
                    </th>
                    <th scope="col">
                      <SectionHintLabel label="Dias" hint={help.otdDays} />
                    </th>
                    <th scope="col">
                      <SectionHintLabel label="Qtd" hint={help.opPlanejado} />
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {pis.map((row) => {
                    const opId = String(row.production_order || "").trim();
                    return (
                      <tr key={opId}>
                        <td>
                          <StatusBadge
                            classNames={cmStatusBadgeClassNames}
                            label={formatOtdStatusLabel(row.otd_status)}
                            variant={otdStatusBadgeVariant(row.otd_status)}
                          />
                        </td>
                        <td>{opId}</td>
                        <td>{displayApiScalar(row.product_code, "—")}</td>
                        <td>{formatDisplayDate(row.due_date)}</td>
                        <td>{formatOtdDaysDiff(row.days_diff)}</td>
                        <td>{formatQuantity(row.planned_qty)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : null}
          {totalPi != null && totalPi > pis.length ? (
            <p className="cm-open-orders-detail__muted">
              +{totalPi - pis.length} OP(s) vinculada(s) fora deste resumo.
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

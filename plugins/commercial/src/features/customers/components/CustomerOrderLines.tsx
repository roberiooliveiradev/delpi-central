import type { DataTableColumn } from "@delpi/plugin-ui/index";

import {
  CommercialActionButton,
  CommercialDataRecordCard,
  CommercialDataTable,
} from "../../../app/commercialUi";
import { formatCurrency } from "../../../utils/format";
import { formatDisplayDate, getDeliveryOverdueDays, isDeliveryOverdue } from "../../../utils/dates";
import type { OpenOrdersTotvsItem } from "../../../types/openOrdersTotvs";
import { toFiniteNumber } from "../utils/customerAggregation";
import {
  navigateAnalyticsOpportunityDetail,
  navigateOpenOrderLineDetail,
  navigateOpenOrderOpDetail,
} from "../../../app/pluginNavigation";
import { buildOpenOrdersContextSearch } from "../../../utils/openOrdersDeepLink";
import { getLineOpForecast } from "../../../utils/opAllocation";
import { buildOrderOpportunityContextSearch } from "../utils/customerAccountActions";

type CustomerOrderLinesProps = {
  lines: readonly OpenOrdersTotvsItem[];
  orderKey: string;
  basePath: string;
  canViewAnalytics: boolean;
  /** Quando definido, deep links de linha/OP voltam para esta origem. */
  returnNav?: { returnTo?: string | null; returnLabel?: string | null };
};

function lineOverdueLabel(item: OpenOrdersTotvsItem): string {
  const saldo = toFiniteNumber(item.saldo);
  if (!isDeliveryOverdue(item.data_entrega, saldo)) return "Em dia";
  const days = getDeliveryOverdueDays(item.data_entrega) ?? 0;
  if (days <= 0) return "Atrasado";
  if (days === 1) return "Atrasado (1 dia)";
  return `Atrasado (${days.toLocaleString("pt-BR")} dias)`;
}

export function CustomerOrderLines({
  lines,
  orderKey,
  basePath,
  canViewAnalytics,
  returnNav,
}: CustomerOrderLinesProps) {
  const regionId = `cm-order-lines-${orderKey.replace(/\|/g, "-")}`;
  const rows = Array.from(lines);
  const rowKey = (line: OpenOrdersTotvsItem, index: number) =>
    `${orderKey}-${line.linha ?? index}-${line.produto ?? ""}`;
  const actions = (line: OpenOrdersTotvsItem) => {
    const canOpenOrder = Boolean(
      line.filial?.trim() && line.pedido?.trim() && line.linha?.trim(),
    );
    const productionOrders = canOpenOrder
      ? Array.from(
          new Map(
            getLineOpForecast(line).opsUtilizadas
              .filter((op) => op.numero_op.trim())
              .map((op) => [op.numero_op.trim(), op]),
          ).values(),
        )
      : [];
    const proposalNumber = line.proposal_number?.trim() || null;
    if (
      !canOpenOrder &&
      productionOrders.length === 0 &&
      !(canViewAnalytics && proposalNumber)
    ) {
      return null;
    }
    return (
      <div className="cm-customer-order-line-actions">
        {canOpenOrder ? (
          <CommercialActionButton
            variant="ghost"
            onClick={() =>
              navigateOpenOrderLineDetail(
                line.filial,
                line.pedido,
                line.linha,
                {
                  basePath,
                  search: buildOpenOrdersContextSearch(),
                  returnNav,
                },
              )
            }
          >
            Ver em Pedidos
          </CommercialActionButton>
        ) : null}
        {productionOrders.map((op) => (
          <CommercialActionButton
            key={op.numero_op}
            variant="ghost"
            onClick={() =>
              navigateOpenOrderOpDetail(
                line.filial,
                line.pedido,
                line.linha,
                op.numero_op,
                {
                  basePath,
                  search: buildOpenOrdersContextSearch(),
                  returnNav,
                },
              )
            }
          >
            Ver OP {op.numero_op}
          </CommercialActionButton>
        ))}
        {canViewAnalytics && proposalNumber ? (
          <CommercialActionButton
            variant="ghost"
            onClick={() =>
              navigateAnalyticsOpportunityDetail(proposalNumber, {
                basePath,
                search: buildOrderOpportunityContextSearch(line),
              })
            }
          >
            Ver OV {proposalNumber}
          </CommercialActionButton>
        ) : null}
      </div>
    );
  };
  const columns: DataTableColumn<OpenOrdersTotvsItem>[] = [
    { key: "product", header: "Produto", render: (line) => line.produto?.trim() || "—" },
    {
      key: "ordered",
      header: "Pedida",
      align: "right",
      render: (line) => toFiniteNumber(line.quantidade).toLocaleString("pt-BR"),
    },
    {
      key: "delivered",
      header: "Entregue",
      align: "right",
      render: (line) => toFiniteNumber(line.entregue).toLocaleString("pt-BR"),
    },
    {
      key: "balance",
      header: "Saldo",
      align: "right",
      render: (line) => toFiniteNumber(line.saldo).toLocaleString("pt-BR"),
    },
    {
      key: "delivery",
      header: "Entrega",
      render: (line) => formatDisplayDate(line.data_entrega),
    },
    {
      key: "open-value",
      header: "Valor aberto",
      align: "right",
      render: (line) => formatCurrency(toFiniteNumber(line.valor_aberto)),
    },
    { key: "delay", header: "Atraso", render: lineOverdueLabel },
    { key: "actions", header: "Ação", render: actions },
  ];

  return (
    <div
      id={regionId}
      className="cm-customer-order-lines"
      role="region"
      aria-label="Linhas do pedido"
    >
      <div className="cm-customer-order-lines__desktop">
        <CommercialDataTable
          rows={rows}
          columns={columns}
          rowKey={rowKey}
          layout="section"
        />
      </div>
      <div className="cm-customer-order-lines__mobile">
        {rows.map((line, index) => (
          <CommercialDataRecordCard
            key={rowKey(line, index)}
            title={line.produto?.trim() || "Produto não informado"}
            subtitle={`Entrega ${formatDisplayDate(line.data_entrega)}`}
            status={lineOverdueLabel(line)}
            fields={[
              { id: "ordered", label: "Pedida", value: toFiniteNumber(line.quantidade).toLocaleString("pt-BR") },
              { id: "delivered", label: "Entregue", value: toFiniteNumber(line.entregue).toLocaleString("pt-BR") },
              { id: "balance", label: "Saldo", value: toFiniteNumber(line.saldo).toLocaleString("pt-BR") },
              { id: "open-value", label: "Valor aberto", value: formatCurrency(toFiniteNumber(line.valor_aberto)) },
            ]}
            context={actions(line)}
          />
        ))}
      </div>
    </div>
  );
}

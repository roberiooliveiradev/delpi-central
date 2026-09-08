import type { DataTableColumn } from "@delpi/plugin-ui/index";

import {
  CommercialDataRecordCard,
  CommercialDataTable,
  CommercialEntityLink,
  CommercialSectionHintLabel,
  CommercialSegmentToggle,
  cmDataTableClassNames,
} from "../../../app/commercialUi";
import { CM_HELP } from "../../../content/helpTooltips";
import { useQuantityDisplayMode } from "../../../hooks/useQuantityDisplayMode";
import {
  CUSTOMER_ORDER_LINES_COLUMN_HELP,
  withColumnHelp,
} from "../../../utils/customersColumnHelp";
import { formatCurrency, formatQuantity } from "../../../utils/format";
import {
  formatDisplayQuantity,
  resolveDisplayQuantity,
} from "../../../utils/displayQuantity";
import { formatDisplayDate, getDeliveryOverdueDays, isDeliveryOverdue } from "../../../utils/dates";
import { tableColumnLabel } from "../../../utils/tableColumns";
import type { OpenOrdersTotvsItem } from "../../../types/openOrdersTotvs";
import { toFiniteNumber } from "../utils/customerAggregation";
import {
  buildAnalyticsOpportunityDetailHref,
  buildOpenOrderLineDetailPath,
  buildOpenOrderOpDetailPath,
  navigateAnalyticsOpportunityDetail,
  navigateOpenOrderLineDetail,
  navigateOpenOrderOpDetail,
} from "../../../app/pluginNavigation";
import { buildHrefWithReturn } from "../../../app/commercialNavigationReturn";
import {
  openOrderLineLinkTitle,
  opPageLinkTitle,
  opportunityLinkTitle,
} from "../../../content/entityLinkHints";
import { buildOpenOrdersContextSearch } from "../../../utils/openOrdersDeepLink";
import { getLineOpForecast } from "../../../utils/opAllocation";
import { buildOrderOpportunityContextSearch } from "../utils/customerAccountActions";

const numericColClass = cmDataTableClassNames.colNumeric;
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
  const { mode, setMode } = useQuantityDisplayMode();
  const regionId = `cm-order-lines-${orderKey.replace(/\|/g, "-")}`;
  const rows = Array.from(lines);
  const rowKey = (line: OpenOrdersTotvsItem, index: number) =>
    `${orderKey}-${line.linha ?? index}-${line.produto ?? ""}`;
  const withReturn = (path: string | null) => {
    if (!path) return null;
    if (!returnNav) return path;
    return buildHrefWithReturn(path, returnNav, basePath);
  };
  const formatLineQty = (qty: number | null | undefined, unit: string | null | undefined) =>
    formatQuantity(resolveDisplayQuantity(qty, unit, mode).value);
  const formatLineUnit = (qty: number | null | undefined, unit: string | null | undefined) =>
    resolveDisplayQuantity(qty, unit, mode).unit;

  const actions = (line: OpenOrdersTotvsItem) => {
    const canOpenOrder = Boolean(
      line.filial?.trim() && line.pedido?.trim() && line.linha?.trim(),
    );
    const contextSearch = buildOpenOrdersContextSearch();
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
    const lineHref = canOpenOrder
      ? withReturn(
          buildOpenOrderLineDetailPath(
            basePath,
            line.filial,
            line.pedido,
            line.linha,
            contextSearch,
          ),
        )
      : null;
    if (
      !lineHref &&
      productionOrders.length === 0 &&
      !(canViewAnalytics && proposalNumber)
    ) {
      return null;
    }
    return (
      <div className="cm-customer-order-line-actions">
        {lineHref ? (
          <CommercialEntityLink
            href={lineHref}
            title={openOrderLineLinkTitle(line.pedido, line.linha)}
            className="cm-link-button"
            onNavigate={() =>
              navigateOpenOrderLineDetail(line.filial, line.pedido, line.linha, {
                basePath,
                search: contextSearch,
                returnNav,
              })
            }
          >
            Ver em Pedidos
          </CommercialEntityLink>
        ) : null}
        {productionOrders.map((op) => {
          const opHref = withReturn(
            buildOpenOrderOpDetailPath(
              basePath,
              line.filial,
              line.pedido,
              line.linha,
              op.numero_op,
              contextSearch,
            ),
          );
          if (!opHref) return null;
          return (
            <CommercialEntityLink
              key={op.numero_op}
              href={opHref}
              title={opPageLinkTitle(op.numero_op)}
              className="cm-link-button"
              onNavigate={() =>
                navigateOpenOrderOpDetail(
                  line.filial,
                  line.pedido,
                  line.linha,
                  op.numero_op,
                  {
                    basePath,
                    search: contextSearch,
                    returnNav,
                  },
                )
              }
            >
              Ver OP {op.numero_op}
            </CommercialEntityLink>
          );
        })}
        {canViewAnalytics && proposalNumber
          ? (() => {
              const ovHref = buildAnalyticsOpportunityDetailHref(proposalNumber, {
                basePath,
                search: buildOrderOpportunityContextSearch(line),
              });
              if (!ovHref) return null;
              return (
                <CommercialEntityLink
                  href={ovHref}
                  title={opportunityLinkTitle(proposalNumber)}
                  className="cm-link-button"
                  onNavigate={() =>
                    navigateAnalyticsOpportunityDetail(proposalNumber, {
                      basePath,
                      search: buildOrderOpportunityContextSearch(line),
                    })
                  }
                >
                  Ver OV {proposalNumber}
                </CommercialEntityLink>
              );
            })()
          : null}
      </div>
    );
  };
  const columns: DataTableColumn<OpenOrdersTotvsItem>[] = [
    { key: "product", header: "Produto", render: (line) => line.produto?.trim() || "—" },
    {
      key: "ordered",
      header: "Pedida",
      align: "right",
      className: numericColClass,
      render: (line) => formatLineQty(line.quantidade, line.unidade),
    },
    {
      key: "delivered",
      header: "Entregue",
      align: "right",
      className: numericColClass,
      render: (line) => formatLineQty(line.entregue, line.unidade),
    },
    {
      key: "balance",
      header: "Saldo",
      align: "right",
      className: numericColClass,
      render: (line) => formatLineQty(line.saldo, line.unidade),
    },
    {
      key: "unit",
      header: "UM",
      className: numericColClass,
      render: (line) => formatLineUnit(line.quantidade, line.unidade),
    },
    {
      key: "delivery",
      header: tableColumnLabel("data_entrega"),
      render: (line) => formatDisplayDate(line.data_entrega),
    },
    {
      key: "open-value",
      header: "Valor aberto",
      align: "right",
      className: numericColClass,
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
      <div className="cm-customer-order-lines__display-mode">
        <CommercialSectionHintLabel
          label="Exibir quantidade"
          hint={CM_HELP.customers.quantityDisplayMode}
        />
        <CommercialSegmentToggle
          ariaLabel={CM_HELP.customers.quantityDisplayMode}
          idPrefix={`order-lines-qty-${orderKey.replace(/\|/g, "-")}`}
          value={mode}
          widthMode="content"
          onChange={(value) => {
            if (value === "catalog" || value === "pieces") setMode(value);
          }}
          options={[
            { value: "catalog", label: "Milheiro" },
            { value: "pieces", label: "Peças" },
          ]}
        />
      </div>
      <div className="cm-customer-order-lines__desktop">
        <CommercialDataTable
          rows={rows}
          columns={withColumnHelp(columns, CUSTOMER_ORDER_LINES_COLUMN_HELP)}
          rowKey={rowKey}
          layout="section"
        />
      </div>
      <div className="cm-customer-order-lines__mobile">
        {rows.map((line, index) => (
          <CommercialDataRecordCard
            key={rowKey(line, index)}
            title={line.produto?.trim() || "Produto não informado"}
            subtitle={`Entrega ${formatDisplayDate(line.data_entrega)} · UM ${formatLineUnit(line.quantidade, line.unidade)}`}
            status={lineOverdueLabel(line)}
            fields={[
              {
                id: "ordered",
                label: "Pedida",
                value: formatDisplayQuantity(line.quantidade, line.unidade, mode),
              },
              {
                id: "delivered",
                label: "Entregue",
                value: formatDisplayQuantity(line.entregue, line.unidade, mode),
              },
              {
                id: "balance",
                label: "Saldo",
                value: formatDisplayQuantity(line.saldo, line.unidade, mode),
              },
              {
                id: "open-value",
                label: "Valor aberto",
                value: formatCurrency(toFiniteNumber(line.valor_aberto)),
              },
            ]}
            context={actions(line)}
          />
        ))}
      </div>
    </div>
  );
}

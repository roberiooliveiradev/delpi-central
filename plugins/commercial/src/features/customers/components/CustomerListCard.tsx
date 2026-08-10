import type { KeyboardEvent, MouseEvent, ReactNode } from "react";

import {
  CommercialDataCellValue,
  CommercialInteractiveDataCard,
  CommercialStatusBadge,
} from "../../../app/commercialUi";
import { CM_HELP } from "../../../content/helpTooltips";
import { formatDisplayDate } from "../../../utils/dates";
import { formatEntityCodeStore } from "../../../utils/entityCodeStore";
import { formatCurrency } from "../../../utils/format";
import type { CustomerSummary } from "../types/customerSummary";
import { hasCustomerEnrichmentCoverage } from "../utils/customerEnrichmentCoverage";
import {
  resolveCustomerStatus,
  statusLabel,
} from "../utils/customerListPresentation";
import type { CustomerColumnKey } from "../utils/customerTableColumns";
import { BillingTrendCell } from "./BillingTrendCell";
import { CustomerAvatar } from "./CustomerAvatar";

type CustomerListCardProps = {
  customer: CustomerSummary;
  visibleColumns: ReadonlyArray<{ key: CustomerColumnKey; label: string }>;
  onOpenDetail: (customer: CustomerSummary) => void;
};

function stopCardBubble(event: MouseEvent | KeyboardEvent) {
  event.stopPropagation();
}

function statusVariant(
  status: ReturnType<typeof resolveCustomerStatus>,
): "success" | "warning" | "neutral" {
  if (status === "ativo") return "success";
  if (status === "atencao") return "warning";
  return "neutral";
}

function renderCardValue(
  key: CustomerColumnKey,
  customer: CustomerSummary,
  onOpenDetail: (customer: CustomerSummary) => void,
): ReactNode {
  const name = customer.nome?.trim() || "—";
  const codeStore =
    formatEntityCodeStore(customer.codigo, customer.loja) ??
    `${customer.codigo}-${customer.loja}`;
  const covered = hasCustomerEnrichmentCoverage(customer);

  switch (key) {
    case "nome":
      return (
        <div className="cm-open-orders-client">
          <CustomerAvatar
            code={customer.codigo}
            store={customer.loja}
            name={name}
            hasAvatar={Boolean(customer.hasAvatar)}
            size="sm"
          />
          <div className="cm-open-orders-client__text">
            <button
              type="button"
              className="cm-open-orders-client__name"
              onClick={(event) => {
                stopCardBubble(event);
                onOpenDetail(customer);
              }}
              onKeyDown={stopCardBubble}
            >
              {name}
            </button>
            <span className="cm-open-orders-client__id">{codeStore}</span>
          </div>
        </div>
      );
    case "sellerName":
      return customer.sellerName?.trim() || "—";
    case "city":
      return (
        <CommercialDataCellValue
          value={
            customer.city || customer.state
              ? [customer.city, customer.state].filter(Boolean).join(" / ")
              : null
          }
          present={covered}
        />
      );
    case "lastPurchaseDate":
      return (
        <CommercialDataCellValue
          value={
            customer.lastPurchaseDate
              ? formatDisplayDate(customer.lastPurchaseDate)
              : null
          }
          present={covered}
        />
      );
    case "billed12m":
      return (
        <CommercialDataCellValue
          value={customer.billed12m == null ? null : formatCurrency(customer.billed12m)}
          present={covered}
        />
      );
    case "billingTrend":
      return (
        <BillingTrendCell
          trend={customer.billingTrend}
          pct={customer.billingTrendPct}
          covered={covered}
        />
      );
    case "status": {
      const status = customer.status ?? resolveCustomerStatus(customer);
      return (
        <CommercialStatusBadge
          label={statusLabel(status)}
          variant={statusVariant(status)}
        />
      );
    }
    case "valorTotalAberto":
      return formatCurrency(customer.valorTotalAberto);
    case "quantidadePedidosAtrasados":
      return customer.quantidadePedidosAtrasados.toLocaleString("pt-BR");
    case "proximaEntrega":
      return formatDisplayDate(customer.proximaEntrega);
    default:
      return "—";
  }
}

export function CustomerListCard({
  customer,
  visibleColumns,
  onOpenDetail,
}: CustomerListCardProps) {
  const openDetail = () => onOpenDetail(customer);
  const name = customer.nome?.trim() || customer.codigo || "cliente";

  return (
    <CommercialInteractiveDataCard
      ariaLabel={`${CM_HELP.customers.cardAriaOpen}: ${name}`}
      onActivate={openDetail}
      openHint={CM_HELP.customers.cardOpenHint}
      fields={visibleColumns.map((column) => {
        const isTitle = column.key === "nome";
        const isValue =
          column.key === "valorTotalAberto" || column.key === "billed12m";
        return {
          id: column.key,
          label: column.label,
          hint:
            column.key === "billingTrend" ? CM_HELP.customers.trend : undefined,
          valueTone: isTitle ? "title" : isValue ? "value" : "meta",
          value: renderCardValue(column.key, customer, onOpenDetail),
        };
      })}
    />
  );
}

import type { KeyboardEvent, ReactNode } from "react";
import { FieldLabel, StatusBadge } from "@delpi/plugin-ui/index";

import {
  CommercialInlineMeter,
  cmStatusBadgeClassNames,
} from "../app/commercialUi";
import { CM_HELP } from "../content/helpTooltips";
import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";
import { formatDisplayDate, getDeliveryOverdueDays } from "../utils/dates";
import { formatCurrency, formatQuantity } from "../utils/format";
import { openOrdersColumnHelp } from "../utils/openOrdersColumnHelp";
import {
  resolveLineCoverage,
  resolvePrevisaoPrazoBadge,
} from "../utils/openOrdersLineVisual";
import { getLineOpForecast } from "../utils/opAllocation";
import { getAllocatedStock } from "../utils/stockAllocation";
import { getLineStatus } from "../utils/statusBadges";
import { TABLE_COLUMNS, type TableColumnKey } from "../utils/tableColumns";

type OpenOrdersLineCardProps = {
  item: OpenOrdersTotvsItem;
  visibleKeys: ReadonlySet<TableColumnKey>;
  onOpenDetail: (item: OpenOrdersTotvsItem) => void;
};

function badgeVariant(
  tone: ReturnType<typeof getLineStatus>["tone"],
): "neutral" | "info" | "success" | "warning" | "danger" {
  if (tone === "success") return "success";
  if (tone === "warning") return "warning";
  if (tone === "danger") return "danger";
  if (tone === "info") return "info";
  return "neutral";
}

function CardField({
  columnKey,
  label,
  children,
  valueClassName,
}: {
  columnKey: TableColumnKey;
  label: string;
  children: ReactNode;
  valueClassName?: string;
}) {
  return (
    <div className="cm-open-orders-card__field">
      <FieldLabel
        label={label}
        hint={openOrdersColumnHelp(columnKey)}
        className="cm-open-orders-card__field-label"
      />
      <div className={valueClassName ?? "cm-open-orders-card__meta"}>{children}</div>
    </div>
  );
}

function renderCardValue(key: TableColumnKey, item: OpenOrdersTotvsItem): ReactNode {
  switch (key) {
    case "nome_cliente":
      return item.nome_cliente || "—";
    case "loja_cadastro":
      return item.loja_cadastro || "—";
    case "filial":
      return item.filial || "—";
    case "pedido":
      return `${item.pedido || "—"} · Linha ${item.linha || "—"}`;
    case "pedido_cliente":
      return item.pedido_cliente || "—";
    case "produto":
      return item.produto || "—";
    case "codigo_cliente":
      return item.codigo_cliente || "—";
    case "quantidade":
      return formatQuantity(item.quantidade);
    case "entregue":
      return formatQuantity(item.entregue);
    case "saldo":
      return formatQuantity(item.saldo);
    case "no_estoque":
      return formatQuantity(getAllocatedStock(item));
    case "cobertura": {
      const coverage = resolveLineCoverage(item);
      return (
        <CommercialInlineMeter
          value={coverage.ratio}
          max={1}
          tone={coverage.tone}
          label={`${coverage.percentLabel} · ${coverage.quantityLabel}`}
          aria-label="Cobertura"
        />
      );
    }
    case "data_entrega": {
      const days = getDeliveryOverdueDays(item.data_entrega);
      const late = days != null && item.saldo > 0;
      return (
        <span className={late ? "cm-cell-danger" : undefined}>
          {formatDisplayDate(item.data_entrega)}
        </span>
      );
    }
    case "previsao_entrega_op": {
      const previsao = getLineOpForecast(item);
      const prazoBadge = resolvePrevisaoPrazoBadge(item);
      return (
        <div className="cm-open-orders-card__row">
          <span>{previsao.previsaoLabel}</span>
          {prazoBadge ? (
            <StatusBadge
              classNames={cmStatusBadgeClassNames}
              label={prazoBadge.label}
              variant={prazoBadge.variant}
            />
          ) : null}
        </div>
      );
    }
    case "data_despacho":
      return item.data_despacho ? formatDisplayDate(item.data_despacho) : "Não informado";
    case "valor_aberto":
      return formatCurrency(item.valor_aberto);
    case "status": {
      const status = getLineStatus(item);
      return (
        <StatusBadge
          classNames={cmStatusBadgeClassNames}
          label={status.label}
          variant={badgeVariant(status.tone)}
        />
      );
    }
    case "atraso_dias": {
      const overdue = getDeliveryOverdueDays(item.data_entrega);
      if (overdue == null || item.saldo <= 0) return "—";
      return (
        <StatusBadge
          classNames={cmStatusBadgeClassNames}
          label={`${overdue.toLocaleString("pt-BR")} d`}
          variant="danger"
        />
      );
    }
    default:
      return "—";
  }
}

export function OpenOrdersLineCard({
  item,
  visibleKeys,
  onOpenDetail,
}: OpenOrdersLineCardProps) {
  const openDetail = () => onOpenDetail(item);

  const onCardKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openDetail();
    }
  };

  const customerLabel = item.nome_cliente?.trim() || "linha";
  const pedidoLabel = item.pedido?.trim() || "—";
  const fields = TABLE_COLUMNS.filter((column) => visibleKeys.has(column.key));

  return (
    <article
      className="cm-open-orders-card cm-open-orders-card--interactive"
      role="button"
      tabIndex={0}
      aria-label={`${CM_HELP.openOrders.cardAriaOpen}: ${customerLabel}, pedido ${pedidoLabel}`}
      onClick={openDetail}
      onKeyDown={onCardKeyDown}
    >
      {fields.map((column) => {
        const isTitle = column.key === "nome_cliente";
        const isValue = column.key === "valor_aberto";
        return (
          <CardField
            key={column.key}
            columnKey={column.key}
            label={column.label}
            valueClassName={
              isTitle
                ? "cm-open-orders-card__title"
                : isValue
                  ? "cm-open-orders-card__value"
                  : "cm-open-orders-card__meta"
            }
          >
            {renderCardValue(column.key, item)}
          </CardField>
        );
      })}
      <div className="cm-open-orders-card__actions">
        <span className="cm-open-orders-card__open-hint" aria-hidden="true">
          {CM_HELP.openOrders.cardOpenHint}
        </span>
      </div>
    </article>
  );
}

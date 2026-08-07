import type { KeyboardEvent, MouseEvent, ReactNode } from "react";
import { FieldLabel, StatusBadge } from "@delpi/plugin-ui/index";

import {
  CommercialInlineMeter,
  cmStatusBadgeClassNames,
} from "../app/commercialUi";
import { navigateCustomerDetail } from "../app/pluginNavigation";
import { CM_HELP } from "../content/helpTooltips";
import { CustomerAvatar } from "../features/customers/components/CustomerAvatar";
import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";
import { formatDisplayDate, getDeliveryOverdueDays } from "../utils/dates";
import { formatEntityTypeWithCodeStore } from "../utils/entityCodeStore";
import { formatCurrency, formatQuantity } from "../utils/format";
import { openOrdersColumnHelp } from "../utils/openOrdersColumnHelp";
import {
  resolveLineCoverage,
  resolvePrevisaoPrazoBadge,
} from "../utils/openOrdersLineVisual";
import { canOpenOpForecastModal, getLineOpForecast } from "../utils/opAllocation";
import { getAllocatedStock } from "../utils/stockAllocation";
import { getLineStatus, getLineStatusCompactLabel } from "../utils/statusBadges";
import { TABLE_COLUMNS, type TableColumnKey } from "../utils/tableColumns";

type OpenOrdersLineCardProps = {
  item: OpenOrdersTotvsItem;
  visibleKeys: ReadonlySet<TableColumnKey>;
  hasAvatar?: boolean;
  basePath?: string;
  onOpenDetail: (item: OpenOrdersTotvsItem) => void;
};

/** Evita que o clique no link interno dispare o open do card inteiro. */
function stopCardBubble(event: MouseEvent | KeyboardEvent) {
  event.stopPropagation();
}

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

function renderCardValue(
  key: TableColumnKey,
  item: OpenOrdersTotvsItem,
  hasAvatar: boolean,
  options: { basePath?: string; onOpenDetail: (item: OpenOrdersTotvsItem) => void },
): ReactNode {
  switch (key) {
    case "nome_cliente": {
      const code = item.codigo_cadastro?.trim() ?? "";
      const store = item.loja_cadastro?.trim() ?? "";
      const name = item.nome_cliente?.trim() || "—";
      return (
        <div className="cm-open-orders-client">
          {code && store ? (
            <CustomerAvatar
              code={code}
              store={store}
              name={name}
              hasAvatar={hasAvatar}
              size="sm"
            />
          ) : null}
          <div className="cm-open-orders-client__text">
            {code && store ? (
              <button
                type="button"
                className="cm-open-orders-client__name"
                onClick={(event) => {
                  stopCardBubble(event);
                  navigateCustomerDetail(code, store, { basePath: options.basePath });
                }}
                onKeyDown={stopCardBubble}
              >
                {name}
              </button>
            ) : (
              <strong className="cm-open-orders-client__name">{name}</strong>
            )}
            <span className="cm-open-orders-client__id">
              {formatEntityTypeWithCodeStore(item.tipo_entidade, item.codigo_cadastro, null)}
            </span>
          </div>
        </div>
      );
    }
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
        <div className="cm-open-orders-meter">
          <CommercialInlineMeter
            value={coverage.ratio}
            max={1}
            tone={coverage.tone}
            size="sm"
            label={coverage.percentLabel}
            aria-label={`Cobertura ${coverage.percentLabel}: ${coverage.quantityLabel}`}
          />
          <span className="cm-cell-muted cm-open-orders-meter__qty">
            {coverage.quantityLabel}
          </span>
        </div>
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
      if (previsao.previsaoLabel === "—") return "—";
      return (
        <div className="cm-cell-inline">
          {canOpenOpForecastModal(item) ? (
            <button
              type="button"
              className="cm-link-button cm-cell-inline__primary"
              title="Ver detalhe da linha e OPs"
              onClick={(event) => {
                stopCardBubble(event);
                options.onOpenDetail(item);
              }}
              onKeyDown={stopCardBubble}
            >
              {previsao.previsaoLabel}
            </button>
          ) : (
            <span className="cm-cell-inline__primary">{previsao.previsaoLabel}</span>
          )}
          {prazoBadge ? (
            <StatusBadge
              classNames={cmStatusBadgeClassNames}
              className="cm-open-orders-badge"
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
          className="cm-open-orders-badge"
          label={getLineStatusCompactLabel(item)}
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
          className="cm-open-orders-badge cm-open-orders-badge--days"
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
  hasAvatar = false,
  basePath,
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
  const valueOptions = { basePath, onOpenDetail };

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
            {renderCardValue(column.key, item, hasAvatar, valueOptions)}
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

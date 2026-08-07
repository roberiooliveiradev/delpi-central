import type { KeyboardEvent } from "react";
import { HelpTooltip, StatusBadge } from "@delpi/plugin-ui/index";

import {
  CommercialInlineMeter,
  cmStatusBadgeClassNames,
} from "../app/commercialUi";
import { CM_HELP } from "../content/helpTooltips";
import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";
import { formatDisplayDate, getDeliveryOverdueDays } from "../utils/dates";
import { formatCurrency } from "../utils/format";
import { openOrdersColumnHelp } from "../utils/openOrdersColumnHelp";
import {
  resolveLineCoverage,
  resolvePrevisaoPrazoBadge,
} from "../utils/openOrdersLineVisual";
import { getLineOpForecast } from "../utils/opAllocation";
import { getLineStatus } from "../utils/statusBadges";
import type { TableColumnKey } from "../utils/tableColumns";

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

function CardFieldLabel({
  columnKey,
  label,
}: {
  columnKey: TableColumnKey;
  label: string;
}) {
  return (
    <span className="cm-open-orders-card__field-label">
      <span>{label}</span>
      <HelpTooltip
        content={openOrdersColumnHelp(columnKey)}
        ariaLabel={`Ajuda: ${label}`}
        placement="top"
      />
    </span>
  );
}

export function OpenOrdersLineCard({
  item,
  visibleKeys,
  onOpenDetail,
}: OpenOrdersLineCardProps) {
  const coverage = resolveLineCoverage(item);
  const previsao = getLineOpForecast(item);
  const status = getLineStatus(item);
  const prazoBadge = resolvePrevisaoPrazoBadge(item);
  const overdue = getDeliveryOverdueDays(item.data_entrega);
  const show = (key: TableColumnKey) => visibleKeys.has(key);
  const openDetail = () => onOpenDetail(item);

  const onCardKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openDetail();
    }
  };

  const customerLabel = item.nome_cliente?.trim() || "linha";
  const pedidoLabel = item.pedido?.trim() || "—";

  return (
    <article
      className="cm-open-orders-card cm-open-orders-card--interactive"
      role="button"
      tabIndex={0}
      aria-label={`${CM_HELP.openOrders.cardAriaOpen}: ${customerLabel}, pedido ${pedidoLabel}`}
      onClick={openDetail}
      onKeyDown={onCardKeyDown}
    >
      {show("nome_cliente") ? (
        <div className="cm-open-orders-card__field">
          <CardFieldLabel columnKey="nome_cliente" label="Cliente" />
          <h3 className="cm-open-orders-card__title">{item.nome_cliente || "Cliente"}</h3>
        </div>
      ) : null}
      {show("pedido") ? (
        <div className="cm-open-orders-card__field">
          <CardFieldLabel columnKey="pedido" label="Pedido" />
          <p className="cm-open-orders-card__meta">
            {item.pedido || "—"} · Linha {item.linha || "—"}
          </p>
        </div>
      ) : null}
      {show("produto") ? (
        <div className="cm-open-orders-card__field">
          <CardFieldLabel columnKey="produto" label="Produto" />
          <p className="cm-open-orders-card__meta">{item.produto || "—"}</p>
        </div>
      ) : null}
      {show("cobertura") ? (
        <div className="cm-open-orders-card__field">
          <CardFieldLabel columnKey="cobertura" label="Cobertura" />
          <CommercialInlineMeter
            value={coverage.ratio}
            max={1}
            tone={coverage.tone}
            label={`${coverage.percentLabel} · ${coverage.quantityLabel}`}
            aria-label="Cobertura"
          />
        </div>
      ) : null}
      {show("data_entrega") ? (
        <div className="cm-open-orders-card__field">
          <CardFieldLabel columnKey="data_entrega" label="Entrega" />
          <p className="cm-open-orders-card__meta">
            {formatDisplayDate(item.data_entrega)}
          </p>
        </div>
      ) : null}
      {show("previsao_entrega_op") ? (
        <div className="cm-open-orders-card__field">
          <CardFieldLabel columnKey="previsao_entrega_op" label="Previsão OP" />
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
        </div>
      ) : null}
      {(show("status") || (show("atraso_dias") && overdue != null && item.saldo > 0)) ? (
        <div className="cm-open-orders-card__field">
          <div className="cm-open-orders-card__badges-head">
            {show("status") ? (
              <CardFieldLabel columnKey="status" label="Status" />
            ) : null}
            {show("atraso_dias") ? (
              <CardFieldLabel columnKey="atraso_dias" label="Atraso" />
            ) : null}
          </div>
          <div className="cm-open-orders-card__badges">
            {show("status") ? (
              <StatusBadge
                classNames={cmStatusBadgeClassNames}
                label={status.label}
                variant={badgeVariant(status.tone)}
              />
            ) : null}
            {show("atraso_dias") && overdue != null && item.saldo > 0 ? (
              <StatusBadge
                classNames={cmStatusBadgeClassNames}
                label={`${overdue} d`}
                variant="danger"
              />
            ) : null}
          </div>
        </div>
      ) : null}
      {show("valor_aberto") ? (
        <div className="cm-open-orders-card__field">
          <CardFieldLabel columnKey="valor_aberto" label="Valor aberto" />
          <p className="cm-open-orders-card__value">{formatCurrency(item.valor_aberto)}</p>
        </div>
      ) : null}
      <div className="cm-open-orders-card__actions">
        <span className="cm-open-orders-card__open-hint" aria-hidden="true">
          {CM_HELP.openOrders.cardOpenHint}
        </span>
        <HelpTooltip
          content={CM_HELP.openOrders.detail.modal}
          ariaLabel="Ajuda: detalhe da linha"
          placement="top"
        />
      </div>
    </article>
  );
}

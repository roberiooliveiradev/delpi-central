import type { KeyboardEvent, MouseEvent, ReactNode } from "react";
import { StatusBadge, formatOperationalUnitCode } from "@delpi/plugin-ui/index";

import {
  CommercialEntityLink,
  CommercialInlineMeter,
  CommercialInteractiveDataCard,
  cmStatusBadgeClassNames,
} from "../app/commercialUi";
import { currentReturnNav } from "../app/commercialNavigationReturn";
import {
  buildCustomerDetailHref,
  buildOpenOrderLineDetailPath,
  buildOpenOrderOpDetailPath,
  navigateCustomerDetail,
  navigateOpenOrderOpDetail,
} from "../app/pluginNavigation";
import {
  accountLinkTitle,
  openOrderLineLinkTitle,
  opPageLinkTitle,
} from "../content/entityLinkHints";
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
import { canOpenOpForecastDetail, getLineOpForecast } from "../utils/opAllocation";
import { getAllocatedStock } from "../utils/stockAllocation";
import { getLineStatus, getLineStatusCompactLabel } from "../utils/statusBadges";
import type { TableColumnKey } from "../utils/tableColumns";
import { buildOpenOrdersContextSearch } from "../utils/openOrdersDeepLink";

type OpenOrdersLineCardProps = {
  item: OpenOrdersTotvsItem;
  /** Colunas visíveis na ordem compartilhada com a tabela. */
  visibleColumns: ReadonlyArray<{ key: TableColumnKey; label: string }>;
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
      const returnNav = currentReturnNav("Meus pedidos");
      const accountHref =
        code && store
          ? buildCustomerDetailHref(code, store, {
              basePath: options.basePath,
              search: "",
              returnNav,
            })
          : null;
      const accountTitle = accountLinkTitle(name);
      const goAccount = () => {
        if (!code || !store) return;
        navigateCustomerDetail(code, store, {
          basePath: options.basePath,
          returnNav,
        });
      };
      return (
        <div className="cm-open-orders-client">
          {code && store && accountHref ? (
            <CustomerAvatar
              code={code}
              store={store}
              name={name}
              hasAvatar={hasAvatar}
              size="sm"
              href={accountHref}
              title={accountTitle}
              onNavigate={goAccount}
            />
          ) : code && store ? (
            <CustomerAvatar
              code={code}
              store={store}
              name={name}
              hasAvatar={hasAvatar}
              size="sm"
            />
          ) : null}
          <div className="cm-open-orders-client__text">
            {accountHref ? (
              <CommercialEntityLink
                href={accountHref}
                title={accountTitle}
                className="cm-open-orders-client__name"
                onNavigate={goAccount}
              >
                {name}
              </CommercialEntityLink>
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
      return formatOperationalUnitCode(item.filial);
    case "pedido": {
      const contextSearch = buildOpenOrdersContextSearch();
      const href =
        buildOpenOrderLineDetailPath(
          options.basePath,
          item.filial,
          item.pedido,
          item.linha,
          contextSearch,
        ) ?? "#";
      const title = openOrderLineLinkTitle(item.pedido, item.linha);
      return (
        <span onClick={stopCardBubble} onKeyDown={stopCardBubble}>
          <CommercialEntityLink
            href={href}
            title={title}
            className="cm-link-button"
            onNavigate={() => options.onOpenDetail(item)}
          >
            {item.pedido || "—"}
          </CommercialEntityLink>
          <span className="cm-cell-muted"> · Linha {item.linha || "—"}</span>
        </span>
      );
    }
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
      const firstOp = previsao.opsUtilizadas[0]?.numero_op?.trim();
      const prazoBadge = resolvePrevisaoPrazoBadge(item);
      if (previsao.previsaoLabel === "—") return "—";
      const contextSearch = buildOpenOrdersContextSearch();
      const lineHref =
        buildOpenOrderLineDetailPath(
          options.basePath,
          item.filial,
          item.pedido,
          item.linha,
          contextSearch,
        ) ?? "#";
      const lineTitle = openOrderLineLinkTitle(item.pedido, item.linha);
      const opHref = firstOp
        ? buildOpenOrderOpDetailPath(
            options.basePath,
            item.filial,
            item.pedido,
            item.linha,
            firstOp,
            contextSearch,
          )
        : null;
      return (
        <div className="cm-cell-inline" onClick={stopCardBubble} onKeyDown={stopCardBubble}>
          {canOpenOpForecastDetail(item) ? (
            <CommercialEntityLink
              href={lineHref}
              title={lineTitle}
              className="cm-link-button cm-cell-inline__primary"
              onNavigate={() => options.onOpenDetail(item)}
            >
              {previsao.previsaoLabel}
            </CommercialEntityLink>
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
          {firstOp && opHref ? (
            <CommercialEntityLink
              href={opHref}
              title={opPageLinkTitle(firstOp)}
              className="cm-link-button"
              onNavigate={() =>
                navigateOpenOrderOpDetail(
                  item.filial,
                  item.pedido,
                  item.linha,
                  firstOp,
                  {
                    basePath: options.basePath,
                    search: contextSearch,
                  },
                )
              }
            >
              OP {firstOp}
            </CommercialEntityLink>
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
  visibleColumns,
  hasAvatar = false,
  basePath,
  onOpenDetail,
}: OpenOrdersLineCardProps) {
  const openDetail = () => onOpenDetail(item);
  const customerLabel = item.nome_cliente?.trim() || "linha";
  const pedidoLabel = item.pedido?.trim() || "—";
  const valueOptions = { basePath, onOpenDetail };

  return (
    <CommercialInteractiveDataCard
      ariaLabel={`${CM_HELP.openOrders.cardAriaOpen}: ${customerLabel}, pedido ${pedidoLabel}`}
      onActivate={openDetail}
      openHint={CM_HELP.openOrders.cardOpenHint}
      fields={visibleColumns.map((column) => {
        const isTitle = column.key === "nome_cliente";
        const isValue = column.key === "valor_aberto";
        return {
          id: column.key,
          label: column.label,
          hint: openOrdersColumnHelp(column.key),
          valueTone: isTitle ? "title" : isValue ? "value" : "meta",
          value: renderCardValue(column.key, item, hasAvatar, valueOptions),
        };
      })}
    />
  );
}

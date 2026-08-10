import type { CSSProperties } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  DataTable,
  ExcelExportButton,
  HelpTooltip,
  SectionCard,
  SegmentToggle,
  StatusBadge,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";

import {
  CommercialInlineMeter,
  CommercialSelectField,
  cmDataTableClassNames,
  cmDataTableLabels,
  cmSectionCardClassNames,
  cmSectionLabels,
  cmStatusBadgeClassNames,
  UI_PREFIX,
} from "../app/commercialUi";
import {
  navigateCustomerDetail,
  navigateOpenOrderLineDetail,
  navigateOpenOrderOpDetail,
} from "../app/pluginNavigation";
import { CM_HELP } from "../content/helpTooltips";
import { CustomerAvatar } from "../features/customers/components/CustomerAvatar";
import {
  customerAvatarKey,
  useOpenOrdersCustomerAvatars,
} from "../hooks/useOpenOrdersCustomerAvatars";
import { useOpenOrdersLayout } from "../hooks/useOpenOrdersLayout";
import { useTableColumnPreferences } from "../hooks/useTableColumnPreferences";
import { useTableFontSize } from "../hooks/useTableFontSize";
import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";
import { formatDisplayDate, getDeliveryOverdueDays } from "../utils/dates";
import { formatEntityTypeWithCodeStore } from "../utils/entityCodeStore";
import { exportOpenOrdersExcel } from "../utils/exportOpenOrdersExcel";
import { formatCurrency, formatQuantity } from "../utils/format";
import { openOrdersColumnHelp } from "../utils/openOrdersColumnHelp";
import {
  findOpenOrderLine,
  buildOpenOrdersContextSearch,
  parseOpenOrdersLineDeepLink,
} from "../utils/openOrdersDeepLink";
import {
  resolveLineCoverage,
  resolvePrevisaoPrazoBadge,
} from "../utils/openOrdersLineVisual";
import { canOpenOpForecastDetail, getLineOpForecast } from "../utils/opAllocation";
import { getAllocatedStock } from "../utils/stockAllocation";
import type { SortDirection, SortKey } from "../utils/sortItems";
import { getLineStatus, getLineStatusCompactLabel } from "../utils/statusBadges";
import {
  isSortableTableColumnKey,
  TABLE_COLUMNS,
  type TableColumnKey,
} from "../utils/tableColumns";
import { OpenOrdersLineCard } from "./OpenOrdersLineCard";
import { TableColumnSettings } from "./TableColumnSettings";
import { TableFontSizeControls } from "./TableFontSizeControls";

type OpenOrdersTableProps = {
  rows: OpenOrdersTotvsItem[];
  exportRows: OpenOrdersTotvsItem[];
  sortKey: SortKey;
  sortDirection: SortDirection;
  onSort: (key: SortKey) => void;
  loading?: boolean;
  emptyMessage?: string;
  basePath?: string;
};

function rowKey(row: OpenOrdersTotvsItem): string {
  return `${row.filial}-${row.pedido}-${row.linha}-${row.produto}`;
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

const SORT_OPTIONS = TABLE_COLUMNS.filter((c) => c.sortable).map((c) => ({
  value: c.key,
  label: c.label,
}));

export function OpenOrdersTable({
  rows,
  exportRows,
  sortKey,
  sortDirection,
  onSort,
  loading = false,
  emptyMessage = "Nenhum registro encontrado.",
  basePath,
}: OpenOrdersTableProps) {
  const [exporting, setExporting] = useState(false);
  const deepLinkHandledRef = useRef(false);
  const { layout, setLayout } = useOpenOrdersLayout();
  const {
    preferences,
    visibleColumns,
    orderedMenuColumns,
    visibleColumnCount,
    setColumnVisible,
    reorderColumns,
    applyVisibleOrder,
    resetPreferences,
  } = useTableColumnPreferences();
  const {
    fontSize,
    increase,
    decrease,
    reset,
    canIncrease,
    canDecrease,
    isDefault,
  } = useTableFontSize();
  const customerAvatars = useOpenOrdersCustomerAvatars(rows);

  useEffect(() => {
    if (loading || deepLinkHandledRef.current) return;
    deepLinkHandledRef.current = true;
    const link = parseOpenOrdersLineDeepLink();
    if (!link) return;
    const found = findOpenOrderLine(exportRows, link);
    if (found) {
      navigateOpenOrderLineDetail(found.filial, found.pedido, found.linha, {
        basePath,
        search: buildOpenOrdersContextSearch(),
        replace: true,
      });
    }
  }, [basePath, loading, exportRows]);

  const openDetail = (row: OpenOrdersTotvsItem) => {
    navigateOpenOrderLineDetail(row.filial, row.pedido, row.linha, {
      basePath,
      search: buildOpenOrdersContextSearch(),
    });
  };

  const tableStyle = {
    "--cm-table-font-size": `${fontSize}px`,
    "--delpi-ui-table-font-size": `${fontSize}px`,
  } as CSSProperties;

  const handleExportExcel = async () => {
    if (exportRows.length === 0 || exporting) return;
    try {
      setExporting(true);
      await exportOpenOrdersExcel(exportRows, visibleColumns);
    } finally {
      setExporting(false);
    }
  };

  const columns: DataTableColumn<OpenOrdersTotvsItem>[] = useMemo(() => {
    const renderers: Record<
      TableColumnKey,
      (row: OpenOrdersTotvsItem) => ReturnType<DataTableColumn<OpenOrdersTotvsItem>["render"]>
    > = {
      nome_cliente: (row) => {
        const code = row.codigo_cadastro?.trim() ?? "";
        const store = row.loja_cadastro?.trim() ?? "";
        const hasAvatar =
          Boolean(code && store) &&
          Boolean(customerAvatars.get(customerAvatarKey(code, store)));
        const name = row.nome_cliente?.trim() || "—";
        const entityLine = formatEntityTypeWithCodeStore(
          row.tipo_entidade,
          row.codigo_cadastro,
          null,
        );
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
            ) : (
              <span className="cm-open-orders-client__avatar-spacer" aria-hidden="true" />
            )}
            <div className="cm-open-orders-client__text">
              {code && store ? (
                <button
                  type="button"
                  className="cm-open-orders-client__name"
                  onClick={() => navigateCustomerDetail(code, store, { basePath })}
                >
                  {name}
                </button>
              ) : (
                <strong className="cm-open-orders-client__name">{name}</strong>
              )}
              <span className="cm-open-orders-client__id">{entityLine}</span>
            </div>
          </div>
        );
      },
      loja_cadastro: (row) => row.loja_cadastro || "—",
      filial: (row) => row.filial || "—",
      pedido: (row) => (
        <div className="cm-cell-stack cm-cell-stack--tight">
          <span>{row.pedido || "—"}</span>
          <span className="cm-cell-muted">Linha {row.linha || "—"}</span>
        </div>
      ),
      pedido_cliente: (row) => row.pedido_cliente || "—",
      produto: (row) => row.produto || "—",
      codigo_cliente: (row) => row.codigo_cliente || "—",
      quantidade: (row) => formatQuantity(row.quantidade),
      entregue: (row) => formatQuantity(row.entregue),
      saldo: (row) => formatQuantity(row.saldo),
      no_estoque: (row) => formatQuantity(getAllocatedStock(row)),
      cobertura: (row) => {
        const coverage = resolveLineCoverage(row);
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
      },
      data_entrega: (row) => {
        const days = getDeliveryOverdueDays(row.data_entrega);
        const late = days != null && row.saldo > 0;
        return (
          <span className={late ? "cm-cell-danger" : undefined}>
            {formatDisplayDate(row.data_entrega)}
          </span>
        );
      },
      previsao_entrega_op: (row) => {
        const previsao = getLineOpForecast(row);
        const firstOp = previsao.opsUtilizadas[0]?.numero_op?.trim();
        const prazoBadge = resolvePrevisaoPrazoBadge(row);
        if (previsao.previsaoLabel === "—") return "—";
        return (
          <div className="cm-cell-inline">
            {canOpenOpForecastDetail(row) ? (
              <button
                type="button"
                className="cm-link-button cm-cell-inline__primary"
                onClick={() => openDetail(row)}
                title="Ver detalhe da linha e OPs"
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
            {firstOp ? (
              <button
                type="button"
                className="cm-link-button"
                onClick={(event) => {
                  event.stopPropagation();
                  navigateOpenOrderOpDetail(
                    row.filial,
                    row.pedido,
                    row.linha,
                    firstOp,
                    {
                      basePath,
                      search: buildOpenOrdersContextSearch(),
                    },
                  );
                }}
                title={`Abrir página da OP ${firstOp}`}
              >
                OP {firstOp}
              </button>
            ) : null}
          </div>
        );
      },
      data_despacho: (row) =>
        row.data_despacho ? formatDisplayDate(row.data_despacho) : "Não informado",
      valor_aberto: (row) => formatCurrency(row.valor_aberto),
      status: (row) => {
        const badge = getLineStatus(row);
        return (
          <StatusBadge
            classNames={cmStatusBadgeClassNames}
            className="cm-open-orders-badge"
            label={getLineStatusCompactLabel(row)}
            variant={badgeVariant(badge.tone)}
          />
        );
      },
      atraso_dias: (row) => {
        const days = getDeliveryOverdueDays(row.data_entrega);
        if (days == null || row.saldo <= 0) return "—";
        return (
          <StatusBadge
            classNames={cmStatusBadgeClassNames}
            className="cm-open-orders-badge cm-open-orders-badge--days"
            label={`${days.toLocaleString("pt-BR")} d`}
            variant="danger"
          />
        );
      },
    };

    return visibleColumns.map((column) => ({
      key: column.key,
      header: column.label,
      headerHint: openOrdersColumnHelp(column.key),
      sortable: Boolean(column.sortable),
      interactive:
        column.key === "nome_cliente" ||
        column.key === "previsao_entrega_op" ||
        column.key === "status" ||
        column.key === "cobertura",
      align:
        column.key === "atraso_dias"
          ? ("center" as const)
          : column.key === "saldo" ||
              column.key === "valor_aberto" ||
              column.key === "quantidade" ||
              column.key === "entregue" ||
              column.key === "no_estoque"
            ? ("right" as const)
            : undefined,
      render: (row) => renderers[column.key](row),
    }));
  }, [basePath, customerAvatars, visibleColumns]);

  return (
    <>
      <SectionCard
        title="Pedidos em aberto"
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
        hint={CM_HELP.openOrders.table}
      >
        <div className="cm-table-toolbar" style={tableStyle}>
          <div className="cm-table-toolbar__leading">
            <div className="cm-table-toolbar__layout">
              <HelpTooltip
                content={CM_HELP.openOrders.layoutToggle}
                ariaLabel="Ajuda: modo Tabela ou Cards"
                wrap
                placement="bottom"
              >
                <SegmentToggle
                  prefix={UI_PREFIX}
                  size="sm"
                  ariaLabel="Modo de visualização"
                  idPrefix="open-orders-layout"
                  value={layout}
                  onChange={setLayout}
                  options={[
                    { value: "table", label: "Tabela" },
                    { value: "cards", label: "Cards" },
                  ]}
                />
              </HelpTooltip>
            </div>
            <p className="cm-table-toolbar__hint">
              <HelpTooltip
                content={CM_HELP.openOrders.table}
                ariaLabel="Ajuda: tabela de pedidos"
                wrap
                placement="bottom"
              >
                <span className="delpi-ui-section-hint-label">
                  {visibleColumnCount} coluna(s) ·{" "}
                  {exportRows.length.toLocaleString("pt-BR")} linha(s)
                </span>
              </HelpTooltip>
            </p>
          </div>
          <div className="cm-table-toolbar__actions">
            <ExcelExportButton
              onExport={() => void handleExportExcel()}
              disabled={exportRows.length === 0 || exporting || loading}
              exporting={exporting}
            />
            <TableFontSizeControls
              fontSize={fontSize}
              onIncrease={increase}
              onDecrease={decrease}
              onReset={reset}
              canIncrease={canIncrease}
              canDecrease={canDecrease}
              isDefault={isDefault}
            />
            <TableColumnSettings
              columns={orderedMenuColumns}
              visibility={preferences.visibility}
              onToggleColumn={setColumnVisible}
              onReorderColumns={reorderColumns}
              onReset={resetPreferences}
            />
          </div>
        </div>

        {layout === "cards" ? (
          <div className="cm-open-orders-cards-toolbar" style={tableStyle}>
            <CommercialSelectField
              id="open-orders-sort"
              label="Ordenar por"
              hint={CM_HELP.openOrders.sortBy}
              value={sortKey}
              options={SORT_OPTIONS}
              onChange={(value) => {
                if (isSortableTableColumnKey(value as TableColumnKey)) {
                  onSort(value as SortKey);
                }
              }}
            />
            <div className="cm-open-orders-cards-toolbar__dir">
              <HelpTooltip
                content={CM_HELP.openOrders.sortDirection}
                ariaLabel="Ajuda: direção da ordenação"
                wrap
                placement="bottom"
              >
                <SegmentToggle
                  prefix={UI_PREFIX}
                  size="sm"
                  ariaLabel="Direção da ordenação"
                  idPrefix="open-orders-sort-dir"
                  value={sortDirection}
                  onChange={(dir) => {
                    if (dir !== sortDirection) onSort(sortKey);
                  }}
                  options={[
                    { value: "asc", label: "Crescente" },
                    { value: "desc", label: "Decrescente" },
                  ]}
                />
              </HelpTooltip>
            </div>
          </div>
        ) : null}

        {layout === "table" ? (
          <div className="cm-open-orders-table" style={tableStyle}>
            <DataTable
              rows={rows}
              rowKey={rowKey}
              classNames={cmDataTableClassNames}
              labels={{ ...cmDataTableLabels, emptyMessage }}
              layout="section"
              loading={loading}
              sortKey={sortKey}
              sortDirection={sortDirection}
              onSortChange={(key) => {
                if (isSortableTableColumnKey(key as TableColumnKey)) {
                  onSort(key as SortKey);
                }
              }}
              onRowClick={(row) => openDetail(row)}
              enableColumnReorder
              onColumnOrderChange={applyVisibleOrder}
              columns={columns}
            />
          </div>
        ) : (
          <div className="cm-open-orders-cards" style={tableStyle}>
            {rows.length === 0 ? (
              <p className="cm-open-orders-cards__empty">{emptyMessage}</p>
            ) : (
              rows.map((row) => (
                <OpenOrdersLineCard
                  key={rowKey(row)}
                  item={row}
                  visibleColumns={visibleColumns}
                  basePath={basePath}
                  hasAvatar={Boolean(
                    row.codigo_cadastro?.trim() &&
                      row.loja_cadastro?.trim() &&
                      customerAvatars.get(
                        customerAvatarKey(row.codigo_cadastro, row.loja_cadastro),
                      ),
                  )}
                  onOpenDetail={openDetail}
                />
              ))
            )}
          </div>
        )}
      </SectionCard>

    </>
  );
}

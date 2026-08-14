import type { CSSProperties } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  DataTable,
  HelpTooltip,
  SectionCard,
  SegmentToggle,
  StatusBadge,
  formatOperationalUnitCode,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";

import {
  CommercialDataCardsGrid,
  CommercialDataCardsSortBar,
  CommercialDataListToolbar,
  CommercialEntityLink,
  CommercialExcelExportButton,
  CommercialInlineMeter,
  CommercialSelectField,
  CommercialTableFontSizeControls,
  cmDataTableClassNames,
  cmDataTableLabels,
  cmSectionCardClassNames,
  cmSectionLabels,
  cmStatusBadgeClassNames,
  OPEN_ORDERS_LAYOUT_STORAGE_KEY,
  OPEN_ORDERS_TABLE_FONT_SIZE_LEGACY_KEYS,
  OPEN_ORDERS_TABLE_FONT_SIZE_STORAGE_KEY,
  UI_PREFIX,
  usePersistedViewLayout,
  useTableFontSize,
} from "../app/commercialUi";
import {
  buildCustomerDetailHref,
  buildOpenOrderLineDetailPath,
  buildOpenOrderOpDetailPath,
  navigateCustomerDetail,
  navigateOpenOrderLineDetail,
  navigateOpenOrderOpDetail,
} from "../app/pluginNavigation";
import { currentReturnNav } from "../app/commercialNavigationReturn";
import {
  accountLinkTitle,
  openOrderLineLinkTitle,
  opPageLinkTitle,
} from "../content/entityLinkHints";
import { CM_HELP } from "../content/helpTooltips";
import { CustomerAvatar } from "../features/customers/components/CustomerAvatar";
import {
  customerAvatarKey,
  useOpenOrdersCustomerAvatars,
} from "../hooks/useOpenOrdersCustomerAvatars";
import { useTableColumnPreferences } from "../hooks/useTableColumnPreferences";
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
  parseOpenOrdersListUrlState,
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
import { useRecentlyClosedOrdersTotvs } from "../hooks/useRecentlyClosedOrdersTotvs";
import { OpenOrdersLineCard } from "./OpenOrdersLineCard";
import { OpenOrdersKanbanBoardView } from "./OpenOrdersKanbanBoard";
import { TableColumnSettings } from "./TableColumnSettings";

type OpenOrdersTableProps = {
  rows: OpenOrdersTotvsItem[];
  exportRows: OpenOrdersTotvsItem[];
  sortKey: SortKey;
  sortDirection: SortDirection;
  onSort: (key: SortKey) => void;
  loading?: boolean;
  emptyMessage?: string;
  basePath?: string;
  /** Portfolio PK for BFF recently-closed (same scope as open list). */
  sellerId?: string | null;
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
  sellerId = null,
}: OpenOrdersTableProps) {
  const [exporting, setExporting] = useState(false);
  const deepLinkHandledRef = useRef(false);
  const { layout, setLayout } = usePersistedViewLayout({
    storageKey: OPEN_ORDERS_LAYOUT_STORAGE_KEY,
  });
  const urlListState = useMemo(
    () => parseOpenOrdersListUrlState(typeof window !== "undefined" ? window.location.search : ""),
    [],
  );
  const [focusStage, setFocusStage] = useState(urlListState.stage);

  useEffect(() => {
    if (urlListState.view === "board" || urlListState.view === "cards" || urlListState.view === "table") {
      setLayout(urlListState.view);
    }
    if (urlListState.stage) {
      setFocusStage(urlListState.stage);
    }
  }, [urlListState.stage, urlListState.view, setLayout]);
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
  } = useTableFontSize({
    storageKey: OPEN_ORDERS_TABLE_FONT_SIZE_STORAGE_KEY,
    legacyStorageKeys: OPEN_ORDERS_TABLE_FONT_SIZE_LEGACY_KEYS,
  });
  const boardEnabled = layout === "board";
  const closedOrders = useRecentlyClosedOrdersTotvs({
    enabled: boardEnabled,
    sellerId,
  });
  const customerAvatars = useOpenOrdersCustomerAvatars(
    boardEnabled ? exportRows : rows,
  );

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
        const returnNav = currentReturnNav("Meus pedidos");
        const accountHref =
          code && store
            ? buildCustomerDetailHref(code, store, {
                basePath,
                search: "",
                returnNav,
              })
            : null;
        const accountTitle = accountLinkTitle(name);
        const goAccount = () => {
          if (!code || !store) return;
          navigateCustomerDetail(code, store, { basePath, returnNav });
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
            ) : (
              <span className="cm-open-orders-client__avatar-spacer" aria-hidden="true" />
            )}
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
              <span className="cm-open-orders-client__id">{entityLine}</span>
            </div>
          </div>
        );
      },
      loja_cadastro: (row) => row.loja_cadastro || "—",
      filial: (row) => formatOperationalUnitCode(row.filial),
      pedido: (row) => {
        const contextSearch = buildOpenOrdersContextSearch();
        const href =
          buildOpenOrderLineDetailPath(
            basePath,
            row.filial,
            row.pedido,
            row.linha,
            contextSearch,
          ) ?? "#";
        const title = openOrderLineLinkTitle(row.pedido, row.linha);
        return (
          <div className="cm-cell-stack cm-cell-stack--tight">
            <CommercialEntityLink
              href={href}
              title={title}
              className="cm-link-button"
              onNavigate={() => openDetail(row)}
            >
              {row.pedido || "—"}
            </CommercialEntityLink>
            <span className="cm-cell-muted">Linha {row.linha || "—"}</span>
          </div>
        );
      },
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
        const contextSearch = buildOpenOrdersContextSearch();
        const lineHref =
          buildOpenOrderLineDetailPath(
            basePath,
            row.filial,
            row.pedido,
            row.linha,
            contextSearch,
          ) ?? "#";
        const lineTitle = openOrderLineLinkTitle(row.pedido, row.linha);
        const opHref = firstOp
          ? buildOpenOrderOpDetailPath(
              basePath,
              row.filial,
              row.pedido,
              row.linha,
              firstOp,
              contextSearch,
            )
          : null;
        return (
          <div className="cm-cell-inline">
            {canOpenOpForecastDetail(row) ? (
              <CommercialEntityLink
                href={lineHref}
                title={lineTitle}
                className="cm-link-button cm-cell-inline__primary"
                onNavigate={() => openDetail(row)}
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
                    row.filial,
                    row.pedido,
                    row.linha,
                    firstOp,
                    {
                      basePath,
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
        column.key === "nome_cliente" || column.key === "previsao_entrega_op",
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
        <CommercialDataListToolbar
          style={tableStyle}
          leading={
            <HelpTooltip
              content={CM_HELP.openOrders.layoutToggle}
              ariaLabel="Ajuda: modo Tabela, Cards ou Board"
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
                  { value: "board", label: "Board" },
                ]}
              />
            </HelpTooltip>
          }
          hint={
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
          }
          actions={
            <>
              <CommercialExcelExportButton
                onExport={() => void handleExportExcel()}
                disabled={exportRows.length === 0 || exporting || loading}
                exporting={exporting}
              />
              <CommercialTableFontSizeControls
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
            </>
          }
        />

        {layout === "cards" ? (
          <CommercialDataCardsSortBar
            style={tableStyle}
            sortField={
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
            }
            direction={
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
            }
          />
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
        ) : null}

        {layout === "cards" ? (
          <CommercialDataCardsGrid
            style={tableStyle}
            empty={rows.length === 0 ? emptyMessage : undefined}
          >
            {rows.map((row) => (
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
            ))}
          </CommercialDataCardsGrid>
        ) : null}

        {layout === "board" ? (
          <div style={tableStyle}>
            {closedOrders.error ? (
              <p className="cm-cell-muted" role="status">
                Concluídos indisponíveis: {closedOrders.error}
              </p>
            ) : null}
            <OpenOrdersKanbanBoardView
              rows={exportRows}
              completedRows={closedOrders.items}
              visibleColumns={visibleColumns}
              basePath={basePath}
              focusStage={focusStage}
              customerAvatarKeys={
                new Set(
                  [...customerAvatars.entries()]
                    .filter(([, v]) => Boolean(v))
                    .map(([k]) => k),
                )
              }
              onOpenDetail={openDetail}
            />
          </div>
        ) : null}
      </SectionCard>

    </>
  );
}

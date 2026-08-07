import type { CSSProperties } from "react";
import { useMemo, useState } from "react";
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
import { navigateCustomerDetail } from "../app/pluginNavigation";
import { CM_HELP } from "../content/helpTooltips";
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
  resolveLineCoverage,
  resolvePrevisaoPrazoBadge,
} from "../utils/openOrdersLineVisual";
import { canOpenOpForecastModal, getLineOpForecast } from "../utils/opAllocation";
import { getAllocatedStock } from "../utils/stockAllocation";
import type { SortDirection, SortKey } from "../utils/sortItems";
import { getLineStatus } from "../utils/statusBadges";
import {
  isSortableTableColumnKey,
  TABLE_COLUMNS,
  type TableColumnKey,
} from "../utils/tableColumns";
import { OpenOrdersLineCard } from "./OpenOrdersLineCard";
import { OpenOrdersLineDetailModal } from "./OpenOrdersLineDetailModal";
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
  const [detailItem, setDetailItem] = useState<OpenOrdersTotvsItem | null>(null);
  const { layout, setLayout } = useOpenOrdersLayout();
  const { preferences, visibleColumns, visibleColumnCount, setColumnVisible, resetPreferences } =
    useTableColumnPreferences();
  const {
    fontSize,
    increase,
    decrease,
    reset,
    canIncrease,
    canDecrease,
    isDefault,
  } = useTableFontSize();

  const visibleKeySet = useMemo(
    () => new Set(visibleColumns.map((c) => c.key)),
    [visibleColumns],
  );

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
      nome_cliente: (row) => (
        <div className="cm-cell-stack">
          {row.codigo_cadastro && row.loja_cadastro ? (
            <button
              type="button"
              className="cm-link-button"
              onClick={() =>
                navigateCustomerDetail(row.codigo_cadastro, row.loja_cadastro, { basePath })
              }
            >
              <strong>{row.nome_cliente || "—"}</strong>
            </button>
          ) : (
            <strong>{row.nome_cliente || "—"}</strong>
          )}
          <span className="cm-cell-muted">
            {formatEntityTypeWithCodeStore(row.tipo_entidade, row.codigo_cadastro, null)}
          </span>
        </div>
      ),
      loja_cadastro: (row) => row.loja_cadastro || "—",
      filial: (row) => row.filial || "—",
      pedido: (row) => (
        <div className="cm-cell-stack">
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
          <CommercialInlineMeter
            value={coverage.ratio}
            max={1}
            tone={coverage.tone}
            label={`${coverage.percentLabel} · ${coverage.quantityLabel}`}
            aria-label="Cobertura de estoque"
          />
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
        const prazoBadge = resolvePrevisaoPrazoBadge(row);
        if (previsao.previsaoLabel === "—") return "—";
        const label = (
          <div className="cm-cell-stack">
            {canOpenOpForecastModal(row) ? (
              <button
                type="button"
                className="cm-link-button"
                onClick={() => setDetailItem(row)}
                title="Ver detalhe da linha e OPs"
              >
                {previsao.previsaoLabel}
              </button>
            ) : (
              <span>{previsao.previsaoLabel}</span>
            )}
            {prazoBadge ? (
              <StatusBadge
                classNames={cmStatusBadgeClassNames}
                label={prazoBadge.label}
                variant={prazoBadge.variant}
              />
            ) : null}
          </div>
        );
        return label;
      },
      data_despacho: (row) =>
        row.data_despacho ? formatDisplayDate(row.data_despacho) : "Não informado",
      valor_aberto: (row) => formatCurrency(row.valor_aberto),
      status: (row) => {
        const badge = getLineStatus(row);
        return (
          <StatusBadge
            classNames={cmStatusBadgeClassNames}
            label={badge.label}
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
        column.key === "saldo" ||
        column.key === "valor_aberto" ||
        column.key === "quantidade" ||
        column.key === "entregue" ||
        column.key === "no_estoque" ||
        column.key === "atraso_dias"
          ? ("right" as const)
          : undefined,
      render: (row) => renderers[column.key](row),
    }));
  }, [basePath, visibleColumns]);

  return (
    <>
      <SectionCard
        title="Pedidos em aberto"
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
        titleHint={CM_HELP.openOrders.table}
      >
        <div className="cm-table-toolbar" style={tableStyle}>
          <div className="cm-table-toolbar__leading">
            <div className="cm-table-toolbar__layout">
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
              <HelpTooltip
                content={CM_HELP.openOrders.layoutToggle}
                ariaLabel="Ajuda: modo Tabela ou Cards"
                placement="bottom"
              />
            </div>
            <p className="cm-table-toolbar__hint">
              {visibleColumnCount} coluna(s) · {exportRows.length.toLocaleString("pt-BR")} linha(s)
              <HelpTooltip
                content={CM_HELP.openOrders.table}
                ariaLabel="Ajuda: tabela de pedidos"
                placement="bottom"
              />
            </p>
          </div>
          <div className="cm-table-toolbar__actions">
            <ExcelExportButton
              onClick={() => void handleExportExcel()}
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
              visibility={preferences.visibility}
              onToggleColumn={setColumnVisible}
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
              <HelpTooltip
                content={CM_HELP.openOrders.sortDirection}
                ariaLabel="Ajuda: direção da ordenação"
                placement="bottom"
              />
            </div>
          </div>
        ) : null}

        {layout === "table" ? (
          <div style={tableStyle}>
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
              onRowClick={(row) => setDetailItem(row)}
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
                  visibleKeys={visibleKeySet}
                  onOpenDetail={setDetailItem}
                />
              ))
            )}
          </div>
        )}
      </SectionCard>

      <OpenOrdersLineDetailModal
        item={detailItem}
        open={Boolean(detailItem)}
        onClose={() => setDetailItem(null)}
        basePath={basePath}
      />
    </>
  );
}

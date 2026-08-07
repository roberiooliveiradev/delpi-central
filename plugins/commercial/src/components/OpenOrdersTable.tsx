import type { CSSProperties } from "react";
import { useMemo, useState } from "react";
import {
  DataTable,
  ExcelExportButton,
  HelpTooltip,
  SectionCard,
  StatusBadge,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";

import {
  cmDataTableClassNames,
  cmDataTableLabels,
  cmSectionCardClassNames,
  cmSectionLabels,
  cmStatusBadgeClassNames,
} from "../app/commercialUi";
import { navigateCustomerDetail } from "../app/pluginNavigation";
import { CM_HELP } from "../content/helpTooltips";
import { useTableColumnPreferences } from "../hooks/useTableColumnPreferences";
import { useTableFontSize } from "../hooks/useTableFontSize";
import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";
import { formatDisplayDate, getDeliveryOverdueDays } from "../utils/dates";
import { formatEntityTypeWithCodeStore } from "../utils/entityCodeStore";
import { exportOpenOrdersExcel } from "../utils/exportOpenOrdersExcel";
import { formatCurrency, formatQuantity } from "../utils/format";
import { canOpenOpForecastModal, getLineOpForecast } from "../utils/opAllocation";
import { getAllocatedStock } from "../utils/stockAllocation";
import type { SortDirection, SortKey } from "../utils/sortItems";
import { getLineStatus } from "../utils/statusBadges";
import {
  isSortableTableColumnKey,
  type TableColumnKey,
} from "../utils/tableColumns";
import { OpenOrdersLineDrawer } from "./OpenOrdersLineDrawer";
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
  const [drawerItem, setDrawerItem] = useState<OpenOrdersTotvsItem | null>(null);
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
      data_entrega: (row) => formatDisplayDate(row.data_entrega),
      previsao_entrega_op: (row) => {
        const previsao = getLineOpForecast(row);
        if (previsao.previsaoLabel === "—") return "—";
        if (canOpenOpForecastModal(row)) {
          return (
            <button
              type="button"
              className="cm-link-button"
              onClick={() => setDrawerItem(row)}
              title="Ver OPs utilizadas na previsão"
            >
              {previsao.previsaoLabel}
            </button>
          );
        }
        return previsao.previsaoLabel;
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
        return days.toLocaleString("pt-BR");
      },
    };

    return visibleColumns.map((column) => ({
      key: column.key,
      header: column.label,
      sortable: Boolean(column.sortable),
      interactive:
        column.key === "nome_cliente" ||
        column.key === "previsao_entrega_op" ||
        column.key === "status",
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
          <p className="cm-table-toolbar__hint">
            {visibleColumnCount} coluna(s) · {exportRows.length.toLocaleString("pt-BR")} linha(s)
            para exportar. Previsão (OP) = cobertura FIFO pelas OPs abertas.
            <HelpTooltip
              content={CM_HELP.openOrders.table}
              ariaLabel="Ajuda: tabela de pedidos"
              placement="bottom"
            />
          </p>
          <div className="cm-table-toolbar__actions">
            <ExcelExportButton
              disabled={exportRows.length === 0}
              exporting={exporting}
              onExport={handleExportExcel}
            />
            <TableFontSizeControls
              fontSize={fontSize}
              canIncrease={canIncrease}
              canDecrease={canDecrease}
              isDefault={isDefault}
              onIncrease={increase}
              onDecrease={decrease}
              onReset={reset}
            />
            <TableColumnSettings
              visibility={preferences.visibility}
              onToggleColumn={setColumnVisible}
              onReset={resetPreferences}
            />
          </div>
        </div>

        {loading ? (
          <p className="cm-table-loading" role="status">
            Carregando…
          </p>
        ) : rows.length === 0 ? (
          <p className="cm-table-empty" role="status">
            {emptyMessage}
          </p>
        ) : (
          <DataTable
            rows={rows}
            columns={columns}
            rowKey={rowKey}
            classNames={cmDataTableClassNames}
            labels={cmDataTableLabels}
            layout="section"
            sortKey={sortKey}
            sortDirection={sortDirection}
            onSortChange={(key) => {
              if (isSortableTableColumnKey(key as TableColumnKey)) {
                onSort(key as SortKey);
              }
            }}
            onRowClick={(row) => setDrawerItem(row)}
          />
        )}
      </SectionCard>

      <OpenOrdersLineDrawer
        item={drawerItem}
        open={drawerItem != null}
        onClose={() => setDrawerItem(null)}
        basePath={basePath}
      />
    </>
  );
}

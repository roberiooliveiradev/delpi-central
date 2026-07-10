import type { CSSProperties } from "react";
import { useState } from "react";
import { ExcelExportButton } from "@delpi/plugin-ui/index";

import type { PedidosVendaAbertosItem } from "../types/pedidosVendaAbertos";
import { formatEntityTypeWithCodeStore } from "../utils/entityCodeStore";
import { useTableColumnPreferences } from "../hooks/useTableColumnPreferences";
import { useTableFontSize } from "../hooks/useTableFontSize";
import { formatDisplayDate } from "../utils/dates";
import { formatCurrency, formatQuantity } from "../utils/format";
import { canOpenOpPrevisaoModal, getLineOpPrevisao } from "../utils/opAllocation";
import { getAllocatedStock } from "../utils/stockAllocation";
import { getLineStatus } from "../utils/statusBadges";
import type { SortDirection, SortKey } from "../utils/sortItems";
import { isSortableTableColumnKey, type TableColumnKey } from "../utils/tableColumns";
import { exportPedidosExcel } from "../utils/exportPedidosExcel";
import { OpPrevisaoModal } from "./OpPrevisaoModal";
import { StatusBadge } from "./StatusBadge";
import { TableColumnSettings } from "./TableColumnSettings";
import { TableFontSizeControls } from "./TableFontSizeControls";

type PedidosTableProps = {
  rows: PedidosVendaAbertosItem[];
  exportRows: PedidosVendaAbertosItem[];
  sortKey: SortKey;
  sortDirection: SortDirection;
  onSort: (key: SortKey) => void;
  loading?: boolean;
  emptyMessage?: string;
};

function sortIndicator(active: boolean, direction: SortDirection): string {
  if (!active) return "↕";
  return direction === "asc" ? "↑" : "↓";
}

function rowKey(row: PedidosVendaAbertosItem): string {
  return `${row.filial}-${row.pedido}-${row.linha}-${row.produto}`;
}

function renderPrevisaoCell(
  row: PedidosVendaAbertosItem,
  onOpenModal: (row: PedidosVendaAbertosItem) => void,
) {
  const previsao = getLineOpPrevisao(row);

  if (previsao.previsaoLabel === "—") {
    return "—";
  }

  if (canOpenOpPrevisaoModal(row)) {
    return (
      <button
        type="button"
        className="pva-link-btn"
        onClick={() => onOpenModal(row)}
        title="Ver OPs utilizadas na previsão"
      >
        {previsao.previsaoLabel}
      </button>
    );
  }

  return previsao.previsaoLabel;
}

function renderCell(
  row: PedidosVendaAbertosItem,
  key: TableColumnKey,
  onOpenModal: (row: PedidosVendaAbertosItem) => void,
) {
  switch (key) {
    case "nome_cliente":
      return (
        <div className="pva-cell-stack">
          <strong>{row.nome_cliente || "—"}</strong>
          <span className="pva-cell-muted">
            {formatEntityTypeWithCodeStore(row.tipo_entidade, row.codigo_cadastro, null)}
          </span>
        </div>
      );
    case "loja_cadastro":
      return row.loja_cadastro || "—";
    case "filial":
      return row.filial || "—";
    case "pedido":
      return (
        <div className="pva-cell-stack">
          <span>{row.pedido || "—"}</span>
          <span className="pva-cell-muted">Linha {row.linha || "—"}</span>
        </div>
      );
    case "pedido_cliente":
      return row.pedido_cliente || "—";
    case "produto":
      return row.produto || "—";
    case "codigo_cliente":
      return row.codigo_cliente || "—";
    case "quantidade":
      return formatQuantity(row.quantidade);
    case "entregue":
      return formatQuantity(row.entregue);
    case "saldo":
      return formatQuantity(row.saldo);
    case "no_estoque":
      return formatQuantity(getAllocatedStock(row));
    case "data_entrega":
      return formatDisplayDate(row.data_entrega);
    case "previsao_entrega_op":
      return renderPrevisaoCell(row, onOpenModal);
    case "data_despacho":
      return row.data_despacho ? formatDisplayDate(row.data_despacho) : "Não informado";
    case "valor_aberto":
      return formatCurrency(row.valor_aberto);
    case "status":
      return (
        <div className="pva-badge-group pva-badge-group--status">
          <StatusBadge badge={getLineStatus(row)} />
        </div>
      );
    default:
      return "—";
  }
}

export function PedidosTable({
  rows,
  exportRows,
  sortKey,
  sortDirection,
  onSort,
  loading = false,
  emptyMessage = "Nenhum registro encontrado.",
}: PedidosTableProps) {
  const [exporting, setExporting] = useState(false);
  const [modalItem, setModalItem] = useState<PedidosVendaAbertosItem | null>(null);
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
    "--pva-table-font-size": `${fontSize}px`,
    "--pva-table-font-size-muted": `${Math.max(10, fontSize - 1)}px`,
    "--pva-table-badge-font-size": `${Math.max(10, fontSize - 1)}px`,
  } as CSSProperties;

  const handleExportExcel = async () => {
    if (exportRows.length === 0 || exporting) return;

    try {
      setExporting(true);
      await exportPedidosExcel(exportRows, visibleColumns);
    } finally {
      setExporting(false);
    }
  };

  return (
    <>
      <section className="pva-card pva-table-card" aria-label="Pedidos em aberto" style={tableStyle}>
        <div className="pva-table-card__toolbar">
          <p className="pva-table-card__hint">
            {visibleColumnCount} coluna(s) visível(is)
            {exportRows.length > 0 ? ` · ${exportRows.length.toLocaleString("pt-BR")} linha(s) para exportar` : ""}.
            Previsão (OP) = data em que o saldo faltante da linha seria coberto pelas OPs abertas (FIFO).
          </p>
          <div className="pva-table-card__actions">
            <ExcelExportButton
              className="pva-export-actions"
              buttonClassName="pva-btn pva-btn--ghost pva-btn--sm"
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

        <div className="pva-table-wrap">
          <table className="pva-table">
            <thead>
              <tr>
                {visibleColumns.map((column) => (
                  <th key={column.key} className={column.className}>
                    {column.sortable ? (
                      <button
                        type="button"
                        className="pva-table__sort-btn"
                        onClick={() => {
                          if (isSortableTableColumnKey(column.key)) {
                            onSort(column.key);
                          }
                        }}
                      >
                        <span>{column.label}</span>
                        <span aria-hidden="true">
                          {sortIndicator(sortKey === column.key, sortDirection)}
                        </span>
                      </button>
                    ) : (
                      column.label
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={visibleColumnCount} className="pva-table__empty">
                    Carregando…
                  </td>
                </tr>
              ) : rows.length === 0 ? (
                <tr>
                  <td colSpan={visibleColumnCount} className="pva-table__empty">
                    {emptyMessage}
                  </td>
                </tr>
              ) : (
                rows.map((row) => (
                  <tr key={rowKey(row)}>
                    {visibleColumns.map((column) => (
                      <td
                        key={column.key}
                        className={column.className}
                        data-label={column.label}
                      >
                        {renderCell(row, column.key, setModalItem)}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <OpPrevisaoModal
        item={modalItem}
        open={modalItem != null}
        onClose={() => setModalItem(null)}
      />
    </>
  );
}

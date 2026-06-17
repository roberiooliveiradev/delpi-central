import { useState, useCallback, useMemo, useEffect } from "react";
import type { ChatPresentation } from "../../../data/api/chatTypes";
import { ExpandButton } from "../ChatExpandModal";
import { buildTableRowMenuActions } from "./chatDrillDown";
import { ChatTableRowMenu } from "../ChatTableRowMenu";
import { formatCellValue, getAlignClass } from "./tableCellFormatting";
import {
  applyCategoryFilter,
  buildCategoryFilterOptions,
} from "./pipeline/presentationCategoryFilter";
import { formatChartColumnLabel } from "./pipeline/chartAxisSelection";
import { buildFieldLabelsFromTableColumns } from "./pipeline/presentationFieldLabels";
import { recordPresentationTelemetry } from "./pipeline/presentationTelemetry";
import { ChatPresentationCopyButton } from "./ChatPresentationCopyButton";
import { ChatPresentationExportButtons } from "./ChatPresentationExportButtons";
import { tablePresentationToMarkdown } from "../chatPresentation";

type TablePresentation = Extract<ChatPresentation, { type: "table" }>;

type SortConfig = {
  key: string;
  direction: "asc" | "desc";
} | null;

export function ChatRichTable({
  presentation,
  hideTitle = false,
  hideToolbar = false,
  embeddedInDashboard = false,
  onDrillDown,
}: {
  presentation: TablePresentation;
  hideTitle?: boolean;
  /** Oculta cabeçalho com ações (ex.: dentro do modal expandido). */
  hideToolbar?: boolean;
  /** Toolbar compacta alinhada (painel de itens do dashboard). */
  embeddedInDashboard?: boolean;
  onDrillDown?: (query: string) => void;
}) {
  const { title, columns: rawColumns, rows: rawRows } = presentation;
  const columns = Array.isArray(rawColumns) ? rawColumns : [];
  const rows = Array.isArray(rawRows) ? rawRows : [];
  const [sortConfig, setSortConfig] = useState<SortConfig>(null);
  const [categoryFilterKey, setCategoryFilterKey] = useState<string | null>(null);
  const [categoryFilterValue, setCategoryFilterValue] = useState<string | null>(null);
  const [rowMenu, setRowMenu] = useState<{
    anchor: { point: { x: number; y: number } };
    actions: ReturnType<typeof buildTableRowMenuActions>;
  } | null>(null);

  useEffect(() => {
    setCategoryFilterKey(null);
    setCategoryFilterValue(null);
  }, [rows, title]);

  const fieldLabels = useMemo(
    () => buildFieldLabelsFromTableColumns(columns).fieldLabels,
    [columns],
  );

  const categoryFilterOptions = useMemo(
    () =>
      buildCategoryFilterOptions(
        rows,
        columns.map((column) => column.key),
        fieldLabels,
      ),
    [columns, fieldLabels, rows],
  );

  const filteredRows = useMemo(
    () => applyCategoryFilter(rows, categoryFilterKey, categoryFilterValue),
    [categoryFilterKey, categoryFilterValue, rows],
  );

  const sortedRows = useCallback(() => {
    if (!sortConfig) return filteredRows;

    return [...filteredRows].sort((a, b) => {
      const aVal = a[sortConfig.key];
      const bVal = b[sortConfig.key];

      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return 1;
      if (bVal == null) return -1;

      const aNum = Number(aVal);
      const bNum = Number(bVal);

      if (!isNaN(aNum) && !isNaN(bNum)) {
        return sortConfig.direction === "asc" ? aNum - bNum : bNum - aNum;
      }

      const aStr = String(aVal).toLowerCase();
      const bStr = String(bVal).toLowerCase();
      const cmp = aStr.localeCompare(bStr, "pt-BR");
      return sortConfig.direction === "asc" ? cmp : -cmp;
    });
  }, [filteredRows, sortConfig]);

  function handleSort(key: string) {
    setSortConfig((prev) => {
      if (prev?.key === key) {
        return prev.direction === "asc"
          ? { key, direction: "desc" }
          : null;
      }
      return { key, direction: "asc" };
    });
  }

  const sorted = sortedRows();
  const filteredPresentation = useMemo(
    () => ({
      ...presentation,
      columns,
      rows: filteredRows,
    }),
    [columns, filteredRows, presentation],
  );

  return (
    <div
      className={[
        "mdc-rich-table",
        hideToolbar ? "mdc-rich-table--embedded" : "",
        embeddedInDashboard ? "mdc-rich-table--dashboard" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {!hideToolbar ? (
        <div className="mdc-rich-table__header">
          {hideTitle ? (
            <span className="mdc-rich-table__title" aria-hidden="true" />
          ) : (
            <span className="mdc-rich-table__title">{title}</span>
          )}
          <div className="mdc-rich-table__actions">
            {categoryFilterOptions.length > 0 ? (
              <>
                <label className="mdc-rich-chart__ux-field mdc-rich-table__filter">
                  <span>Filtrar</span>
                  <select
                    value={categoryFilterKey ?? ""}
                    onChange={(event) => {
                      setCategoryFilterKey(event.target.value || null);
                      setCategoryFilterValue(null);
                    }}
                  >
                    <option value="">Todos</option>
                    {categoryFilterOptions.map((option) => (
                      <option key={option.key} value={option.key}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                {categoryFilterKey ? (
                  <label className="mdc-rich-chart__ux-field mdc-rich-table__filter">
                    <span>{formatChartColumnLabel(categoryFilterKey, fieldLabels)}</span>
                    <select
                      value={categoryFilterValue ?? ""}
                      onChange={(event) => {
                        const value = event.target.value || null;
                        setCategoryFilterValue(value);
                        if (value) {
                          recordPresentationTelemetry("presentation_category_filter", {
                            filterKey: categoryFilterKey,
                            filterValue: value,
                            surface: "table",
                          });
                        }
                      }}
                    >
                      <option value="">Todos</option>
                      {categoryFilterOptions
                        .find((option) => option.key === categoryFilterKey)
                        ?.values.map((value) => (
                          <option key={value} value={value}>
                            {value}
                          </option>
                        ))}
                    </select>
                  </label>
                ) : null}
              </>
            ) : null}
            <ChatPresentationCopyButton
              getText={() =>
                tablePresentationToMarkdown(
                  {
                    ...presentation,
                    columns,
                    rows: filteredRows,
                  },
                  { includeTitle: true },
                )
              }
              copyAriaLabel="Copiar tabela"
              copiedAriaLabel="Tabela copiada"
            />
            <ChatPresentationExportButtons
              presentation={filteredPresentation}
              tableRows={filteredRows}
            />
            <ExpandButton presentation={presentation} onDrillDown={onDrillDown} />
          </div>
        </div>
      ) : null}

      <div className="mdc-rich-table__scroll">
        <table className="mdc-rich-table__table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className={
                    sortConfig?.key === col.key
                      ? `mdc-rich-table__th--sorted-${sortConfig.direction}`
                      : ""
                  }
                >
                  {col.label}
                  {sortConfig?.key === col.key && (
                    <span className="mdc-rich-table__sort-icon">
                      {sortConfig.direction === "asc" ? " ▲" : " ▼"}
                    </span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((row, idx) => (
              <tr
                key={idx}
                className={onDrillDown ? "mdc-rich-table__tr--clickable" : ""}
                onClick={(event) => {
                  if (!onDrillDown) return;

                  const actions = buildTableRowMenuActions(row, columns);

                  if (!actions.length) {
                    return;
                  }

                  setRowMenu({
                    anchor: { point: { x: event.clientX, y: event.clientY } },
                    actions,
                  });
                }}
                title={onDrillDown ? "Clique para ver ações" : undefined}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    data-label={col.label}
                    className={getAlignClass(
                      col.key,
                      row[col.key],
                      col.dataType,
                      row,
                    )}
                  >
                    {formatCellValue(row[col.key], col.key, col.dataType, row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {rows.length > 0 && (
        <div className="mdc-rich-table__footer">
          {rows.length} registro(s)
        </div>
      )}

      {rowMenu && onDrillDown ? (
        <ChatTableRowMenu
          actions={rowMenu.actions}
          anchor={rowMenu.anchor}
          onSelect={onDrillDown}
          onClose={() => setRowMenu(null)}
        />
      ) : null}
    </div>
  );
}

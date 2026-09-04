import { useState, useCallback, useMemo, useEffect, useRef } from "react";
import type { ChatPresentation } from "../../../data/api/chatTypes";
import {
  formatRichToolbarTemplate,
  richPresentationToolbar,
} from "../../../content/presentationVocabulary";
import { ExpandButton } from "../canvas/ChatExpandModal";
import { buildTableRowMenuActions } from "./chatDrillDown";
import { ChatTableRowMenu } from "../shared/menus/ChatTableRowMenu";
import { formatCellValue, getAlignClass } from "./tableCellFormatting";
import {
  applyPresentationRowPipeline,
  buildCategoryFilterOptions,
} from "./pipeline/presentationCategoryFilter";
import { formatChartColumnLabel } from "./pipeline/chartAxisSelection";
import { buildFieldLabelsFromTableColumns } from "./pipeline/presentationFieldLabels";
import { recordPresentationTelemetry } from "./pipeline/presentationTelemetry";
import { ChatPresentationCopyButton } from "./ChatPresentationCopyButton";
import { ChatPresentationExportButtons } from "./ChatPresentationExportButtons";
import { ChatRichSearchField } from "./ChatRichSearchField";
import type { RichTableViewState } from "./richPresentationViewState";
import { tablePresentationToMarkdown } from "../chatPresentation";
import { ChatRichUxSelect } from "./chatRichUxSelect";
import "./ChatRichSearchField.css";

type TablePresentation = Extract<ChatPresentation, { type: "table" }>;

type SortConfig = {
  key: string;
  direction: "asc" | "desc";
} | null;

function tableRowEmphasisClass(row: Record<string, unknown>): string {
  const emphasis = String(row.row_emphasis ?? row.rowEmphasis ?? "").trim();

  if (emphasis === "exclusive_mp") {
    return "mdc-rich-table__tr--exclusive-mp";
  }

  return "";
}

export function ChatRichTable({
  presentation,
  hideTitle = false,
  hideToolbar = false,
  expanded = false,
  embeddedInDashboard = false,
  initialViewState,
  onDrillDown,
}: {
  presentation: TablePresentation;
  hideTitle?: boolean;
  /** Oculta cabeçalho com ações (ex.: painel embutido). */
  hideToolbar?: boolean;
  /** Modal expandido — mantém toolbar de filtro (como ChatRichChart). */
  expanded?: boolean;
  /** Toolbar compacta alinhada (painel de itens do dashboard). */
  embeddedInDashboard?: boolean;
  /** Estado de busca/filtro preservado ao Expandir. */
  initialViewState?: RichTableViewState;
  onDrillDown?: (query: string) => void;
}) {
  const toolbarCopy = richPresentationToolbar();
  const { title, columns: rawColumns, rows: rawRows } = presentation;
  const columns = Array.isArray(rawColumns) ? rawColumns : [];
  const rows = Array.isArray(rawRows) ? rawRows : [];
  const columnKeys = useMemo(() => columns.map((column) => column.key), [columns]);
  const [sortConfig, setSortConfig] = useState<SortConfig>(null);
  const [searchQuery, setSearchQuery] = useState(initialViewState?.searchQuery ?? "");
  const [categoryFilterKey, setCategoryFilterKey] = useState<string | null>(
    initialViewState?.categoryFilterKey ?? null,
  );
  const [categoryFilterValue, setCategoryFilterValue] = useState<string | null>(
    initialViewState?.categoryFilterValue ?? null,
  );
  const skipFilterResetOnMountRef = useRef(Boolean(initialViewState));
  const [rowMenu, setRowMenu] = useState<{
    anchor: { point: { x: number; y: number } };
    actions: ReturnType<typeof buildTableRowMenuActions>;
  } | null>(null);

  useEffect(() => {
    if (skipFilterResetOnMountRef.current) {
      skipFilterResetOnMountRef.current = false;
      return;
    }

    setCategoryFilterKey(null);
    setCategoryFilterValue(null);
    setSearchQuery("");
  }, [rows, title]);

  const fieldLabels = useMemo(
    () => buildFieldLabelsFromTableColumns(columns).fieldLabels,
    [columns],
  );

  const categoryFilterOptions = useMemo(
    () => buildCategoryFilterOptions(rows, columnKeys, fieldLabels),
    [columnKeys, fieldLabels, rows],
  );

  const activeFilterOption = useMemo(
    () => categoryFilterOptions.find((option) => option.key === categoryFilterKey) ?? null,
    [categoryFilterKey, categoryFilterOptions],
  );

  const tableViewState = useMemo(
    (): RichTableViewState => ({
      searchQuery,
      categoryFilterKey,
      categoryFilterValue,
    }),
    [categoryFilterKey, categoryFilterValue, searchQuery],
  );

  const filteredRows = useMemo(
    () =>
      applyPresentationRowPipeline(rows, {
        searchQuery,
        filterKey: categoryFilterKey,
        filterValue: categoryFilterValue,
        filterMode: activeFilterOption?.mode ?? "equality",
        columnKeys,
      }),
    [
      activeFilterOption?.mode,
      categoryFilterKey,
      categoryFilterValue,
      columnKeys,
      rows,
      searchQuery,
    ],
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

  const footerLabel =
    filteredRows.length !== rows.length
      ? formatRichToolbarTemplate(toolbarCopy.footerTableFiltered, {
          visible: filteredRows.length,
          total: rows.length,
        })
      : formatRichToolbarTemplate(toolbarCopy.footerTableAll, {
          total: rows.length,
        });

  const showToolbar = !hideToolbar || expanded;

  return (
    <div
      className={[
        "mdc-rich-table",
        hideToolbar && !expanded ? "mdc-rich-table--embedded" : "",
        embeddedInDashboard ? "mdc-rich-table--dashboard" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {showToolbar ? (
        <div className="mdc-rich-table__header">
          {hideTitle ? (
            <span className="mdc-rich-table__title" aria-hidden="true" />
          ) : (
            <span className="mdc-rich-table__title">{title}</span>
          )}
          <div className="mdc-rich-table__actions">
            <ChatRichSearchField
              className="mdc-rich-table__search"
              label={toolbarCopy.searchAriaLabelTable}
              onChange={setSearchQuery}
              placeholder={toolbarCopy.searchPlaceholderTable}
              value={searchQuery}
            />
            {categoryFilterOptions.length > 0 ? (
              <>
                <ChatRichUxSelect
                  className="mdc-rich-table__filter"
                  label={toolbarCopy.filterColumnLabel}
                  value={categoryFilterKey ?? ""}
                  onChange={(nextKey) => {
                    setCategoryFilterKey(nextKey || null);
                    setCategoryFilterValue(null);
                  }}
                  options={categoryFilterOptions.map((option) => ({
                    value: option.key,
                    label: option.label,
                  }))}
                />
                {categoryFilterKey && activeFilterOption?.mode === "contains" ? (
                  <ChatRichSearchField
                    className="mdc-rich-table__filter-contains"
                    label={toolbarCopy.filterContainsLabel}
                    onChange={(value) => {
                      setCategoryFilterValue(value || null);
                      if (value) {
                        recordPresentationTelemetry("presentation_category_filter", {
                          filterKey: categoryFilterKey,
                          filterValue: value,
                          surface: "table",
                          mode: "contains",
                        });
                      }
                    }}
                    placeholder={toolbarCopy.filterContainsPlaceholder}
                    value={categoryFilterValue ?? ""}
                  />
                ) : null}
                {categoryFilterKey && activeFilterOption?.mode === "equality" ? (
                  <ChatRichUxSelect
                    className="mdc-rich-table__filter"
                    label={formatChartColumnLabel(categoryFilterKey, fieldLabels)}
                    value={categoryFilterValue ?? ""}
                    onChange={(value) => {
                      setCategoryFilterValue(value || null);
                      if (value) {
                        recordPresentationTelemetry("presentation_category_filter", {
                          filterKey: categoryFilterKey,
                          filterValue: value,
                          surface: "table",
                          mode: "equality",
                        });
                      }
                    }}
                    options={activeFilterOption.values.map((value) => ({
                      value,
                      label: value,
                    }))}
                  />
                ) : null}
              </>
            ) : null}
            <ChatPresentationCopyButton
              getText={() =>
                tablePresentationToMarkdown(filteredPresentation, { includeTitle: true })
              }
              copyAriaLabel="Copiar tabela"
              copiedAriaLabel="Tabela copiada"
            />
            <ChatPresentationExportButtons
              presentation={filteredPresentation}
              tableRows={filteredRows}
            />
            {!expanded ? (
              <ExpandButton
                presentation={presentation}
                tableViewState={tableViewState}
                onDrillDown={onDrillDown}
              />
            ) : null}
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
                className={[
                  tableRowEmphasisClass(row),
                  onDrillDown ? "mdc-rich-table__tr--clickable" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
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
                    onClick={(event) => {
                      if (!onDrillDown) return;

                      const actions = buildTableRowMenuActions(row, columns, col);

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
                    {formatCellValue(row[col.key], col.key, col.dataType, row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {rows.length > 0 && (
        <div className="mdc-rich-table__footer">{footerLabel}</div>
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

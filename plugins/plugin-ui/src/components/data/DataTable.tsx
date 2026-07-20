import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type DragEvent,
  type KeyboardEvent as ReactKeyboardEvent,
  type MouseEvent,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
} from "react";

import { HelpTooltip } from "../help/HelpTooltip";
import {
  delpiUiClass,
  resolveDataTableColumnClassName,
  withBemModifier,
} from "../../utils/delpiUiClass";
import {
  autofitDataTableColumn,
  clampColumnWidthPx,
  startDataTableColumnResize,
  type DataTableColumnWidths,
} from "./dataTableColumnResize";
import {
  isCellSelected,
  isColumnSelected,
  isRowSelected,
  primaryColumnKey,
  resolveCellSelection,
  resolveColumnSelection,
  resolveRowSelection,
  selectionFromColumnKey,
  selectionToTsv,
  type DataTableSelection,
  type DataTableSelectionModifiers,
} from "./dataTableSelection";

export type { DataTableColumnWidths, DataTableSelection };

export type DataTableColumn<T> = {
  key: string;
  header: string;
  headerHint?: string;
  render: (row: T) => ReactNode;
  className?: string;
  align?: "left" | "right" | "center";
  /** Impede propagação do clique da linha (ex.: coluna de ações). */
  interactive?: boolean;
  sortable?: boolean;
  sortValue?: (row: T) => string | number | null | undefined;
  mobileLabel?: string;
  /** Conteúdo visual anterior ao título (ícone de tipo, status etc.). */
  headerPrefix?: ReactNode;
};

export type DataTableClassNames = {
  wrapSection: string;
  wrapEmbedded: string;
  /** Wrapper padrão (sem --section/--embedded). */
  wrap?: string;
  /** Container externo opcional (ex.: dm-datatable). */
  outerRoot?: string;
  /** Área com scroll horizontal opcional (ex.: dm-datatable__scroll). */
  scrollWrap?: string;
  table: string;
  /** Classe completa da tabela quando há onRowClick (substitui modificadores --clickable). */
  tableClickable?: string;
  /** Classe extra em th sortable (ex.: dm-datatable__col--sortable). */
  sortableColumn?: string;
  empty: string;
  /** Quando true, envolve o texto vazio em div dentro do td. */
  emptyInnerWrapper?: boolean;
  headerLabel: string;
  headerText: string;
  headerHelp: string;
  sortButton: string;
  sortButtonActive: string;
  sortIndicator: string;
  rowClickable: string;
  /** Tabela com `--sortable` dual (prefix + delpi-ui). */
  sortableTable?: string;
  /** Tabela com `--compact` dual (prefix + delpi-ui). */
  compactTable?: string;
  /** Célula/coluna numérica alinhada à direita. */
  colNumeric?: string;
  /** Coluna larga (descrição / texto). */
  colWide?: string;
};

export type DataTableLabels = {
  emptyMessage: string;
  loadingMessage: string;
  sortByAriaLabel: (header: string) => string;
  headerHelpAriaLabel: (header: string) => string;
};

export type DataTableProps<T> = {
  columns: DataTableColumn<T>[];
  rows: T[];
  rowKey: (row: T, index: number) => string;
  emptyMessage?: string;
  loading?: boolean;
  onRowClick?: (row: T) => void;
  getRowClassName?: (row: T) => string | undefined;
  sortKey?: string | null;
  sortDirection?: "asc" | "desc";
  onSortChange?: (columnKey: string) => void;
  layout?: "section" | "embedded" | "scroll";
  mode?: "default" | "grid-preview";
  rowClickRole?: "button" | "none";
  onHeaderClick?: (column: DataTableColumn<T>, modifiers: DataTableSelectionModifiers) => void;
  onHeaderContextMenu?: (event: MouseEvent<HTMLElement>, column: DataTableColumn<T>) => void;
  onCellClick?: (
    row: T,
    column: DataTableColumn<T>,
    rowIndex: number,
    modifiers: DataTableSelectionModifiers,
  ) => void;
  onCellContextMenu?: (
    event: MouseEvent<HTMLElement>,
    row: T,
    column: DataTableColumn<T>,
    rowIndex: number,
  ) => void;
  getHeaderClassName?: (column: DataTableColumn<T>) => string | undefined;
  getCellClassName?: (
    row: T,
    column: DataTableColumn<T>,
    rowIndex: number,
  ) => string | undefined;
  /** @deprecated Prefira `selection` + `onSelectionChange`. */
  selectedColumnKey?: string | null;
  selection?: DataTableSelection | null;
  onSelectionChange?: (selection: DataTableSelection | null) => void;
  /** Quebra de texto automática (default: true em grid-preview). */
  wrapText?: boolean;
  /** Larguras em px por chave de coluna. */
  columnWidths?: DataTableColumnWidths;
  onColumnWidthsChange?: (widths: DataTableColumnWidths) => void;
  resizableColumns?: boolean;
  enableColumnReorder?: boolean;
  onColumnOrderChange?: (columnKeys: string[]) => void;
  enableCopySelection?: boolean;
  /** Coluna visual de índice; não altera o shape das linhas. */
  indexColumn?: { header?: string; ariaLabel?: string; startAt?: number };
  classNames: DataTableClassNames;
  labels: DataTableLabels;
};

export function dataTableBemClasses(prefix: string): DataTableClassNames {
  const table = `${prefix}-table`;
  const ui = "delpi-ui-table";
  const wrap = `${prefix}-table-wrap`;
  const uiWrap = "delpi-ui-table-wrap";
  const tableDual = delpiUiClass(table, ui);
  return {
    wrap: delpiUiClass(wrap, uiWrap),
    wrapSection: delpiUiClass(
      `${wrap} ${wrap}--section`,
      `${uiWrap} ${uiWrap}--section`,
    ),
    wrapEmbedded: delpiUiClass(
      `${wrap} ${wrap}--embedded`,
      `${uiWrap} ${uiWrap}--embedded`,
    ),
    table: tableDual,
    sortableTable: withBemModifier(tableDual, "sortable"),
    compactTable: withBemModifier(tableDual, "compact"),
    colNumeric: delpiUiClass(`${table}__col--numeric`, `${ui}__col--numeric`),
    colWide: delpiUiClass(`${table}__col--wide`, `${ui}__col--wide`),
    empty: delpiUiClass(`${table}__empty`, `${ui}__empty`),
    headerLabel: delpiUiClass(`${table}__header-label`, `${ui}__header-label`),
    headerText: delpiUiClass(`${table}__header-text`, `${ui}__header-text`),
    headerHelp: delpiUiClass(`${table}__header-help`, `${ui}__header-help`),
    sortButton: delpiUiClass(`${table}__sort-button`, `${ui}__sort-button`),
    sortButtonActive: delpiUiClass(
      `${table}__sort-button ${table}__sort-button--active`,
      `${ui}__sort-button ${ui}__sort-button--active`,
    ),
    sortIndicator: delpiUiClass(`${table}__sort-indicator`, `${ui}__sort-indicator`),
    rowClickable: delpiUiClass(`${table}__row--clickable`, `${ui}__row--clickable`),
  };
}

function buildTableClassName(
  classNames: DataTableClassNames,
  layout: "section" | "embedded" | "scroll",
  isSortable: boolean,
  clickable: boolean,
  mode: "default" | "grid-preview",
  wrapText: boolean,
  hasFixedWidths: boolean,
): string {
  if (clickable && classNames.tableClickable) {
    return classNames.tableClickable;
  }

  const tableTokens = classNames.table.split(/\s+/).filter(Boolean);
  return [
    classNames.table,
    ...tableTokens.flatMap((token) => {
      const modifiers: string[] = [];
      if (layout === "section") modifiers.push(`${token}--section`);
      if (isSortable) modifiers.push(`${token}--sortable`);
      if (clickable) modifiers.push(`${token}--clickable`);
      if (mode === "grid-preview") modifiers.push(`${token}--grid-preview`);
      if (wrapText) modifiers.push(`${token}--wrap`);
      if (hasFixedWidths) modifiers.push(`${token}--fixed-cols`);
      return modifiers;
    }),
  ]
    .filter(Boolean)
    .join(" ");
}

function renderEmptyCell(message: string, colSpan: number, classNames: DataTableClassNames) {
  const content = classNames.emptyInnerWrapper ? (
    <div className={classNames.empty}>{message}</div>
  ) : (
    message
  );

  return (
    <tr>
      <td colSpan={colSpan} className={classNames.emptyInnerWrapper ? undefined : classNames.empty}>
        {content}
      </td>
    </tr>
  );
}

function wrapTableMarkup(
  classNames: DataTableClassNames,
  layout: "section" | "embedded" | "scroll",
  table: ReactNode,
): ReactNode {
  if (layout === "scroll" && classNames.scrollWrap) {
    const scroll = <div className={classNames.scrollWrap}>{table}</div>;
    return classNames.outerRoot ? <div className={classNames.outerRoot}>{scroll}</div> : scroll;
  }

  const wrapClass = layout === "section" ? classNames.wrapSection : classNames.wrapEmbedded;
  const inner = <div className={wrapClass}>{table}</div>;
  return classNames.outerRoot ? <div className={classNames.outerRoot}>{inner}</div> : inner;
}

function renderColumnHeader<T>(
  column: DataTableColumn<T>,
  classNames: DataTableClassNames,
  labels: DataTableLabels,
) {
  return (
    <span className={classNames.headerLabel}>
      {column.headerPrefix}
      <span className={classNames.headerText}>{column.header}</span>
      {column.headerHint ? (
        <HelpTooltip
          content={column.headerHint}
          ariaLabel={labels.headerHelpAriaLabel(column.header)}
          className={classNames.headerHelp}
        />
      ) : null}
    </span>
  );
}

function modifiersFromMouseEvent(event: {
  ctrlKey: boolean;
  metaKey: boolean;
  shiftKey: boolean;
}): DataTableSelectionModifiers {
  return {
    toggle: event.ctrlKey || event.metaKey,
    range: event.shiftKey,
  };
}

function reorderColumnKeys(keys: string[], fromKey: string, toKey: string): string[] {
  if (fromKey === toKey) return keys;
  const from = keys.indexOf(fromKey);
  const to = keys.indexOf(toKey);
  if (from < 0 || to < 0) return keys;
  const next = [...keys];
  const [moved] = next.splice(from, 1);
  next.splice(to, 0, moved!);
  return next;
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  emptyMessage,
  loading = false,
  onRowClick,
  getRowClassName,
  sortKey = null,
  sortDirection = "asc",
  onSortChange,
  layout = "embedded",
  mode = "default",
  rowClickRole = "none",
  onHeaderClick,
  onHeaderContextMenu,
  onCellClick,
  onCellContextMenu,
  getHeaderClassName,
  getCellClassName,
  selectedColumnKey = null,
  selection: selectionProp = null,
  onSelectionChange,
  wrapText: wrapTextProp,
  columnWidths: columnWidthsProp,
  onColumnWidthsChange,
  resizableColumns = false,
  enableColumnReorder = false,
  onColumnOrderChange,
  enableCopySelection = false,
  indexColumn,
  classNames,
  labels,
}: DataTableProps<T>) {
  const tableRef = useRef<HTMLTableElement | null>(null);
  const [dragColumnKey, setDragColumnKey] = useState<string | null>(null);
  const [localWidths, setLocalWidths] = useState<DataTableColumnWidths>({});
  const wrapText = wrapTextProp ?? mode === "grid-preview";
  const columnWidths = columnWidthsProp ?? localWidths;
  const hasFixedWidths = Object.keys(columnWidths).length > 0;

  const resolvedSelection =
    selectionProp ?? selectionFromColumnKey(selectedColumnKey);

  const isSortable = Boolean(onSortChange && columns.some((column) => column.sortable));
  const resolvedEmptyMessage = emptyMessage ?? labels.emptyMessage;
  const tableClassName = buildTableClassName(
    classNames,
    layout,
    isSortable,
    Boolean(onRowClick),
    mode,
    wrapText,
    hasFixedWidths,
  );
  const columnKeys = useMemo(() => columns.map((column) => column.key), [columns]);

  const commitSelection = useCallback(
    (next: DataTableSelection | null) => {
      onSelectionChange?.(next);
    },
    [onSelectionChange],
  );

  const commitWidth = useCallback(
    (columnKey: string, widthPx: number) => {
      const next = { ...columnWidths, [columnKey]: clampColumnWidthPx(widthPx) };
      if (onColumnWidthsChange) {
        onColumnWidthsChange(next);
      } else {
        setLocalWidths(next);
      }
    },
    [columnWidths, onColumnWidthsChange],
  );

  const handleHeaderSelect = useCallback(
    (column: DataTableColumn<T>, modifiers: DataTableSelectionModifiers) => {
      onHeaderClick?.(column, modifiers);
      if (!onSelectionChange) return;
      commitSelection(resolveColumnSelection(resolvedSelection, column.key, columnKeys, modifiers));
    },
    [commitSelection, columnKeys, onHeaderClick, onSelectionChange, resolvedSelection],
  );

  const handleRowSelect = useCallback(
    (rowIndex: number, modifiers: DataTableSelectionModifiers) => {
      if (!onSelectionChange) return;
      commitSelection(resolveRowSelection(resolvedSelection, rowIndex, modifiers));
    },
    [commitSelection, onSelectionChange, resolvedSelection],
  );

  const handleCellSelect = useCallback(
    (
      row: T,
      column: DataTableColumn<T>,
      rowIndex: number,
      modifiers: DataTableSelectionModifiers,
    ) => {
      onCellClick?.(row, column, rowIndex, modifiers);
      if (!onSelectionChange) return;
      commitSelection(
        resolveCellSelection(resolvedSelection, { rowIndex, columnKey: column.key }, modifiers),
      );
    },
    [commitSelection, onCellClick, onSelectionChange, resolvedSelection],
  );

  useEffect(() => {
    if (!enableCopySelection || !resolvedSelection) return;

    const onCopy = (event: ClipboardEvent) => {
      const target = event.target;
      if (
        target instanceof HTMLElement &&
        target.closest("input, textarea, [contenteditable='true']")
      ) {
        return;
      }
      const recordRows = rows as Array<Record<string, unknown>>;
      const tsv = selectionToTsv(resolvedSelection, recordRows, columnKeys);
      if (!tsv) return;
      event.clipboardData?.setData("text/plain", tsv);
      event.preventDefault();
    };

    document.addEventListener("copy", onCopy);
    return () => document.removeEventListener("copy", onCopy);
  }, [columnKeys, enableCopySelection, resolvedSelection, rows]);

  if (loading) {
    return wrapTableMarkup(
      classNames,
      layout,
      <table className={tableClassName}>
        <tbody>
          {renderEmptyCell(labels.loadingMessage, columns.length + (indexColumn ? 1 : 0), classNames)}
        </tbody>
      </table>,
    );
  }

  if (rows.length === 0) {
    return wrapTableMarkup(
      classNames,
      layout,
      <table className={tableClassName}>
        <tbody>
          {renderEmptyCell(
            resolvedEmptyMessage,
            columns.length + (indexColumn ? 1 : 0),
            classNames,
          )}
        </tbody>
      </table>,
    );
  }

  const startResize = (event: ReactPointerEvent<HTMLElement>, columnKey: string) => {
    const th = (event.currentTarget as HTMLElement).closest("th");
    const current =
      columnWidths[columnKey] ?? th?.getBoundingClientRect().width ?? MIN_FALLBACK_WIDTH;
    startDataTableColumnResize({
      event: event.nativeEvent,
      columnKey,
      currentWidthPx: current,
      onResize: commitWidth,
    });
  };

  const onHeaderDragStart = (event: DragEvent<HTMLElement>, columnKey: string) => {
    if (!enableColumnReorder || !onColumnOrderChange) return;
    setDragColumnKey(columnKey);
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", columnKey);
  };

  const onHeaderDrop = (event: DragEvent<HTMLElement>, targetKey: string) => {
    if (!enableColumnReorder || !onColumnOrderChange) return;
    event.preventDefault();
    const fromKey = dragColumnKey || event.dataTransfer.getData("text/plain");
    setDragColumnKey(null);
    if (!fromKey) return;
    onColumnOrderChange(reorderColumnKeys(columnKeys, fromKey, targetKey));
  };

  return wrapTableMarkup(
    classNames,
    layout,
    <table
      ref={tableRef}
      className={tableClassName}
      data-selection-kind={resolvedSelection?.kind}
      data-primary-column={primaryColumnKey(resolvedSelection) ?? undefined}
    >
      {hasFixedWidths ? (
        <colgroup>
          {indexColumn ? <col style={{ width: 44 }} /> : null}
          {columns.map((column) => (
            <col
              key={column.key}
              style={
                columnWidths[column.key] != null
                  ? { width: columnWidths[column.key] }
                  : undefined
              }
            />
          ))}
        </colgroup>
      ) : null}
      <thead>
        <tr>
          {indexColumn ? (
            <th
              scope="col"
              className="delpi-ui-table__index-col"
              aria-label={indexColumn.ariaLabel ?? "Índice"}
            >
              {indexColumn.header ?? "#"}
            </th>
          ) : null}
          {columns.map((column) => {
            const isSorted = sortKey === column.key;
            const columnSelected = isColumnSelected(resolvedSelection, column.key);
            const columnClass = resolveDataTableColumnClassName(column.className);
            const headerClass = [
              columnClass,
              getHeaderClassName?.(column),
              column.sortable && classNames.sortableColumn ? classNames.sortableColumn : "",
              columnSelected ? "delpi-ui-table__column--selected" : "",
              dragColumnKey === column.key ? "delpi-ui-table__column--dragging" : "",
            ]
              .filter(Boolean)
              .join(" ");

            return (
              <th
                key={column.key}
                scope="col"
                className={headerClass || undefined}
                data-align={column.align}
                data-column-key={column.key}
                aria-selected={columnSelected || undefined}
                tabIndex={onHeaderClick || onSelectionChange ? 0 : undefined}
                draggable={enableColumnReorder && Boolean(onColumnOrderChange)}
                onDragStart={(event) => onHeaderDragStart(event, column.key)}
                onDragOver={(event) => {
                  if (enableColumnReorder && onColumnOrderChange) event.preventDefault();
                }}
                onDrop={(event) => onHeaderDrop(event, column.key)}
                onDragEnd={() => setDragColumnKey(null)}
                onClick={(event) => {
                  if ((event.target as HTMLElement).closest("[data-column-resize-handle]")) {
                    return;
                  }
                  handleHeaderSelect(column, modifiersFromMouseEvent(event));
                }}
                onContextMenu={
                  onHeaderContextMenu
                    ? (event) => onHeaderContextMenu(event, column)
                    : undefined
                }
                onKeyDown={
                  onHeaderClick || onSelectionChange
                    ? (event: ReactKeyboardEvent<HTMLElement>) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          handleHeaderSelect(column, modifiersFromMouseEvent(event));
                        }
                      }
                    : undefined
                }
                aria-sort={
                  column.sortable
                    ? isSorted
                      ? sortDirection === "asc"
                        ? "ascending"
                        : "descending"
                      : "none"
                    : undefined
                }
                style={
                  columnWidths[column.key] != null
                    ? { width: columnWidths[column.key], minWidth: columnWidths[column.key] }
                    : undefined
                }
              >
                {column.sortable && onSortChange ? (
                  <button
                    type="button"
                    className={isSorted ? classNames.sortButtonActive : classNames.sortButton}
                    onClick={(event) => {
                      event.stopPropagation();
                      onSortChange(column.key);
                    }}
                    aria-label={labels.sortByAriaLabel(column.header)}
                  >
                    {renderColumnHeader(column, classNames, labels)}
                    <span className={classNames.sortIndicator} aria-hidden="true">
                      {isSorted ? (sortDirection === "asc" ? "↑" : "↓") : "↕"}
                    </span>
                  </button>
                ) : (
                  renderColumnHeader(column, classNames, labels)
                )}
                {resizableColumns ? (
                  <span
                    className="delpi-ui-table__column-resize-handle"
                    role="separator"
                    aria-orientation="vertical"
                    aria-label={`Redimensionar coluna ${column.header}`}
                    data-column-resize-handle="true"
                    onPointerDown={(event) => startResize(event, column.key)}
                    onDoubleClick={(event) => {
                      event.preventDefault();
                      event.stopPropagation();
                      autofitDataTableColumn({
                        table: tableRef.current,
                        columnKey: column.key,
                        onResize: commitWidth,
                      });
                    }}
                  />
                ) : null}
              </th>
            );
          })}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, index) => {
          const rowSelected = isRowSelected(resolvedSelection, index);
          const rowClass = [
            getRowClassName?.(row),
            onRowClick ? classNames.rowClickable : "",
            rowSelected ? "delpi-ui-table__row--selected" : "",
          ]
            .filter(Boolean)
            .join(" ");

          return (
            <tr
              key={rowKey(row, index)}
              className={rowClass || undefined}
              aria-selected={rowSelected || undefined}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              tabIndex={onRowClick ? 0 : undefined}
              role={onRowClick && rowClickRole === "button" ? "button" : undefined}
              onKeyDown={
                onRowClick
                  ? (event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        onRowClick(row);
                      }
                    }
                  : undefined
              }
            >
              {indexColumn ? (
                <td
                  className="delpi-ui-table__index-col"
                  data-label={indexColumn.ariaLabel ?? "Índice"}
                  tabIndex={onSelectionChange ? 0 : undefined}
                  aria-selected={
                    resolvedSelection?.kind === "row" &&
                    resolvedSelection.indices.includes(index)
                      ? true
                      : undefined
                  }
                  onClick={
                    onSelectionChange
                      ? (event) => {
                          event.stopPropagation();
                          handleRowSelect(index, modifiersFromMouseEvent(event));
                        }
                      : undefined
                  }
                  onKeyDown={
                    onSelectionChange
                      ? (event) => {
                          if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            handleRowSelect(index, modifiersFromMouseEvent(event));
                          }
                        }
                      : undefined
                  }
                >
                  {(indexColumn.startAt ?? 1) + index}
                </td>
              ) : null}
              {columns.map((column) => {
                const cellSelected = isCellSelected(resolvedSelection, index, column.key);
                return (
                  <td
                    key={column.key}
                    className={[
                      resolveDataTableColumnClassName(column.className),
                      getCellClassName?.(row, column, index),
                      cellSelected ? "delpi-ui-table__cell--selected" : "",
                      isColumnSelected(resolvedSelection, column.key)
                        ? "delpi-ui-table__column--selected"
                        : "",
                    ]
                      .filter(Boolean)
                      .join(" ") || undefined}
                    data-label={column.mobileLabel ?? column.header}
                    data-align={column.align}
                    data-column-key={column.key}
                    data-interactive={column.interactive ? "true" : undefined}
                    aria-selected={cellSelected || undefined}
                    tabIndex={onCellClick || onSelectionChange ? 0 : undefined}
                    onClick={
                      column.interactive || onCellClick || onSelectionChange
                        ? (event) => {
                            if (column.interactive) event.stopPropagation();
                            handleCellSelect(
                              row,
                              column,
                              index,
                              modifiersFromMouseEvent(event),
                            );
                          }
                        : undefined
                    }
                    onContextMenu={
                      onCellContextMenu
                        ? (event) => onCellContextMenu(event, row, column, index)
                        : undefined
                    }
                    onKeyDown={
                      onCellClick || onSelectionChange
                        ? (event) => {
                            if (event.key === "Enter" || event.key === " ") {
                              event.preventDefault();
                              handleCellSelect(
                                row,
                                column,
                                index,
                                modifiersFromMouseEvent(event),
                              );
                            }
                          }
                        : undefined
                    }
                    style={
                      columnWidths[column.key] != null
                        ? {
                            width: columnWidths[column.key],
                            minWidth: columnWidths[column.key],
                          }
                        : undefined
                    }
                  >
                    {column.render(row)}
                  </td>
                );
              })}
            </tr>
          );
        })}
      </tbody>
    </table>,
  );
}

const MIN_FALLBACK_WIDTH = 120;

export type DashboardDataTableProps<T> = Omit<DataTableProps<T>, "classNames" | "labels">;

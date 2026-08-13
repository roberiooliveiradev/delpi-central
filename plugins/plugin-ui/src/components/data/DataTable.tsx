import {
  Fragment,
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
  applyTransparentColumnDragImage,
  reorderColumnKeysWithEdge,
  resolveColumnDropEdge,
  type ColumnDropEdge,
} from "./dataTableColumnReorder";
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
  /**
   * Cell hosts its own pointer target (link/button/control).
   * Default: stops `onRowClick` (`rowClick: "stop"`).
   * Use only when the cell destination differs from the row detail,
   * or set `rowClick: "propagate"` when the cell intentionally shares the row action.
   * Never set `interactive: true` without a real handler (orphans cancel row navigation).
   */
  interactive?: boolean;
  /**
   * Whether cell click stops the row click.
   * Defaults to `"stop"` when `interactive` is true; `"propagate"` keeps row navigation.
   */
  rowClick?: "stop" | "propagate";
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
  /** Coluna de ações (nowrap). */
  colActions?: string;
  /** Grupo horizontal de botões na célula de ações. */
  actions?: string;
  /** Texto secundário dentro da célula. */
  sub?: string;
  /** Linha em modo edição inline. */
  rowEditing?: string;
  /** Linha de detalhe expandida (`renderExpandedRow`). */
  detailRow?: string;
  /** Célula que envolve o conteúdo expandido. */
  detailCell?: string;
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
  /** Chave da linha expandida (controlado; tipicamente uma por vez). */
  expandedRowKey?: string | null;
  onExpandedRowKeyChange?: (key: string | null) => void;
  /** Conteúdo da linha de detalhe sob a row expandida. */
  renderExpandedRow?: (row: T, index: number) => ReactNode;
  /** Default: true quando `renderExpandedRow` existe. */
  isRowExpandable?: (row: T) => boolean;
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
    colActions: delpiUiClass(`${table}__actions-col`, `${ui}__actions-col`),
    actions: delpiUiClass(`${table}__actions`, `${ui}__actions`),
    sub: delpiUiClass(`${table}__sub`, `${ui}__sub`),
    rowEditing: delpiUiClass(`${table}__row--editing`, `${ui}__row--editing`),
    detailRow: delpiUiClass(`${table}__detail-row`, `${ui}__detail-row`),
    detailCell: delpiUiClass(`${table}__detail-cell`, `${ui}__detail-cell`),
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
  const headerText =
    column.headerHint != null && column.headerHint !== "" ? (
      <HelpTooltip
        content={column.headerHint}
        ariaLabel={labels.headerHelpAriaLabel(column.header)}
        wrap
        placement="bottom"
        className={classNames.headerHelp}
      >
        <span className={`${classNames.headerText} delpi-ui-section-hint-label`}>
          {column.header}
        </span>
      </HelpTooltip>
    ) : (
      <span className={classNames.headerText}>{column.header}</span>
    );

  return (
    <span className={classNames.headerLabel}>
      {column.headerPrefix ? <span>{column.headerPrefix}</span> : null}
      {headerText}
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
  expandedRowKey = null,
  onExpandedRowKeyChange,
  renderExpandedRow,
  isRowExpandable,
  classNames,
  labels,
}: DataTableProps<T>) {
  const tableRef = useRef<HTMLTableElement | null>(null);
  const [dragColumnKey, setDragColumnKey] = useState<string | null>(null);
  const [holdColumnKey, setHoldColumnKey] = useState<string | null>(null);
  const [dropTargetKey, setDropTargetKey] = useState<string | null>(null);
  const [dropEdge, setDropEdge] = useState<ColumnDropEdge>("before");
  const [localWidths, setLocalWidths] = useState<DataTableColumnWidths>({});
  const wrapText = wrapTextProp ?? mode === "grid-preview";
  const columnWidths = columnWidthsProp ?? localWidths;
  const hasFixedWidths = Object.keys(columnWidths).length > 0;

  const resolvedSelection =
    selectionProp ?? selectionFromColumnKey(selectedColumnKey);

  const isSortable = Boolean(onSortChange && columns.some((column) => column.sortable));
  const resolvedEmptyMessage = emptyMessage ?? labels.emptyMessage;
  const tableClassName = [
    buildTableClassName(
      classNames,
      layout,
      isSortable,
      Boolean(onRowClick),
      mode,
      wrapText,
      hasFixedWidths,
    ),
    enableColumnReorder && onColumnOrderChange ? "delpi-ui-table--column-reorder" : "",
    dragColumnKey ? "delpi-ui-table--column-reordering" : "",
  ]
    .filter(Boolean)
    .join(" ");
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

  const clearColumnDragState = useCallback(() => {
    setDragColumnKey(null);
    setHoldColumnKey(null);
    setDropTargetKey(null);
  }, []);

  const onHeaderDragStart = (event: DragEvent<HTMLElement>, columnKey: string) => {
    if (!enableColumnReorder || !onColumnOrderChange) return;
    if ((event.target as HTMLElement).closest("[data-column-resize-handle]")) {
      event.preventDefault();
      return;
    }
    setHoldColumnKey(null);
    setDragColumnKey(columnKey);
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", columnKey);
    applyTransparentColumnDragImage(event.dataTransfer);
  };

  const onHeaderDragOver = (event: DragEvent<HTMLElement>, targetKey: string) => {
    if (!enableColumnReorder || !onColumnOrderChange || !dragColumnKey) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
    if (targetKey === dragColumnKey) {
      setDropTargetKey(null);
      return;
    }
    const edge = resolveColumnDropEdge(
      event.clientX,
      event.currentTarget.getBoundingClientRect(),
    );
    setDropTargetKey(targetKey);
    setDropEdge(edge);
  };

  const onHeaderDrop = (event: DragEvent<HTMLElement>, targetKey: string) => {
    if (!enableColumnReorder || !onColumnOrderChange) return;
    event.preventDefault();
    const fromKey = dragColumnKey || event.dataTransfer.getData("text/plain");
    const edge = resolveColumnDropEdge(
      event.clientX,
      event.currentTarget.getBoundingClientRect(),
    );
    clearColumnDragState();
    if (!fromKey) return;
    onColumnOrderChange(reorderColumnKeysWithEdge(columnKeys, fromKey, targetKey, edge));
  };

  const activeColumnKey = dragColumnKey ?? holdColumnKey;

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
            const isActiveColumn = activeColumnKey === column.key;
            const isDropTarget = dropTargetKey === column.key && dragColumnKey !== column.key;
            const headerClass = [
              columnClass,
              getHeaderClassName?.(column),
              column.sortable && classNames.sortableColumn ? classNames.sortableColumn : "",
              columnSelected ? "delpi-ui-table__column--selected" : "",
              isActiveColumn ? "delpi-ui-table__column--dragging" : "",
              isDropTarget && dropEdge === "before"
                ? "delpi-ui-table__column--drop-before"
                : "",
              isDropTarget && dropEdge === "after"
                ? "delpi-ui-table__column--drop-after"
                : "",
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
                aria-grabbed={dragColumnKey === column.key || undefined}
                tabIndex={onHeaderClick || onSelectionChange ? 0 : undefined}
                draggable={enableColumnReorder && Boolean(onColumnOrderChange)}
                onPointerDown={(event) => {
                  if (!enableColumnReorder || !onColumnOrderChange) return;
                  if ((event.target as HTMLElement).closest("[data-column-resize-handle]")) {
                    return;
                  }
                  if (event.button !== 0) return;
                  setHoldColumnKey(column.key);
                }}
                onPointerUp={() => {
                  if (!dragColumnKey) setHoldColumnKey(null);
                }}
                onPointerCancel={() => {
                  if (!dragColumnKey) setHoldColumnKey(null);
                }}
                onDragStart={(event) => onHeaderDragStart(event, column.key)}
                onDragOver={(event) => onHeaderDragOver(event, column.key)}
                onDragLeave={() => {
                  if (dropTargetKey === column.key) setDropTargetKey(null);
                }}
                onDrop={(event) => onHeaderDrop(event, column.key)}
                onDragEnd={() => clearColumnDragState()}
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
          const key = rowKey(row, index);
          const rowSelected = isRowSelected(resolvedSelection, index);
          const expandable =
            Boolean(renderExpandedRow) && (isRowExpandable ? isRowExpandable(row) : true);
          const isExpanded = expandable && expandedRowKey != null && expandedRowKey === key;
          const colSpan = columns.length + (indexColumn ? 1 : 0);
          const rowClass = [
            getRowClassName?.(row),
            onRowClick ? classNames.rowClickable : "",
            rowSelected ? "delpi-ui-table__row--selected" : "",
            isExpanded ? "delpi-ui-table__row--expanded" : "",
          ]
            .filter(Boolean)
            .join(" ");

          return (
            <Fragment key={key}>
              <tr
                className={rowClass || undefined}
                aria-selected={rowSelected || undefined}
                aria-expanded={expandable ? isExpanded : undefined}
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
                  const isActiveColumn = activeColumnKey === column.key;
                  const isDropTarget =
                    dropTargetKey === column.key && dragColumnKey !== column.key;
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
                        isActiveColumn ? "delpi-ui-table__column--dragging" : "",
                        isDropTarget && dropEdge === "before"
                          ? "delpi-ui-table__column--drop-before"
                          : "",
                        isDropTarget && dropEdge === "after"
                          ? "delpi-ui-table__column--drop-after"
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
                        column.interactive ||
                        column.rowClick === "stop" ||
                        onCellClick ||
                        onSelectionChange
                          ? (event) => {
                              const stopRowClick =
                                column.rowClick === "stop" ||
                                (Boolean(column.interactive) && column.rowClick !== "propagate");
                              if (stopRowClick) event.stopPropagation();
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
              {isExpanded && renderExpandedRow ? (
                <tr className={classNames.detailRow ?? "delpi-ui-table__detail-row"}>
                  <td
                    className={classNames.detailCell ?? "delpi-ui-table__detail-cell"}
                    colSpan={colSpan}
                    onClick={(event) => event.stopPropagation()}
                  >
                    {renderExpandedRow(row, index)}
                  </td>
                </tr>
              ) : null}
            </Fragment>
          );
        })}
      </tbody>
    </table>,
  );
}

const MIN_FALLBACK_WIDTH = 120;

export type DashboardDataTableProps<T> = Omit<DataTableProps<T>, "classNames" | "labels">;

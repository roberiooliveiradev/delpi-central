import type { MouseEvent, ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";
import {
  delpiUiClass,
  resolveDataTableColumnClassName,
  withBemModifier,
} from "../../utils/delpiUiClass";

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
  /** Célula/coluna numérica alinhada à direita. */
  colNumeric?: string;
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
  onHeaderClick?: (column: DataTableColumn<T>) => void;
  onHeaderContextMenu?: (event: MouseEvent<HTMLElement>, column: DataTableColumn<T>) => void;
  onCellClick?: (row: T, column: DataTableColumn<T>, rowIndex: number) => void;
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
  selectedColumnKey?: string | null;
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
    colNumeric: delpiUiClass(`${table}__col--numeric`, `${ui}__col--numeric`),
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
): string {
  if (clickable && classNames.tableClickable) {
    return classNames.tableClickable;
  }

  // classNames.table já traz prefix + delpi-ui-table; modificadores espelham os dois.
  const tableTokens = classNames.table.split(/\s+/).filter(Boolean);
  return [
    classNames.table,
    ...tableTokens.flatMap((token) => {
      const modifiers: string[] = [];
      if (layout === "section") modifiers.push(`${token}--section`);
      if (isSortable) modifiers.push(`${token}--sortable`);
      if (clickable) modifiers.push(`${token}--clickable`);
      if (mode === "grid-preview") modifiers.push(`${token}--grid-preview`);
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
  indexColumn,
  classNames,
  labels,
}: DataTableProps<T>) {
  const isSortable = Boolean(onSortChange && columns.some((column) => column.sortable));
  const resolvedEmptyMessage = emptyMessage ?? labels.emptyMessage;
  const tableClassName = buildTableClassName(
    classNames,
    layout,
    isSortable,
    Boolean(onRowClick),
    mode,
  );

  if (loading) {
    return wrapTableMarkup(
      classNames,
      layout,
      <table className={tableClassName}>
        <tbody>{renderEmptyCell(labels.loadingMessage, columns.length + (indexColumn ? 1 : 0), classNames)}</tbody>
      </table>,
    );
  }

  if (rows.length === 0) {
    return wrapTableMarkup(
      classNames,
      layout,
      <table className={tableClassName}>
        <tbody>{renderEmptyCell(resolvedEmptyMessage, columns.length + (indexColumn ? 1 : 0), classNames)}</tbody>
      </table>,
    );
  }

  return wrapTableMarkup(
    classNames,
    layout,
    <table className={tableClassName}>
      <thead>
        <tr>
          {indexColumn ? (
            <th scope="col" aria-label={indexColumn.ariaLabel ?? "Índice"}>
              {indexColumn.header ?? "#"}
            </th>
          ) : null}
          {columns.map((column) => {
            const isSorted = sortKey === column.key;
            const columnClass = resolveDataTableColumnClassName(column.className);
            const headerClass = [
              columnClass,
              getHeaderClassName?.(column),
              column.sortable && classNames.sortableColumn ? classNames.sortableColumn : "",
            ]
              .filter(Boolean)
              .join(" ");

            return (
              <th
                key={column.key}
                scope="col"
                className={headerClass || undefined}
                data-align={column.align}
                aria-selected={selectedColumnKey === column.key || undefined}
                tabIndex={onHeaderClick ? 0 : undefined}
                onClick={onHeaderClick ? () => onHeaderClick(column) : undefined}
                onContextMenu={
                  onHeaderContextMenu
                    ? (event) => onHeaderContextMenu(event, column)
                    : undefined
                }
                onKeyDown={
                  onHeaderClick
                    ? (event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          onHeaderClick(column);
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
              >
                {column.sortable && onSortChange ? (
                  <button
                    type="button"
                    className={isSorted ? classNames.sortButtonActive : classNames.sortButton}
                    onClick={() => onSortChange(column.key)}
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
              </th>
            );
          })}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, index) => {
          const rowClass = [getRowClassName?.(row), onRowClick ? classNames.rowClickable : ""]
            .filter(Boolean)
            .join(" ");

          return (
            <tr
              key={rowKey(row, index)}
              className={rowClass || undefined}
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
                <td data-label={indexColumn.ariaLabel ?? "Índice"}>
                  {(indexColumn.startAt ?? 1) + index}
                </td>
              ) : null}
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={[
                    resolveDataTableColumnClassName(column.className),
                    getCellClassName?.(row, column, index),
                  ]
                    .filter(Boolean)
                    .join(" ") || undefined}
                  data-label={column.mobileLabel ?? column.header}
                  data-align={column.align}
                  data-interactive={column.interactive ? "true" : undefined}
                  aria-selected={selectedColumnKey === column.key || undefined}
                  tabIndex={onCellClick ? 0 : undefined}
                  onClick={(column.interactive || onCellClick)
                    ? (event) => {
                        if (column.interactive) event.stopPropagation();
                        onCellClick?.(row, column, index);
                      }
                    : undefined}
                  onContextMenu={
                    onCellContextMenu
                      ? (event) => onCellContextMenu(event, row, column, index)
                      : undefined
                  }
                  onKeyDown={
                    onCellClick
                      ? (event) => {
                          if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            onCellClick(row, column, index);
                          }
                        }
                      : undefined
                  }
                >
                  {column.render(row)}
                </td>
              ))}
            </tr>
          );
        })}
      </tbody>
    </table>,
  );
}

export type DashboardDataTableProps<T> = Omit<DataTableProps<T>, "classNames" | "labels">;

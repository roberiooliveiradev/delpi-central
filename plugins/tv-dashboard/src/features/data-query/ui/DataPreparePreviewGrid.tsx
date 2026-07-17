import {
  DataCellValue,
  DataTable,
  dataTableBemClasses,
  primaryColumnKey,
  type DataTableColumn,
  type DataTableSelection,
} from "@delpi/plugin-ui/index";
import { useMemo, useState, type MouseEvent } from "react";

import type { DataQueryCompiledStep, DataQueryPreview } from "../domain/dataQueryTypes";
import { nextSortDirection, resolvePreviewSort } from "./resolvePreviewSort";

export function DataPreparePreviewGrid({
  preview,
  loading,
  compiledSteps,
  selectedStepName,
  selectedColumnKey,
  selection,
  onSelectionChange,
  onSelectColumn,
  onColumnContextMenu,
  onSortColumn,
  onReorderColumns,
}: {
  preview: DataQueryPreview | null;
  loading: boolean;
  compiledSteps?: DataQueryCompiledStep[] | null;
  selectedStepName?: string | null;
  selectedColumnKey: string | null;
  selection?: DataTableSelection | null;
  onSelectionChange?: (selection: DataTableSelection | null) => void;
  onSelectColumn: (key: string) => void;
  onColumnContextMenu: (
    event: MouseEvent<HTMLElement>,
    key: string,
    cellValue?: unknown,
  ) => void;
  onSortColumn?: (columnKey: string, direction: "asc" | "desc") => void;
  onReorderColumns?: (columnKeys: string[]) => void;
}) {
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({});
  const activeSort = useMemo(
    () => resolvePreviewSort(compiledSteps, selectedStepName),
    [compiledSteps, selectedStepName],
  );

  const columns: Array<DataTableColumn<Record<string, unknown>>> = (preview?.columns ?? []).map(
    (column) => ({
      key: column.key,
      header: column.label,
      sortable: Boolean(onSortColumn),
      headerPrefix: (
        <span
          className="td-data-pq__col-type"
          title={`${column.type}${column.nullable ? " · anulável" : ""} · ${column.typeSource}`}
          aria-label={`Tipo ${column.type}${column.nullable ? ", anulável" : ""}`}
        >
          {typeGlyph(column.type)}
        </span>
      ),
      render: (row) => (
        <DataCellValue
          value={row[column.key]}
          present={Object.prototype.hasOwnProperty.call(row, column.key)}
        />
      ),
    }),
  );

  const resolvedSelection =
    selection ?? (selectedColumnKey ? { kind: "column" as const, keys: [selectedColumnKey] } : null);

  return (
    <div className="td-data-pq__grid-wrap">
      <DataTable
        columns={columns}
        rows={preview?.rows ?? []}
        rowKey={(_, index) => String(index)}
        classNames={dataTableBemClasses("td-m-preview")}
        labels={{
          emptyMessage: "Sem linhas para a etapa selecionada.",
          loadingMessage: "Atualizando prévia…",
          sortByAriaLabel: (header) => `Ordenar por ${header}`,
          headerHelpAriaLabel: (header) => `Ajuda: ${header}`,
        }}
        mode="grid-preview"
        layout="embedded"
        loading={loading}
        wrapText
        resizableColumns
        enableColumnReorder={Boolean(onReorderColumns)}
        enableCopySelection
        columnWidths={columnWidths}
        onColumnWidthsChange={setColumnWidths}
        indexColumn={{ ariaLabel: "Número da linha" }}
        selection={resolvedSelection}
        onSelectionChange={(next) => {
          if (onSelectionChange) {
            onSelectionChange(next);
            return;
          }
          onSelectColumn(primaryColumnKey(next) ?? "");
        }}
        sortKey={activeSort?.key ?? null}
        sortDirection={activeSort?.direction ?? "asc"}
        onSortChange={
          onSortColumn
            ? (columnKey) => {
                onSortColumn(columnKey, nextSortDirection(activeSort, columnKey));
              }
            : undefined
        }
        onColumnOrderChange={onReorderColumns}
        onHeaderClick={
          onSelectionChange ? undefined : (column) => onSelectColumn(column.key)
        }
        onHeaderContextMenu={(event, column) => onColumnContextMenu(event, column.key)}
        onCellClick={
          onSelectionChange ? undefined : (_, column) => onSelectColumn(column.key)
        }
        onCellContextMenu={(event, row, column) =>
          onColumnContextMenu(event, column.key, row[column.key])
        }
      />
      {preview?.isSample ? (
        <p className="td-deck-inspector__meta" role="status">
          Amostra: {preview.returnedRows} de {preview.availableRows} linhas
          {preview.truncated ? " (limitada)" : ""}.
        </p>
      ) : null}
    </div>
  );
}

function typeGlyph(type: string): string {
  if (type === "number") return "123";
  if (type === "date" || type === "datetime") return "▣";
  if (type === "logical") return "◉";
  return "ABC";
}

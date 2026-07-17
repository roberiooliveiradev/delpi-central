import {
  DataTable,
  dataTableBemClasses,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";
import type { MouseEvent } from "react";

import type { DataQueryPreview } from "../domain/dataQueryTypes";

function typeGlyph(type: string): string {
  if (type === "number") return "123";
  if (type === "date" || type === "datetime") return "▣";
  if (type === "logical") return "◉";
  return "ABC";
}

export function DataPreparePreviewGrid({
  preview,
  loading,
  selectedColumnKey,
  onSelectColumn,
  onColumnContextMenu,
}: {
  preview: DataQueryPreview | null;
  loading: boolean;
  selectedColumnKey: string | null;
  onSelectColumn: (key: string) => void;
  onColumnContextMenu: (event: MouseEvent<HTMLElement>, key: string) => void;
}) {
  const columns: Array<DataTableColumn<Record<string, unknown>>> = (preview?.columns ?? []).map(
    (column) => ({
      key: column.key,
      header: column.label,
      headerPrefix: (
        <span
          className="td-data-pq__col-type"
          title={`${column.type}${column.nullable ? " · anulável" : ""} · ${column.typeSource}`}
          aria-label={`Tipo ${column.type}${column.nullable ? ", anulável" : ""}`}
        >
          {typeGlyph(column.type)}
        </span>
      ),
      render: (row) => (row[column.key] == null ? "" : String(row[column.key])),
    }),
  );
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
        indexColumn={{ ariaLabel: "Número da linha" }}
        selectedColumnKey={selectedColumnKey}
        onHeaderClick={(column) => onSelectColumn(column.key)}
        onHeaderContextMenu={(event, column) => onColumnContextMenu(event, column.key)}
        onCellClick={(_, column) => onSelectColumn(column.key)}
        onCellContextMenu={(event, _, column) => onColumnContextMenu(event, column.key)}
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

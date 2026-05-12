import { Download, Search } from "lucide-react";
import { useMemo, useState } from "react";

import "./DataTable.css";

export type DataTableColumn = {
  key: string;
  label: string;
};

type DataTableProps = {
  title?: string;
  columns: DataTableColumn[];
  rows: Record<string, unknown>[];
};

function normalize(value: unknown): string {
  if (value === null || value === undefined) {
    return "";
  }

  if (typeof value === "boolean") {
    return value ? "Sim" : "Não";
  }

  return String(value);
}

function toCsv(columns: DataTableColumn[], rows: Record<string, unknown>[]): string {
  const escape = (value: string) => `"${value.replaceAll('"', '""')}"`;

  const header = columns.map((column) => escape(column.label)).join(",");

  const body = rows
    .map((row) =>
      columns.map((column) => escape(normalize(row[column.key]))).join(","),
    )
    .join("\n");

  return [header, body].filter(Boolean).join("\n");
}

export function DataTable({ title, columns, rows }: DataTableProps) {
  const [filter, setFilter] = useState("");

  const filteredRows = useMemo(() => {
    const normalizedFilter = filter.trim().toLowerCase();

    if (!normalizedFilter) {
      return rows;
    }

    return rows.filter((row) =>
      columns.some((column) =>
        normalize(row[column.key]).toLowerCase().includes(normalizedFilter),
      ),
    );
  }, [columns, filter, rows]);

  function exportCsv() {
    const csv = toCsv(columns, filteredRows);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");

    anchor.href = url;
    anchor.download = `${title || "dados"}.csv`;
    anchor.click();

    URL.revokeObjectURL(url);
  }

  return (
    <section className="mdc-data-table">
      <header className="mdc-data-table__header">
        <div>
          {title ? <h3>{title}</h3> : null}
          <small>{filteredRows.length} registro(s)</small>
        </div>

        <div className="mdc-data-table__actions">
          <label>
            <Search size={15} aria-hidden="true" />
            <input
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
              placeholder="Filtrar..."
            />
          </label>

          <button type="button" onClick={exportCsv}>
            <Download size={15} aria-hidden="true" />
            CSV
          </button>
        </div>
      </header>

      <div className="mdc-data-table__scroll">
        <table>
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column.key}>{column.label}</th>
              ))}
            </tr>
          </thead>

          <tbody>
            {filteredRows.map((row, index) => (
              <tr key={index}>
                {columns.map((column) => (
                  <td key={column.key}>{normalize(row[column.key]) || "—"}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

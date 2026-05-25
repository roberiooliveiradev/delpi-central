import { useState, useCallback } from "react";
import type { ChatPresentation } from "../../data/api/chatTypes";

type TablePresentation = Extract<ChatPresentation, { type: "table" }>;

type SortConfig = {
  key: string;
  direction: "asc" | "desc";
} | null;

export function ChatRichTable({
  presentation,
}: {
  presentation: TablePresentation;
}) {
  const { title, columns, rows } = presentation;
  const [sortConfig, setSortConfig] = useState<SortConfig>(null);
  const [copied, setCopied] = useState(false);

  const sortedRows = useCallback(() => {
    if (!sortConfig) return rows;

    return [...rows].sort((a, b) => {
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
  }, [rows, sortConfig]);

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

  function exportCsv() {
    const BOM = "\uFEFF";
    const header = columns.map((c) => c.label).join(";");
    const body = rows
      .map((row) =>
        columns
          .map((col) => {
            const val = row[col.key];
            if (val == null) return "";
            const str = String(val);
            return str.includes(";") || str.includes('"')
              ? `"${str.replace(/"/g, '""')}"`
              : str;
          })
          .join(";"),
      )
      .join("\n");

    const csv = BOM + header + "\n" + body;
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${title || "dados"}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function copyToClipboard() {
    const header = columns.map((c) => c.label).join("\t");
    const body = rows
      .map((row) =>
        columns.map((col) => String(row[col.key] ?? "")).join("\t"),
      )
      .join("\n");

    navigator.clipboard.writeText(header + "\n" + body).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  const sorted = sortedRows();

  return (
    <div className="mdc-rich-table">
      <div className="mdc-rich-table__header">
        <span className="mdc-rich-table__title">{title}</span>
        <div className="mdc-rich-table__actions">
          <button
            className="mdc-rich-table__btn"
            onClick={copyToClipboard}
            title="Copiar tabela"
          >
            {copied ? "✓ Copiado" : "Copiar"}
          </button>
          <button
            className="mdc-rich-table__btn"
            onClick={exportCsv}
            title="Baixar CSV"
          >
            ↓ CSV
          </button>
        </div>
      </div>

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
              <tr key={idx}>
                {columns.map((col) => (
                  <td key={col.key}>{formatCellValue(row[col.key])}</td>
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
    </div>
  );
}

function formatCellValue(value: unknown): string {
  if (value == null) return "—";
  if (typeof value === "boolean") return value ? "Sim" : "Não";
  if (typeof value === "number") {
    if (Number.isInteger(value)) return value.toLocaleString("pt-BR");
    return value.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 4 });
  }
  return String(value);
}
